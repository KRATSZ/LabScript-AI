"""Three-state tool gate for the lean agent.

Statuses: allow | ask | suspend.
Context author|run is system-inferred and never sent to the model.
Daemon (interactive=False) upgrades every ask → suspend.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# Minimal SAFE set copied from core/labscriptai/runtime/actions.py
SAFE_ACTION_TYPES: frozenset[str] = frozenset(
    {
        "simulate_protocol",
        "inspect_robot_state",
        "capture_deck_image",
        "mark_resource_unavailable",
        "choose_alternative_source",
        "request_human_confirmation",
        "propose_continuation_patch",
        "validate_continuation_patch",
        "execute_recovery_branch",
        "pause_run",
        "resume_run",
        "abort_run",
    }
)

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


def infer_context(*, robot_connected: bool, active_run: bool) -> ContextName:
    """System-only context bit: no robot or no active run → author."""
    if robot_connected and active_run:
        return "run"
    return "author"


def evaluate(
    tool_name: str,
    args: dict[str, Any],
    *,
    context: ContextName,
    interactive: bool,
    preauthorized: set[str] | None = None,
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
        decision = _eval_robot(args, context=context, preauthorized=preauthorized)
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


def _path_in_workspace(path: str) -> bool:
    if not path or not str(path).strip():
        return False
    workspace = _workspace_root()
    candidate = Path(str(path)).expanduser()
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()
        resolved.relative_to(workspace)
    except (OSError, ValueError):
        return False
    # Also reject obvious escape tokens before resolve edge cases
    parts = Path(str(path)).parts
    if ".." in parts:
        # still ok if resolve stays inside; re-check relative_to already did
        pass
    return True


def _eval_edit(args: dict[str, Any], *, context: ContextName) -> GateDecision:
    path = str(args.get("path") or args.get("file") or "")
    if not path.strip():
        return GateDecision(status="ask", reasons=["edit requires path"], context=context)
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

    # op=act
    if context == "author":
        return GateDecision(
            status="suspend",
            reasons=["robot act suspended in author context (no robot / no active run)"],
            context=context,
        )

    action_type = str(
        args.get("action_type") or args.get("action") or args.get("type") or ""
    ).strip()
    if action_type in SAFE_ACTION_TYPES or action_type in preauthorized:
        return GateDecision(
            status="allow",
            reasons=[f"robot act allowed: {action_type}"],
            context=context,
        )
    return GateDecision(
        status="ask",
        reasons=[
            f"robot act not in SAFE/preauthorized: {action_type or '(missing action_type)'}",
        ],
        context=context,
    )


__all__ = (
    "SAFE_ACTION_TYPES",
    "GateDecision",
    "evaluate",
    "infer_context",
)
