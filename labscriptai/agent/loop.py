"""Single agent turn loop: observe → LLM propose → gate → execute → trail.

Mode never enters the model prompt. The model always sees the fixed 5-tool schema.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

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


DEFAULT_MAX_STEPS = 12
OUTBOX_DIRNAME = ".labscriptai/outbox"


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
    messages: list[dict[str, Any]] = field(default_factory=list)
    interactive: bool = True
    preauthorized: set[str] = field(default_factory=set)
    max_steps: int = DEFAULT_MAX_STEPS


ConfirmFn = Callable[[str], bool]


def build_system_prompt(session: SessionState) -> str:
    """8–12 line system prompt: identity, status, five tools, one safety line."""
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
        "You are LabscriptAI, a Synbio automation agent.",
        f"Workspace: {ws}. {robot_line}.",
        "Tools (always these five):",
        "- bash: run local shell commands in the workspace.",
        "- edit: read/write/str_replace files under the workspace.",
        "- robot: status/watch (read) or act (gated recovery/control).",
        "- memory: read/write case memory for reuse.",
        "- skill: load domain markdown skills on demand.",
        "Safety: robot actions only through robot; dangerous calls are gated and you will get feedback.",
        "Tip recovery: when robot(op=status) reports tip_budget_blocked or tip_budget.sufficient=false, stop — do not recover_tip_pickup, play, or resume.",
        "Prefer short replies. Load skills when you need domain detail; do not invent robot HTTP calls.",
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
    )


def run_turn(
    user_text: str,
    *,
    session: SessionState,
    llm: LLMClient,
    interactive: bool | None = None,
    confirm: ConfirmFn | None = None,
    tools_schema: list[dict[str, Any]] | None = None,
) -> str:
    """Run one user turn until the model returns a final message or max_steps."""
    if interactive is None:
        interactive = session.interactive
    confirm = confirm or _default_confirm
    schema = tools_schema if tools_schema is not None else TOOLS_SCHEMA

    ensure_system_message(session)
    session.messages.append({"role": "user", "content": user_text})

    last_text = ""
    for _ in range(max(1, session.max_steps)):
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
                _append_tool_result(session, call_id=call["id"], name=name, payload=result)
                continue

            if status == "ask" and interactive:
                reason_txt = "; ".join(reasons) or "gated action"
                approved = confirm(f"Allow {name}({json.dumps(args, ensure_ascii=False)})? {reason_txt}")
                if approved:
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
                    _append_tool_result(session, call_id=call["id"], name=name, payload=result)
                else:
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

    last_text = (
        f"Stopped after {session.max_steps} tool steps without a final message. "
        "Ask me to continue or narrow the task."
    )
    session.messages.append({"role": "assistant", "content": last_text})
    return last_text


__all__ = (
    "DEFAULT_MAX_STEPS",
    "OUTBOX_DIRNAME",
    "SessionState",
    "TOOLS_SCHEMA",
    "append_outbox",
    "build_system_prompt",
    "ensure_system_message",
    "run_turn",
)
