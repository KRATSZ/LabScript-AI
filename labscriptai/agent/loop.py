"""Single agent turn loop: observe → LLM propose → gate → execute → trail.

Mode never enters the model prompt. The model always sees the fixed 5-tool schema.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

# --- W1 / W2 contracts (defensive) -------------------------------------------

try:
    from labscriptai.agent.gate import GateDecision, evaluate, infer_context
except ImportError:  # pragma: no cover - W1 not ready
    GateDecision = None  # type: ignore[misc, assignment]
    evaluate = None  # type: ignore[assignment]
    infer_context = None  # type: ignore[assignment]

try:
    from labscriptai.agent.tools import TOOLS_SCHEMA, execute
except ImportError:  # pragma: no cover - W2 not ready
    TOOLS_SCHEMA: list[dict[str, Any]] = [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Run a local shell command in the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit",
                "description": "Read/write/str_replace a file under the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "enum": ["read", "write", "str_replace"]},
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "old_str": {"type": "string"},
                        "new_str": {"type": "string"},
                    },
                    "required": ["op", "path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "robot",
                "description": "Robot ops: status/watch (read) or act (gated).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "enum": ["status", "watch", "act"]},
                        "run_id": {"type": "string"},
                        "action_type": {"type": "string"},
                    },
                    "required": ["op"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "memory",
                "description": "Read/write case memory under .labscriptai/memory/.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string"},
                        "name": {"type": "string"},
                        "content": {"type": "string"},
                        "query": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "skill",
                "description": "Load a skill markdown by name (or list skills).",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
            },
        },
    ]

    def execute(  # type: ignore[misc]
        name: str,
        args: dict,
        *,
        workspace: Path,
        robot_ip: str | None,
        session: dict,
    ) -> dict:
        del args, workspace, robot_ip, session
        return {"error": "W2 tools not ready", "tool": name}


# 0 = unlimited tool steps per turn (override via LABSCRIPTAI_MAX_STEPS or session.max_steps).
DEFAULT_MAX_STEPS = 0
OUTBOX_DIRNAME = ".labscriptai/outbox"


def resolve_max_steps(value: int | None = None) -> int:
    """Max tool-call iterations per user turn; 0 means no cap."""
    if value is not None:
        return max(0, int(value))
    raw = os.environ.get("LABSCRIPTAI_MAX_STEPS")
    if raw is None or not str(raw).strip():
        return DEFAULT_MAX_STEPS
    try:
        return max(0, int(str(raw).strip()))
    except ValueError:
        return DEFAULT_MAX_STEPS


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]: ...


@dataclass
class SessionState:
    """Minimal session fields shared by chat / recover / daemon."""

    workspace: Path
    robot_ip: str | None = None
    robot_connected: bool = False
    active_run_id: str | None = None
    active_run_status: str | None = None
    time_window: dict[str, Any] | None = None
    instruments_summary: list[Any] = field(default_factory=list)
    well_roles: dict[str, Any] = field(default_factory=dict)
    tip_budget: dict[str, Any] | None = None
    volume_check: dict[str, Any] | None = None
    blocked_reason: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    interactive: bool = True
    preauthorized: set[str] = field(default_factory=set)
    max_steps: int = field(default_factory=resolve_max_steps)
    llmreview_ran: bool = False
    sim_fail_class: str | None = None
    sim_fail_streak: int = 0
    stuck_reviewed: set[str] = field(default_factory=set)


ConfirmFn = Callable[[str], bool]
ProgressFn = Callable[[str], None]


def build_system_prompt(session: SessionState) -> str:
    """System prompt: identity, status, five tools, safety, pressure discovery."""
    ws = str(session.workspace.resolve())
    if session.robot_ip and session.robot_connected:
        robot_line = f"Robot: connected at {session.robot_ip}"
        if session.active_run_id:
            robot_line += f" (active run {session.active_run_id})"
        else:
            robot_line += " (no active run)"
    elif session.robot_ip:
        robot_line = f"Robot: configured {session.robot_ip} but not connected"
    else:
        robot_line = "Robot: not configured"

    lines = [
        "You are LabscriptAI, a synbio automation agent.",
        f"Workspace: {ws}. {robot_line}.",
        "Available tools:",
        "- bash: local shell in the workspace.",
        "- edit: read/write/str_replace under the workspace.",
        "- robot: status/watch (read) or act (gated).",
        "- memory: case memory for reuse.",
        "- skill: load plugins/skills/{name}.md; empty name lists.",
        "Guidelines:",
        "- Robot actions only through robot. A tool error is an observation — adjust and continue.",
        "- Escalate with no play/resume on: tip_budget.enforced+insufficient; time_window.expired; sample tip touching common_stock. Unknown (basis=none / window undeclared) → load recovery-playbooks.",
        "- liquidNotFound (probe-only, attached tip): recover_liquid_source_substitution once volume_check clears; never resume_run while awaiting-recovery. Clogged aspirate: robot(op=act, action_type=run_pressure_trace) with execute_on_robot not true.",
        "- Write: edit a .py first. Flex: robotType+apiLevel 2.20 only in requirements (not metadata), "
        "load_waste_chute() (occupies D3 — no labware there), load_instrument(..., tip_racks=[tips]), "
        "pipette flex_1channel_50 or flex_1channel_1000 (no 200; >50 µL needs 1000; not OT-2), "
        "modules temperatureModuleV2 / magneticBlockV1. If checks.sim.ok is false keep editing. "
        "No play unless asked live. English prose, not JSON. Do not invent HTTP.",
        "Skills (load on demand): authoring-guide, error-taxonomy, pressure-trace, recovery-playbooks, safety-brief.",
    ]
    return "\n".join(lines)


def ensure_system_message(session: SessionState) -> None:
    prompt = build_system_prompt(session)
    if session.messages and session.messages[0].get("role") == "system":
        session.messages[0] = {"role": "system", "content": prompt}
    else:
        session.messages.insert(0, {"role": "system", "content": prompt})


def _final_text(response: dict[str, Any]) -> str:
    final = response.get("final")
    if isinstance(final, dict):
        msg = final.get("message")
        if isinstance(msg, str) and msg.strip():
            return msg.strip()
        keys = set(final)
        if keys and keys <= {"robotType", "apiLevel", "protocolName", "metadata", "author"}:
            return "Protocol updated."
        return json.dumps(final, ensure_ascii=False)
    if isinstance(final, str) and final.strip():
        return final.strip()
    content = response.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return json.dumps(response, ensure_ascii=False)


def _tool_calls_from(response: dict[str, Any]) -> list[dict[str, Any]]:
    raw = response.get("tool_calls")
    if not isinstance(raw, list):
        return []
    calls: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not name and isinstance(item.get("function"), dict):
            name = item["function"].get("name")
            args = item["function"].get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"_raw": args}
        else:
            args = item.get("arguments") or {}
        if not isinstance(args, dict):
            args = {"_raw": args}
        if not name:
            continue
        calls.append(
            {
                "id": item.get("id") or f"call_{len(calls)}",
                "name": str(name),
                "arguments": args,
            }
        )
    return calls


def _append_assistant(session: SessionState, response: dict[str, Any], calls: list[dict[str, Any]]) -> None:
    canned = response.get("_assistant_message")
    if isinstance(canned, dict) and canned.get("role") == "assistant":
        session.messages.append(dict(canned))
        return
    if calls:
        session.messages.append(
            {
                "role": "assistant",
                "content": response.get("content") or "",
                "tool_calls": [
                    {
                        "id": c["id"],
                        "type": "function",
                        "function": {
                            "name": c["name"],
                            "arguments": json.dumps(c["arguments"], ensure_ascii=False),
                        },
                    }
                    for c in calls
                ],
            }
        )
    else:
        session.messages.append({"role": "assistant", "content": _final_text(response)})


def _append_tool_result(
    session: SessionState,
    *,
    call_id: str,
    name: str,
    payload: Any,
) -> None:
    if not isinstance(payload, str):
        try:
            text = json.dumps(payload, ensure_ascii=False, default=str)
        except TypeError:
            text = str(payload)
    else:
        text = payload
    session.messages.append(
        {
            "role": "tool",
            "tool_call_id": call_id,
            "name": name,
            "content": text,
        }
    )


def _outbox_dir(workspace: Path) -> Path:
    path = Path(workspace) / OUTBOX_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_outbox(
    workspace: Path,
    event: dict[str, Any],
) -> Path:
    """Append a suspend / wake event as a JSONL file under .labscriptai/outbox/."""
    directory = _outbox_dir(workspace)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"suspend_{stamp}.json"
    path.write_text(json.dumps(event, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    # Also append to a rolling wake.jsonl for daemon consumers
    wake = directory / "wake.jsonl"
    with wake.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    return path


def _default_confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _extract_mapping(payload: Any, *keys: str) -> dict[str, Any] | None:
    """Walk nested dicts for the first mapping under any of ``keys``."""
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    for nested_key in ("watch", "robot_status", "result", "data", "suggest_recovery"):
        nested = payload.get(nested_key)
        if nested is payload:
            continue
        found = _extract_mapping(nested, *keys)
        if found is not None:
            return found
        if isinstance(nested, dict):
            data = nested.get("data")
            found = _extract_mapping(data, *keys)
            if found is not None:
                return found
    return None


def _extract_sequence(payload: Any, *keys: str) -> list[Any] | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    for nested_key in ("watch", "robot_status", "result", "data", "suggest_recovery"):
        nested = payload.get(nested_key)
        found = _extract_sequence(nested, *keys)
        if found is not None:
            return found
        if isinstance(nested, dict):
            found = _extract_sequence(nested.get("data"), *keys)
            if found is not None:
                return found
    return None


def _well_key_from_item(item: Mapping[str, Any]) -> str | None:
    from labscriptai.agent.gate import normalize_well_key

    for key in ("well_key", "key", "id", "source_key", "candidate_key"):
        raw = item.get(key)
        if raw:
            normalized = normalize_well_key(raw)
            if normalized:
                return normalized
    slot = (
        item.get("slot")
        or item.get("slot_name")
        or item.get("labware_slot")
        or item.get("labwareSlot")
    )
    well = item.get("well_name") or item.get("wellName") or item.get("well")
    if slot and well:
        return normalize_well_key(f"{slot}.{well}")
    return None


def _derive_well_roles_from_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    """Build well_roles keyed as ``SLOT.WELL`` from MCP live-state fields.

    Preference: wells_summary[].role → well_roles[key] → liquid snapshot well_role.
    Ignores liquid_tracking filter role ``source``.
    """
    try:
        from labscriptai.agent.gate import normalize_pollution_well_role, normalize_well_key
    except ImportError:  # pragma: no cover
        return None

    derived: dict[str, Any] = {}

    wells_summary = _extract_sequence(result, "wells_summary")
    if wells_summary:
        for item in wells_summary:
            if not isinstance(item, Mapping):
                continue
            key = _well_key_from_item(item)
            role = normalize_pollution_well_role(item.get("role"))
            if key and role:
                derived[key] = role

    well_roles = _extract_mapping(result, "well_roles", "well_role_map", "labware_well_roles")
    if isinstance(well_roles, dict):
        for key, value in well_roles.items():
            k = normalize_well_key(key)
            if not k or k in derived:
                continue
            role = normalize_pollution_well_role(value)
            if role:
                derived[k] = role

    for seq_key in ("wells", "well_states", "liquid_sources", "sources"):
        entries = _extract_sequence(result, seq_key)
        if not entries:
            continue
        for item in entries:
            if not isinstance(item, Mapping):
                continue
            key = _well_key_from_item(item)
            if not key or key in derived:
                continue
            role = normalize_pollution_well_role(item.get("well_role"))
            if role:
                derived[key] = role

    return derived or None


_TERMINAL_RUN_STATUSES = frozenset({"succeeded", "stopped"})


def _apply_recovery_gate_fields(
    session: SessionState,
    result: dict[str, Any],
    *,
    tip_budget: dict[str, Any] | None,
    tip_budget_seen: bool,
    volume_check: dict[str, Any] | None,
    volume_seen: bool,
    blocked_reason: str | None,
    blocked_seen: bool,
) -> None:
    """Update tip/volume gate fields; clear when a fresher observation supersedes them."""
    if session.active_run_status in _TERMINAL_RUN_STATUSES:
        session.tip_budget = None
        session.volume_check = None
        session.blocked_reason = None
        return

    fresh_live = (
        _extract_sequence(result, "instruments_summary") is not None
        or _extract_sequence(result, "wells_summary") is not None
        or "suggest_recovery" in result
        or _extract_mapping(result, "recovery", "recovery_suggestion") is not None
    )

    if tip_budget is not None:
        session.tip_budget = dict(tip_budget)
    elif tip_budget_seen or result.get("tip_budget_blocked") is False or fresh_live:
        session.tip_budget = None

    if volume_check is not None:
        session.volume_check = dict(volume_check)
    elif volume_seen or fresh_live:
        session.volume_check = None

    if isinstance(blocked_reason, str) and blocked_reason.strip():
        session.blocked_reason = blocked_reason.strip()
    elif blocked_seen or fresh_live:
        session.blocked_reason = None


def _sync_session_run_status(session: SessionState, result: Any) -> None:
    """Cache latest run status from robot tool payloads for gate decisions."""
    if not isinstance(result, dict):
        return
    status = result.get("active_run_status")
    if isinstance(status, str) and status.strip():
        session.active_run_status = status.strip().lower()
    else:
        for key in ("watch", "robot_status"):
            nested = result.get(key)
            if not isinstance(nested, dict):
                continue
            data = nested.get("data")
            if isinstance(data, dict):
                hist_status = data.get("status")
                if isinstance(hist_status, str) and hist_status.strip():
                    session.active_run_status = hist_status.strip().lower()
                    break
            hist = nested.get("run_history") or nested.get("history")
            if isinstance(hist, dict):
                data = hist.get("data") if isinstance(hist.get("data"), dict) else hist
                if isinstance(data, dict):
                    hist_status = data.get("status")
                    if isinstance(hist_status, str) and hist_status.strip():
                        session.active_run_status = hist_status.strip().lower()
                        break
        else:
            tool_result = result.get("result")
            if isinstance(tool_result, dict):
                data = tool_result.get("data")
                if isinstance(data, dict):
                    final_status = data.get("final_status") or data.get("status")
                    if isinstance(final_status, str) and final_status.strip():
                        session.active_run_status = final_status.strip().lower()

    time_window = _extract_mapping(result, "time_window")
    if time_window is not None:
        session.time_window = dict(time_window)

    instruments = _extract_sequence(result, "instruments_summary")
    if instruments is not None:
        session.instruments_summary = list(instruments)

    derived_roles = _derive_well_roles_from_payload(result)
    if derived_roles is not None:
        session.well_roles = derived_roles

    tip_budget_seen = "tip_budget" in result
    tip_budget = result.get("tip_budget") if tip_budget_seen else None
    if not isinstance(tip_budget, dict):
        tip_budget = _extract_mapping(result, "tip_budget")
        tip_budget_seen = tip_budget_seen or tip_budget is not None
    if tip_budget is None:
        recovery = _extract_mapping(result, "recovery", "recovery_suggestion")
        if isinstance(recovery, dict) and "tip_budget" in recovery:
            tip_budget_seen = True
            nested_tb = recovery.get("tip_budget")
            tip_budget = nested_tb if isinstance(nested_tb, dict) else None

    volume_seen = "volume_check" in result
    volume_check = result.get("volume_check") if volume_seen else None
    if not isinstance(volume_check, dict):
        volume_check = _extract_mapping(result, "volume_check")
        volume_seen = volume_seen or volume_check is not None
    if volume_check is None:
        recovery = _extract_mapping(result, "recovery", "recovery_suggestion")
        if isinstance(recovery, dict) and "volume_check" in recovery:
            volume_seen = True
            nested_vc = recovery.get("volume_check")
            volume_check = nested_vc if isinstance(nested_vc, dict) else None

    blocked_seen = "blocked_reason" in result
    blocked = result.get("blocked_reason") if blocked_seen else None
    if not isinstance(blocked, str) or not blocked.strip():
        recovery = _extract_mapping(result, "recovery", "recovery_suggestion")
        if isinstance(recovery, dict) and "blocked_reason" in recovery:
            blocked_seen = True
            blocked = recovery.get("blocked_reason")
        if (not isinstance(blocked, str) or not blocked.strip()) and isinstance(
            volume_check, dict
        ):
            if "blocked_reason" in volume_check:
                blocked_seen = True
                blocked = volume_check.get("blocked_reason")

    _apply_recovery_gate_fields(
        session,
        result,
        tip_budget=tip_budget if isinstance(tip_budget, dict) else None,
        tip_budget_seen=tip_budget_seen,
        volume_check=volume_check if isinstance(volume_check, dict) else None,
        volume_seen=volume_seen,
        blocked_reason=blocked if isinstance(blocked, str) else None,
        blocked_seen=blocked_seen,
    )


def _tool_error_payload(exc: BaseException, *, tool_name: str) -> dict[str, Any]:
    """Observation payload when a gated-allow tool raises (do not end the turn)."""
    return {
        "status": "error",
        "tool": tool_name,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
        },
        "feedback": (
            "Tool call raised an exception. Treat this as an observation, "
            "not a completed action; decide the next safe step."
        ),
    }


def _latest_user_text(session: SessionState) -> str:
    for message in reversed(session.messages):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""


def _simulate_protocol_path(args: dict[str, Any], workspace: Path) -> Path | None:
    extra = args.get("args") if isinstance(args.get("args"), dict) else {}
    raw = (
        extra.get("file_path")
        or extra.get("protocol_path")
        or extra.get("protocol")
        or args.get("file_path")
        or args.get("protocol_path")
        or args.get("protocol")
    )
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    return resolved if resolved.is_file() else None


_PY_IN_CMD = re.compile(r"""(?<![A-Za-z0-9_])((?:\.?/|[A-Za-z0-9_.-])[^ \t'"\\;|&]*\.py)""")


def _protocol_path_from_bash_command(command: str, workspace: Path) -> Path | None:
    """If bash looks like it wrote a .py under workspace, return that path."""
    if not any(mark in command for mark in (">", "tee", "<<")):
        return None
    workspace = workspace.resolve()
    for match in _PY_IN_CMD.finditer(command):
        raw = match.group(1)
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = workspace / candidate
        try:
            resolved = candidate.resolve()
            resolved.relative_to(workspace)
        except (OSError, ValueError):
            continue
        if resolved.is_file() and resolved.suffix == ".py":
            return resolved
    return None


def _simulate_succeeded(result: Any) -> bool:
    if not isinstance(result, dict) or result.get("error"):
        return False
    inner = result.get("result")
    if isinstance(inner, dict) and inner.get("error"):
        return False
    return True


def _apply_sim_streak(
    session: SessionState,
    checks: dict[str, Any],
    *,
    protocol_source: str,
) -> dict[str, Any]:
    """Count consecutive sim-fail classes; flash once at streak 3. Not llmreview_ran."""
    sim = checks.get("sim") if isinstance(checks.get("sim"), dict) else {}
    if sim.get("ok"):
        session.sim_fail_class = None
        session.sim_fail_streak = 0
        if isinstance(checks.get("llmreview"), dict):
            session.llmreview_ran = True
        return checks

    from labscriptai.agent.checks import STUCK_REVIEW_STREAK, sim_error_class, stuck_llmreview

    klass = sim_error_class(sim) or "sim_failed"
    if klass == session.sim_fail_class:
        session.sim_fail_streak += 1
    else:
        session.sim_fail_class = klass
        session.sim_fail_streak = 1
    if (
        session.sim_fail_streak >= STUCK_REVIEW_STREAK
        and klass not in session.stuck_reviewed
    ):
        checks = dict(checks)
        checks["llmreview"] = stuck_llmreview(
            user_intent=_latest_user_text(session),
            protocol_source=protocol_source,
            sim=sim,
        )
        session.stuck_reviewed.add(klass)
    return checks


def _maybe_attach_authoring_checks(
    name: str,
    args: dict[str, Any],
    result: Any,
    *,
    session: SessionState,
) -> Any:
    """Stuff sim/logicpass/llmreview into edit, bash-written .py, or simulate_protocol."""
    if not isinstance(result, dict) or result.get("error") or result.get("ok") is False:
        return result
    if infer_context is None:
        return result
    context = infer_context(
        robot_connected=bool(session.robot_connected),
        active_run=bool(session.active_run_id),
    )
    if context != "author":
        return result

    workspace = Path(session.workspace)
    protocol_path: Path | None = None
    if name == "edit" and str(args.get("op") or "") in {"write", "str_replace"}:
        rel = args.get("path")
        if isinstance(rel, str) and rel.strip():
            protocol_path = (workspace / rel).resolve()
            if not protocol_path.is_file():
                return result
    elif name == "robot":
        action = str(args.get("action") or args.get("action_type") or "").strip()
        extra = args.get("args") if isinstance(args.get("args"), dict) else {}
        nested_action = str(extra.get("action") or extra.get("action_type") or "").strip()
        if action != "simulate_protocol" and nested_action != "simulate_protocol":
            return result
        if not _simulate_succeeded(result):
            return result
        protocol_path = _simulate_protocol_path(args, workspace)
        if protocol_path is None:
            return result
    elif name == "bash":
        protocol_path = _protocol_path_from_bash_command(
            str(args.get("command") or ""),
            workspace,
        )
        if protocol_path is None:
            return result
    else:
        return result

    if protocol_path is None:
        return result

    try:
        source = protocol_path.read_text(encoding="utf-8")
    except OSError:
        return result

    try:
        from labscriptai.agent.checks import looks_like_opentrons_protocol, run_authoring_checks

        if not looks_like_opentrons_protocol(protocol_path, source):
            return result
        merged = dict(result)
        checks = run_authoring_checks(
            protocol_path,
            user_intent=_latest_user_text(session),
            protocol_source=source,
            skip_review=bool(session.llmreview_ran),
        )
        merged["checks"] = _apply_sim_streak(
            session, checks, protocol_source=source
        )
        return merged
    except Exception as exc:  # noqa: BLE001 — checks must not kill the turn
        merged = dict(result)
        merged["checks"] = {
            "sim": {"ok": False, "reason": "checks_exception", "detail": str(exc)},
        }
        return merged


def _execute_allowed_tool(
    name: str,
    args: dict[str, Any],
    *,
    session: SessionState,
    interactive: bool,
) -> Any:
    try:
        result = execute(
            name,
            args,
            workspace=Path(session.workspace),
            robot_ip=session.robot_ip,
            session={
                "active_run_id": session.active_run_id,
                "robot_connected": session.robot_connected,
                "interactive": interactive,
                "preauthorized": sorted(session.preauthorized),
            },
        )
    except Exception as exc:  # noqa: BLE001 — observation feedback; keep turn alive
        return _tool_error_payload(exc, tool_name=name)
    return _maybe_attach_authoring_checks(name, args, result, session=session)


def _gate_or_raise(
    tool_name: str,
    args: dict[str, Any],
    *,
    session: SessionState,
    interactive: bool,
) -> Any:
    if evaluate is None or infer_context is None:
        raise RuntimeError("W1/W2 未就绪: labscriptai.agent.gate is missing")
    context = infer_context(
        robot_connected=bool(session.robot_connected),
        active_run=bool(session.active_run_id),
    )
    # Help gate see robot IP / workspace (gate reads env for bash red-lines)
    os.environ.setdefault("LABSCRIPTAI_WORKSPACE", str(session.workspace.resolve()))
    if session.robot_ip:
        os.environ.setdefault("LABSCRIPTAI_ROBOT_IP", session.robot_ip)
        os.environ.setdefault("ROBOT_IP", session.robot_ip)
    return evaluate(
        tool_name,
        args,
        context=context,
        interactive=interactive,
        preauthorized=set(session.preauthorized or ()),
        active_run_status=session.active_run_status,
        time_window=session.time_window,
        instruments_summary=session.instruments_summary,
        well_roles=session.well_roles,
        tip_budget=session.tip_budget,
        volume_check=session.volume_check,
        blocked_reason=session.blocked_reason,
    )


def _progress_tool_line(name: str, args: Mapping[str, Any]) -> str:
    extra = args.get("args") if isinstance(args.get("args"), dict) else {}
    if name == "edit":
        return f"edit {args.get('op') or ''} {args.get('path') or ''}".strip()
    if name == "skill":
        return f"skill {str(args.get('name') or '').strip() or 'list'}"
    if name == "bash":
        cmd = " ".join(str(args.get("command") or "").split())
        if len(cmd) > 72:
            cmd = cmd[:72] + "…"
        return f"bash {cmd}"
    if name == "memory":
        return f"memory {args.get('op') or ''}".strip()
    if name == "robot":
        action = str(
            args.get("action")
            or args.get("action_type")
            or extra.get("action")
            or extra.get("action_type")
            or args.get("op")
            or ""
        ).strip()
        return f"robot {action}" if action else "robot"
    return name


def _progress_checks_line(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return None
    bits: list[str] = []
    sim = checks.get("sim") if isinstance(checks.get("sim"), dict) else {}
    if sim.get("ok") is True:
        bits.append("sim=ok")
    elif sim.get("ok") is False:
        errors = sim.get("errors") or []
        detail = str(errors[0] if errors else sim.get("reason") or "failed")[:80]
        bits.append(f"sim=red {detail}")
    lp = checks.get("logicpass") if isinstance(checks.get("logicpass"), dict) else {}
    if lp.get("outcome"):
        bits.append(f"logicpass={lp['outcome']}")
    review = checks.get("llmreview") if isinstance(checks.get("llmreview"), dict) else {}
    if isinstance(review.get("match"), bool):
        bits.append("review=match" if review["match"] else "review=mismatch")
    return "checks " + " · ".join(bits) if bits else None


def _emit(on_event: ProgressFn | None, line: str | None) -> None:
    if on_event is None or not line:
        return
    try:
        on_event(line)
    except Exception:
        return


def run_turn(
    user_text: str,
    *,
    session: SessionState,
    llm: LLMClient,
    interactive: bool | None = None,
    confirm: ConfirmFn | None = None,
    tools_schema: list[dict[str, Any]] | None = None,
    on_event: ProgressFn | None = None,
) -> str:
    """Run one user turn until the model returns a final message or max_steps."""
    if interactive is None:
        interactive = session.interactive
    confirm = confirm or _default_confirm
    schema = tools_schema if tools_schema is not None else TOOLS_SCHEMA

    ensure_system_message(session)
    session.llmreview_ran = False
    session.sim_fail_class = None
    session.sim_fail_streak = 0
    session.stuck_reviewed = set()
    session.messages.append({"role": "user", "content": user_text})

    last_text = ""
    step = 0
    while True:
        step += 1
        if session.max_steps > 0 and step > session.max_steps:
            break
        _emit(on_event, "thinking")
        response = llm.complete(session.messages, tools=schema)
        calls = _tool_calls_from(response)
        if not calls:
            last_text = _final_text(response)
            _append_assistant(session, response, [])
            return last_text

        _append_assistant(session, response, calls)
        for call in calls:
            name = call["name"]
            args = dict(call["arguments"] or {})
            _emit(on_event, _progress_tool_line(name, args))
            decision = _gate_or_raise(name, args, session=session, interactive=interactive)
            status = getattr(decision, "status", None) or (
                decision.get("status") if isinstance(decision, dict) else None
            )
            reasons = list(
                getattr(decision, "reasons", None)
                or (decision.get("reasons") if isinstance(decision, dict) else [])
                or []
            )

            if status == "allow":
                result = _execute_allowed_tool(
                    name, args, session=session, interactive=interactive
                )
                _sync_session_run_status(session, result)
                _emit(on_event, _progress_checks_line(result))
                _append_tool_result(session, call_id=call["id"], name=name, payload=result)
                continue

            if status == "ask" and interactive:
                reason_txt = "; ".join(reasons) or "gated action"
                approved = confirm(f"Allow {name}({json.dumps(args, ensure_ascii=False)})? {reason_txt}")
                if approved:
                    result = _execute_allowed_tool(
                        name, args, session=session, interactive=interactive
                    )
                    _sync_session_run_status(session, result)
                    _emit(on_event, _progress_checks_line(result))
                    _append_tool_result(session, call_id=call["id"], name=name, payload=result)
                else:
                    _emit(on_event, f"denied {name}")
                    _append_tool_result(
                        session,
                        call_id=call["id"],
                        name=name,
                        payload={
                            "status": "denied",
                            "gate": "ask",
                            "reasons": reasons,
                            "feedback": "User declined this tool call at the terminal prompt.",
                        },
                    )
                continue

            # ask (non-interactive) or suspend → outbox + feedback
            event = {
                "kind": "gate_suspend",
                "tool": name,
                "arguments": args,
                "reasons": reasons,
                "run_id": session.active_run_id,
                "robot_ip": session.robot_ip,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            outbox_path = append_outbox(Path(session.workspace), event)
            _emit(on_event, f"suspended {name}")
            _append_tool_result(
                session,
                call_id=call["id"],
                name=name,
                payload={
                    "status": "suspended",
                    "gate": status or "suspend",
                    "reasons": reasons,
                    "outbox": str(outbox_path),
                    "feedback": (
                        "Action suspended pending human review. "
                        f"Details written to {outbox_path}. Do not retry the same act blindly."
                    ),
                },
            )

        # continue loop for model to consume tool results
        continue

    limit_label = str(session.max_steps) if session.max_steps > 0 else "unlimited"
    last_text = (
        f"Stopped after {step} tool steps (limit: {limit_label}) without a final message. "
        "Ask me to continue or narrow the task."
    )
    session.messages.append({"role": "assistant", "content": last_text})
    return last_text


__all__ = (
    "DEFAULT_MAX_STEPS",
    "resolve_max_steps",
    "OUTBOX_DIRNAME",
    "SessionState",
    "TOOLS_SCHEMA",
    "append_outbox",
    "build_system_prompt",
    "ensure_system_message",
    "run_turn",
)
