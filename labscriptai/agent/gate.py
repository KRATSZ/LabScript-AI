"""Three-state tool gate for the lean agent.

Statuses: allow | ask | suspend.
Context author|run is system-inferred and never sent to the model.
Run context requires a reachable robot; an active run id is optional.
Daemon (interactive=False) upgrades every ask → suspend.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

# Agent-facing labels → MCP tool names (keep aligned with tools._ACT_ALIASES).
ROBOT_ACT_ALIASES: dict[str, str] = {
    "execute_recovery_branch": "execute_protocol_recovery",
    "execute_protocol_recovery": "execute_protocol_recovery",
    "pause_run": "control_run",
    "resume_run": "control_run",
    "abort_run": "control_run",
    "play_run": "control_run",
    "stop_run": "control_run",
    "inspect_robot_state": "robot_status",
    "capture_deck_image": "capture_preview_image",
    "recover_liquid_source_substitution": "recover_liquid_source_substitution",
    "drop_tip": "drop_attached_tip",
}

RESUME_BLOCKED_RUN_STATUSES: frozenset[str] = frozenset({"awaiting-recovery", "failed"})

# robot(op=act) labels that aspirate from / probe a well (contamination gate).
ASPIRATE_OR_PROBE_ACTIONS: frozenset[str] = frozenset(
    {
        "probe_wells",
        "aspirate",
        "aspirateInPlace",
        "aspirate_in_place",
        "require_liquid_presence",
        "liquidProbe",
        "liquid_probe",
        "measure_liquid_height",
    }
)

# Pollution / tip-policy roles (not liquid_tracking filter role "source").
POLLUTION_WELL_ROLES: frozenset[str] = frozenset(
    {"sample", "common_stock", "waste", "unknown"}
)

_TIP_RECOVERY_BRANCH_MARKERS: tuple[str, ...] = (
    "tip",
    "pick_up_tip",
    "pickup_tip",
    "pickuptip",
    "retry_pick_up",
    "retry_pickup",
)

# Run-context robot(op=act) whitelist: aliases above plus direct MCP tool names.
SAFE_ACTION_TYPES: frozenset[str] = frozenset(
    {
        *ROBOT_ACT_ALIASES.keys(),
        *ROBOT_ACT_ALIASES.values(),
        "simulate_protocol",
        "mark_resource_unavailable",
        "choose_alternative_source",
        "request_human_confirmation",
        "propose_continuation_patch",
        "validate_continuation_patch",
        "record_liquid_source_map",
        "run_protocol",
        "upload_protocol",
        "create_run",
        "get_protocols",
        "get_runs",
        "run_history",
        "parse_error",
        "suggest_recovery_action",
        "runtime_watch_poll",
        "health_check",
        "doctor_local_runtime",
        "recover_tip_pickup",
        "recover_liquid_source_substitution",
        "drop_attached_tip",
        "probe_wells",
        "apply_liquid_probe_results",
        "control_run",
        "robot_status",
        "capture_preview_image",
    }
)

# Optional extras for `labscriptai chat --robot` / recover drivers (SAFE already covers recovery).
DEFAULT_RECOVERY_PREAUTHORIZED: frozenset[str] = frozenset()

ContextName = Literal["author", "run"]
GateStatus = Literal["allow", "ask", "suspend"]

_DESTRUCTIVE_CMDS = frozenset(
    {
        "rm",
        "rmdir",
        "mv",
        "chmod",
        "chown",
        "dd",
        "mkfs",
        "shutdown",
        "reboot",
        "kill",
        "killall",
        "unlink",
        "shred",
    }
)
_NETWORK_CMDS = frozenset(
    {
        "curl",
        "wget",
        "nc",
        "ncat",
        "ssh",
        "scp",
        "sftp",
        "ftp",
        "telnet",
    }
)
_ROBOT_PORT_MARKERS = (":31950", "31950")


@dataclass
class GateDecision:
    status: GateStatus
    reasons: list[str] = field(default_factory=list)
    context: ContextName = "author"


def infer_context(*, robot_connected: bool, active_run: bool = False) -> ContextName:
    """System-only context bit: robot reachable → run; otherwise author.

    ``active_run`` is retained for call-site compatibility / session tracking but
    no longer required to enter run context. Requiring an existing run made
    protocol start impossible from chat (robot act needs run context; run
    context needed an already-started run).
    """
    del active_run  # kept in signature for callers; not used for inference
    if robot_connected:
        return "run"
    return "author"


def resolve_robot_act_label(args: dict[str, Any]) -> str:
    """Normalize robot(op=act) action label from action fields or recovery_branch."""
    action = str(
        args.get("action_type") or args.get("action") or args.get("type") or ""
    ).strip()
    nested = args.get("args")
    branch = args.get("recovery_branch")
    if isinstance(nested, dict):
        branch = branch or nested.get("recovery_branch") or nested.get("branch")
    branch = str(branch or "").strip()
    if branch and not action:
        return "execute_protocol_recovery"
    if branch and action in {"execute_recovery_branch", "execute_protocol_recovery"}:
        return action
    return action


def is_resume_play_request(args: dict[str, Any]) -> bool:
    """True when robot(op=act) would resume/play an existing run."""
    action_label = resolve_robot_act_label(args)
    if action_label in {"resume_run", "play_run", "play"}:
        return True
    nested = args.get("args") if isinstance(args.get("args"), dict) else {}
    if action_label == "control_run":
        play_action = str(
            nested.get("action")
            or nested.get("actionType")
            or args.get("action_type")
            or ""
        ).strip().lower()
        return play_action == "play"
    injected = ROBOT_ACT_ALIASES.get(action_label)
    if injected == "control_run":
        play_action = str(args.get("action") or args.get("action_type") or "").strip().lower()
        return play_action == "play"
    return False


def is_time_window_expired(time_window: Mapping[str, Any] | None) -> bool:
    """True only when MCP reports an explicitly expired declared window.

    Missing / null / non-mapping payloads must not change gate behavior.
    """
    if not isinstance(time_window, Mapping):
        return False
    return time_window.get("expired") is True


def _nested_act_args(args: dict[str, Any]) -> dict[str, Any]:
    nested = args.get("args")
    return nested if isinstance(nested, dict) else {}


def is_aspirate_or_probe_request(args: dict[str, Any]) -> bool:
    """True when robot(op=act) would aspirate from or probe a well."""
    action_label = resolve_robot_act_label(args)
    if action_label in ASPIRATE_OR_PROBE_ACTIONS:
        return True
    nested = _nested_act_args(args)
    nested_action = str(
        nested.get("action")
        or nested.get("action_type")
        or nested.get("command_type")
        or nested.get("commandType")
        or ""
    ).strip()
    if nested_action in ASPIRATE_OR_PROBE_ACTIONS:
        return True
    # recover_liquid_source_substitution aspirates from a declared substitute well
    if action_label in {
        "recover_liquid_source_substitution",
        "choose_alternative_source",
    }:
        return True
    return False


def _normalize_well_key(value: Any) -> str | None:
    """Canonical well key as ``SLOT.WELL`` (MCP live-state form).

    Accepts ``C2.A1``, ``C2:A1``, ``C2/A1``, and slot wildcards ``C2.*``.
    """
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("/", ".").replace(":", ".")
    parts = [p for p in text.split(".") if p]
    if len(parts) >= 2:
        slot, well = parts[0].strip().upper(), parts[1].strip().upper()
        if slot and well:
            return f"{slot}.{well}"
    return text.upper()


normalize_well_key = _normalize_well_key


def _iter_target_well_keys(args: dict[str, Any]) -> list[str]:
    """Best-effort well keys from act args (missing → empty → no contamination block)."""
    nested = _nested_act_args(args)
    candidates: list[Any] = []
    for blob in (args, nested):
        for key in (
            "well",
            "well_name",
            "wellName",
            "well_key",
            "wellKey",
            "key",
            "source",
            "source_well",
            "sourceWell",
            "labware_well",
            "target_well",
            "candidate_key",
        ):
            if key in blob:
                candidates.append(blob.get(key))
        for key in ("wells", "targets", "probe_wells", "probeWells"):
            value = blob.get(key)
            if isinstance(value, (list, tuple)):
                candidates.extend(value)
            elif value is not None:
                candidates.append(value)
        slot = (
            blob.get("slot")
            or blob.get("slot_name")
            or blob.get("labware_slot")
            or blob.get("labwareSlot")
        )
        well = blob.get("well_name") or blob.get("wellName") or blob.get("well")
        if slot and well:
            candidates.append(f"{slot}.{well}")

    keys: list[str] = []
    for item in candidates:
        if isinstance(item, Mapping):
            slot = (
                item.get("slot")
                or item.get("slot_name")
                or item.get("labware_slot")
                or item.get("labwareSlot")
            )
            well = item.get("well") or item.get("well_name") or item.get("wellName")
            if slot and well:
                normalized = _normalize_well_key(f"{slot}.{well}")
            else:
                normalized = _normalize_well_key(
                    item.get("well_key") or item.get("key") or item.get("id")
                )
        else:
            normalized = _normalize_well_key(item)
        if normalized and normalized not in keys:
            keys.append(normalized)
    return keys


def _instrument_has_tip(item: Mapping[str, Any]) -> bool | None:
    """True/False when tip presence is explicit; None when unknown."""
    if "has_tip" in item:
        value = item.get("has_tip")
        if isinstance(value, bool):
            return value
    if "tip_detected" in item:
        value = item.get("tip_detected")
        if isinstance(value, bool):
            return value
    return None


def _attached_tip_contact_classes(
    instruments_summary: Sequence[Any] | None,
) -> list[str]:
    """Return contact_class values for instruments that currently hold a tip."""
    if not isinstance(instruments_summary, Sequence) or isinstance(
        instruments_summary, (str, bytes)
    ):
        return []
    classes: list[str] = []
    for item in instruments_summary:
        if not isinstance(item, Mapping):
            continue
        contact = item.get("contact_class")
        if not isinstance(contact, str) or not contact.strip():
            continue
        has_tip = _instrument_has_tip(item)
        if has_tip is False:
            continue
        classes.append(contact.strip().lower())
    return classes


def normalize_pollution_well_role(value: Any) -> str | None:
    """Return sample/common_stock/waste/unknown; ignore liquid_tracking ``source``."""
    if isinstance(value, Mapping):
        for key in ("well_role", "pollution_role", "tip_policy_role"):
            role = normalize_pollution_well_role(value.get(key))
            if role:
                return role
        role = value.get("role")
        if isinstance(role, str) and role.strip().lower() in POLLUTION_WELL_ROLES:
            return role.strip().lower()
        return None
    if not isinstance(value, str):
        return None
    role = value.strip().lower()
    if role in POLLUTION_WELL_ROLES:
        return role
    return None


def _well_roles_lookup(well_roles: Mapping[str, Any]) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    for key, value in well_roles.items():
        normalized = _normalize_well_key(key)
        if normalized:
            lookup[normalized] = value
    return lookup


def _well_role_for_key(
    well_key: str,
    well_roles: Mapping[str, Any] | None,
) -> str | None:
    if not isinstance(well_roles, Mapping) or not well_key:
        return None
    lookup = _well_roles_lookup(well_roles)
    normalized = _normalize_well_key(well_key)
    if not normalized:
        return None
    role = normalize_pollution_well_role(lookup.get(normalized))
    if role:
        return role
    # Slot wildcard used by MCP well role maps (e.g. ``C2.*``).
    if "." in normalized:
        slot = normalized.split(".", 1)[0]
        role = normalize_pollution_well_role(lookup.get(f"{slot}.*"))
        if role:
            return role
    return None


def is_sample_tip_common_stock_request(
    args: dict[str, Any],
    *,
    instruments_summary: Sequence[Any] | None = None,
    well_roles: Mapping[str, Any] | None = None,
) -> bool:
    """True when a sample-contact tip would aspirate/probe a common_stock well.

    Any missing field → False (preserve prior allow/ask behavior).
    """
    if not is_aspirate_or_probe_request(args):
        return False
    contacts = _attached_tip_contact_classes(instruments_summary)
    if "sample" not in contacts:
        return False
    if not isinstance(well_roles, Mapping) or not well_roles:
        return False
    targets = _iter_target_well_keys(args)
    if not targets:
        return False
    for key in targets:
        if _well_role_for_key(key, well_roles) == "common_stock":
            return True
    return False


def _recovery_branch_text(args: dict[str, Any]) -> str:
    nested = _nested_act_args(args)
    branch = (
        args.get("recovery_branch")
        or args.get("branch")
        or nested.get("recovery_branch")
        or nested.get("branch")
        or ""
    )
    return str(branch).strip().lower()


def is_tip_recovery_request(args: dict[str, Any]) -> bool:
    """True for recover_tip_pickup or tip-retry execute_protocol_recovery branches."""
    action_label = resolve_robot_act_label(args)
    if action_label == "recover_tip_pickup":
        return True
    if action_label in {"execute_protocol_recovery", "execute_recovery_branch"}:
        branch = _recovery_branch_text(args)
        if not branch:
            return False
        compact = branch.replace("-", "_").replace(" ", "_")
        return any(marker in compact for marker in _TIP_RECOVERY_BRANCH_MARKERS)
    return False


def is_liquid_substitution_request(args: dict[str, Any]) -> bool:
    return resolve_robot_act_label(args) == "recover_liquid_source_substitution"


def is_tip_budget_insufficient(tip_budget: Mapping[str, Any] | None) -> bool:
    """Hard-block only when tip_budget is explicitly enforced and insufficient.

    ``basis == "none"`` (or missing enforced) must not change gate behavior.
    """
    if not isinstance(tip_budget, Mapping):
        return False
    if tip_budget.get("enforced") is not True:
        return False
    return tip_budget.get("sufficient") is False


def is_substitute_volume_insufficient(
    volume_check: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None = None,
) -> bool:
    """Hard-block substitute recovery on known short declared/estimated volume.

    ``basis == "insufficient_data"`` with sufficient=False is NOT a hard stop.
    Runtime LPD failures / approximate height shortfalls are hard stops.
    """
    reason = str(blocked_reason or "").strip()
    if reason in {
        "substitute_volume_insufficient",
        "substitute_reserve_lpd_failed",
        "substitute_reserve_volume_insufficient",
    }:
        return True
    if not isinstance(volume_check, Mapping):
        return False
    basis = str(volume_check.get("basis") or "").strip()
    if basis == "insufficient_data":
        return False
    if basis == "declared_source_map" and volume_check.get("sufficient") is False:
        return True
    if basis == "approximate_lpd_height" and volume_check.get("sufficient") is False:
        return True
    return False


def robot_act_allow_candidates(action_label: str) -> tuple[str, ...]:
    """Return action labels that satisfy SAFE/preauthorized (alias + canonical)."""
    if not action_label:
        return ()
    canonical = ROBOT_ACT_ALIASES.get(action_label)
    if canonical and canonical != action_label:
        return (action_label, canonical)
    return (action_label,)


def evaluate(
    tool_name: str,
    args: dict[str, Any],
    *,
    context: ContextName,
    interactive: bool,
    preauthorized: set[str] | None = None,
    active_run_status: str | None = None,
    time_window: Mapping[str, Any] | None = None,
    instruments_summary: Sequence[Any] | None = None,
    well_roles: Mapping[str, Any] | None = None,
    tip_budget: Mapping[str, Any] | None = None,
    volume_check: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
) -> GateDecision:
    """Evaluate one tool call. ``interactive=False`` upgrades ask → suspend."""
    preauthorized = set(preauthorized or ())
    name = (tool_name or "").strip().lower()
    args = dict(args or {})

    if name == "skill":
        decision = GateDecision(status="allow", reasons=["skill is always allowed"], context=context)
    elif name == "memory":
        decision = _eval_memory(args, context=context)
    elif name == "edit":
        decision = _eval_edit(args, context=context)
    elif name == "bash":
        decision = _eval_bash(args, context=context)
    elif name == "robot":
        decision = _eval_robot(
            args,
            context=context,
            preauthorized=preauthorized,
            active_run_status=active_run_status,
            time_window=time_window,
            instruments_summary=instruments_summary,
            well_roles=well_roles,
            tip_budget=tip_budget,
            volume_check=volume_check,
            blocked_reason=blocked_reason,
        )
    else:
        decision = GateDecision(
            status="ask",
            reasons=[f"unknown tool: {tool_name}"],
            context=context,
        )

    # Daemon: every ask upgrades to suspend
    if not interactive and decision.status == "ask":
        return GateDecision(
            status="suspend",
            reasons=[*decision.reasons, "daemon: ask upgraded to suspend"],
            context=decision.context,
        )
    return decision


def _eval_memory(args: dict[str, Any], *, context: ContextName) -> GateDecision:
    op = str(args.get("op") or args.get("action") or "read").strip().lower()
    if op in {"write", "append", "set", "put"}:
        return GateDecision(
            status="allow",
            reasons=["memory write allowed (trajectory)"],
            context=context,
        )
    return GateDecision(status="allow", reasons=["memory read allowed"], context=context)


def _workspace_root() -> Path:
    raw = os.environ.get("LABSCRIPTAI_WORKSPACE") or os.getcwd()
    return Path(raw).expanduser().resolve()


def coerce_path_into_workspace(path: str, workspace: Path | None = None) -> str:
    """Rewrite mistaken ``../local/...`` paths into workspace-relative paths.

    Models often prepend ``../`` when cwd is ``labscriptai/`` even though chat
    ``--workspace`` is already the repo root. If stripping leading ``..``
    segments lands on an existing path inside the workspace, use that; otherwise
    return the original string unchanged.
    """
    raw = str(path or "").strip()
    if not raw:
        return raw
    root = (workspace or _workspace_root()).expanduser().resolve()

    def _inside(rel_or_abs: str, *, require_existing: bool) -> Path | None:
        candidate = Path(rel_or_abs).expanduser()
        try:
            resolved = (
                candidate.resolve()
                if candidate.is_absolute()
                else (root / candidate).resolve()
            )
            resolved.relative_to(root)
        except (OSError, ValueError):
            return None
        if require_existing and not resolved.exists():
            return None
        return resolved

    hit = _inside(raw, require_existing=False)
    if hit is not None:
        try:
            return str(hit.relative_to(root)).replace("\\", "/")
        except ValueError:
            return raw.replace("\\", "/")

    # Strip leading ../ or ..\ segments (and lone "..").
    parts = list(Path(raw.replace("\\", "/")).parts)
    while parts and parts[0] == "..":
        parts = parts[1:]
        if not parts:
            break
        candidate = "/".join(parts)
        hit = _inside(candidate, require_existing=True)
        if hit is not None:
            return str(hit.relative_to(root)).replace("\\", "/")

    return raw


def _path_in_workspace(path: str) -> bool:
    if not path or not str(path).strip():
        return False
    workspace = _workspace_root()
    coerced = coerce_path_into_workspace(path, workspace)
    candidate = Path(str(coerced)).expanduser()
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()
        resolved.relative_to(workspace)
    except (OSError, ValueError):
        return False
    return True


def _eval_edit(args: dict[str, Any], *, context: ContextName) -> GateDecision:
    path = str(args.get("path") or args.get("file") or "")
    if not path.strip():
        return GateDecision(status="ask", reasons=["edit requires path"], context=context)
    # Mutate args so execute sees the coerced path (avoids re-escape at tool layer).
    coerced = coerce_path_into_workspace(path)
    if coerced != path:
        if "path" in args or "file" not in args:
            args["path"] = coerced
        if "file" in args:
            args["file"] = coerced
        path = coerced
    if _path_in_workspace(path):
        return GateDecision(
            status="allow",
            reasons=["edit path is inside workspace"],
            context=context,
        )
    return GateDecision(
        status="ask",
        reasons=[f"edit path outside workspace: {path}"],
        context=context,
    )


def _known_robot_ips() -> set[str]:
    ips: set[str] = set()
    for key in (
        "OPENTRONS_ROBOT_IP",
        "ROBOT_IP",
        "OT_ROBOT_IP",
        "LABSCRIPTAI_ROBOT_IP",
    ):
        value = (os.environ.get(key) or "").strip()
        if value:
            ips.add(value)
    return ips


def _command_text_and_tokens(args: dict[str, Any]) -> tuple[str, list[str]]:
    command = args.get("command", args.get("cmd", args.get("argv")))
    if isinstance(command, list):
        tokens = [str(item) for item in command]
        text = " ".join(tokens)
        return text, tokens
    text = str(command or "")
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    return text, tokens


def _executable_basename(token: str) -> str:
    return Path(token).name.lower()


def _eval_bash(args: dict[str, Any], *, context: ContextName) -> GateDecision:
    text, tokens = _command_text_and_tokens(args)
    if not text.strip():
        return GateDecision(status="ask", reasons=["bash requires command"], context=context)

    # Hard ban: robot HTTP via shell — must use robot tool
    robot_ips = _known_robot_ips()
    hits_port = any(marker in text for marker in _ROBOT_PORT_MARKERS)
    hits_ip = any(ip and ip in text for ip in robot_ips)
    if hits_port or hits_ip:
        return GateDecision(
            status="suspend",
            reasons=[
                "bash must not call the robot HTTP API directly "
                f"(found {':31950' if hits_port else 'robot_ip'}); use the robot tool",
            ],
            context=context,
        )

    basenames = {_executable_basename(tok) for tok in tokens if tok}
    # Also scan bare words in the string for piped/subshell forms
    word_hits = set(re.findall(r"[A-Za-z0-9_./+-]+", text))
    basenames |= {_executable_basename(w) for w in word_hits}

    destructive = sorted(basenames & _DESTRUCTIVE_CMDS)
    network = sorted(basenames & _NETWORK_CMDS)
    if destructive or network:
        kinds: list[str] = []
        if destructive:
            kinds.append(f"destructive:{','.join(destructive)}")
        if network:
            kinds.append(f"network:{','.join(network)}")
        return GateDecision(
            status="ask",
            reasons=[f"bash needs approval ({'; '.join(kinds)})"],
            context=context,
        )

    return GateDecision(status="allow", reasons=["bash command allowed"], context=context)


def _eval_robot(
    args: dict[str, Any],
    *,
    context: ContextName,
    preauthorized: set[str],
    active_run_status: str | None = None,
    time_window: Mapping[str, Any] | None = None,
    instruments_summary: Sequence[Any] | None = None,
    well_roles: Mapping[str, Any] | None = None,
    tip_budget: Mapping[str, Any] | None = None,
    volume_check: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
) -> GateDecision:
    op = str(args.get("op") or "").strip().lower()
    if op in {"status", "watch"}:
        return GateDecision(
            status="allow",
            reasons=[f"robot {op} is read-only"],
            context=context,
        )

    if op != "act":
        return GateDecision(
            status="ask",
            reasons=[f"unknown robot op: {op or '(missing)'}"],
            context=context,
        )

    # op=act — author means robot is not connected (see infer_context).
    if context == "author":
        return GateDecision(
            status="suspend",
            reasons=["robot act suspended in author context (robot not connected)"],
            context=context,
        )

    action_label = resolve_robot_act_label(args)
    if not action_label:
        return GateDecision(
            status="ask",
            reasons=["robot act requires action_type, action, or recovery_branch"],
            context=context,
        )

    run_status = str(active_run_status or "").strip().lower()
    if run_status in RESUME_BLOCKED_RUN_STATUSES and is_resume_play_request(args):
        return GateDecision(
            status="suspend",
            reasons=[
                f"resume_run blocked while run status is {run_status}; "
                "use recover_liquid_source_substitution (L0, like recover_tip_pickup) "
                "instead of replaying the failed run",
            ],
            context=context,
        )

    if is_time_window_expired(time_window) and is_resume_play_request(args):
        return GateDecision(
            status="suspend",
            reasons=[
                "play/resume blocked: declared time window has expired; "
                "the only executable exit is abort_run / stop_run",
            ],
            context=context,
        )

    if is_tip_budget_insufficient(tip_budget) and (
        is_tip_recovery_request(args) or is_resume_play_request(args)
    ):
        return GateDecision(
            status="suspend",
            reasons=[
                "tip budget insufficient: remaining tips cannot cover remaining "
                "pickups; continuing would waste leftover tips — refill tips or "
                "escalate (do not recover_tip_pickup, play, or resume)",
            ],
            context=context,
        )

    if is_substitute_volume_insufficient(
        volume_check, blocked_reason=blocked_reason
    ) and is_liquid_substitution_request(args):
        return GateDecision(
            status="suspend",
            reasons=[
                "liquid source substitution blocked: reserve LPD failed or usable "
                "volume is insufficient for the remaining transfer; refill or "
                "escalate — do not substitute",
            ],
            context=context,
        )

    if is_sample_tip_common_stock_request(
        args,
        instruments_summary=instruments_summary,
        well_roles=well_roles,
    ):
        return GateDecision(
            status="suspend",
            reasons=[
                "sample-contact tip blocked from aspirate/probe on common_stock well; "
                "drop tip and pick a fresh tip before re-entering shared stock",
            ],
            context=context,
        )

    allowed = SAFE_ACTION_TYPES | preauthorized
    for candidate in robot_act_allow_candidates(action_label):
        if candidate in allowed:
            return GateDecision(
                status="allow",
                reasons=[f"robot act allowed: {candidate}"],
                context=context,
            )

    return GateDecision(
        status="ask",
        reasons=[
            f"robot act not in SAFE/preauthorized: {action_label}",
        ],
        context=context,
    )


__all__ = (
    "ASPIRATE_OR_PROBE_ACTIONS",
    "DEFAULT_RECOVERY_PREAUTHORIZED",
    "POLLUTION_WELL_ROLES",
    "RESUME_BLOCKED_RUN_STATUSES",
    "ROBOT_ACT_ALIASES",
    "SAFE_ACTION_TYPES",
    "GateDecision",
    "coerce_path_into_workspace",
    "evaluate",
    "infer_context",
    "is_aspirate_or_probe_request",
    "is_liquid_substitution_request",
    "is_resume_play_request",
    "is_sample_tip_common_stock_request",
    "is_substitute_volume_insufficient",
    "is_tip_budget_insufficient",
    "is_tip_recovery_request",
    "is_time_window_expired",
    "normalize_pollution_well_role",
    "normalize_well_key",
    "resolve_robot_act_label",
    "robot_act_allow_candidates",
)
