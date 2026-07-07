"""Unified gatekeeper dispatch for tool calls."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import TOOL_NAMES, ToolCall
from labscriptai.runtime.actions import CandidateAction
from labscriptai.runtime.gatekeeper import GatekeeperDecision, evaluate_action
from labscriptai.runtime.state import RuntimeState

SHELL_ALLOWED_COMMANDS = {"ls", "find", "rg", "cat", "sed", "head", "tail", "wc", "python", "uv"}
SHELL_DENIED_COMMANDS = {
    "bash",
    "sh",
    "zsh",
    "pip",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rm",
    "mv",
    "cp",
    "chmod",
    "chown",
    "brew",
    "git",
    "open",
    "osascript",
}


def evaluate_tool_call(call: ToolCall, state: AgentState) -> GatekeeperDecision:
    if call.name not in TOOL_NAMES:
        return GatekeeperDecision(call.name, "blocked", ("unknown tool name",))
    if call.name == "run.control":
        action_type = str(call.arguments.get("action_type", ""))
        action = CandidateAction(
            action_type=action_type,
            reason=call.reason,
            parameters={k: v for k, v in call.arguments.items() if k != "action_type"},
            proposed_by=call.proposed_by,
        )
        return evaluate_action(action, _project_to_runtime_state(state))
    return _evaluate_non_runtime(call, state)


def _project_to_runtime_state(state: AgentState) -> RuntimeState:
    """Project AgentState to RuntimeState for the legacy runtime gatekeeper.

    Mapping table:
    AgentState.run_id -> RuntimeState.run_id
    AgentState.phase -> RuntimeState.phase
    AgentState.robot_status -> RuntimeState.robot
    AgentState.run_status["expected"] -> RuntimeState.expected
    AgentState.run_status["committed"] -> RuntimeState.committed
    AgentState.run_status["observed"] -> RuntimeState.observed
    AgentState.run_status["completed_commands"] -> RuntimeState.completed_commands
    AgentState.run_status["failed_commands"] -> RuntimeState.failed_commands
    AgentState.run_status["used_tips"] -> RuntimeState.used_tips
    AgentState.run_status["treated_wells"] -> RuntimeState.treated_wells
    AgentState.run_status["liquid_transfers"] -> RuntimeState.liquid_transfers
    AgentState.run_status["remaining_plan"] -> RuntimeState.remaining_plan
    AgentState.risks -> RuntimeState.risks
    AgentState.task_spec.autonomy_mode -> RuntimeState.expected["autonomy_mode"]
    """

    run_status = dict(state.run_status)
    expected = dict(run_status.get("expected") or {})
    expected.setdefault("autonomy_mode", state.task_spec.autonomy_mode)
    phase = state.phase
    if phase not in {
        "preflight",
        "simulating",
        "ready",
        "running",
        "recovering",
        "paused",
        "completed",
        "aborted",
    }:
        phase = "preflight"
    return RuntimeState(
        run_id=state.run_id,
        phase=phase,
        robot=dict(state.robot_status),
        expected=expected,
        committed=dict(run_status.get("committed") or {}),
        observed=dict(run_status.get("observed") or {}),
        completed_commands=tuple(run_status.get("completed_commands") or ()),
        failed_commands=tuple(run_status.get("failed_commands") or ()),
        used_tips=tuple(str(item) for item in run_status.get("used_tips") or ()),
        treated_wells=tuple(str(item) for item in run_status.get("treated_wells") or ()),
        liquid_transfers=tuple(run_status.get("liquid_transfers") or ()),
        remaining_plan=tuple(run_status.get("remaining_plan") or ()),
        risks=state.risks,
    )


def _evaluate_non_runtime(call: ToolCall, state: AgentState) -> GatekeeperDecision:
    reasons: list[str] = []
    args = dict(call.arguments)
    op = str(args.get("op", ""))
    if args.get("op") == "__unknown__":
        return GatekeeperDecision(call.name, "blocked", (f"unknown tool: {args.get('raw_name')}",))
    if state.mode == "author":
        if call.name in {"robot.inspect", "error.parse", "recovery.suggest"}:
            reasons.append("not allowed in author mode")
        elif call.name == "run.control":
            reasons.append("not allowed in author mode")
        elif call.name == "shell.run":
            reasons.append("shell.run is not allowed in author mode")
        elif call.name == "memory.read_write" and op == "append" and "memory.write" not in state.permissions:
            reasons.append("memory append is disabled in author mode")
        elif call.name == "skill.search_load" and op == "load" and "skill.search_load" not in state.permissions:
            reasons.append("skill load is disabled")
    else:
        if call.name == "robot.inspect" and not (
            state.robot_status.get("id")
            or state.robot_status.get("serial")
            or state.robot_status.get("host")
            or args.get("host")
            or args.get("robot_ip")
        ):
            reasons.append("robot.inspect requires robot identity or host")
        if call.name == "error.parse" and not args.get("raw_error") and not args.get("run_id"):
            reasons.append("error.parse requires raw_error or run_id")
        if call.name == "package.read_write" and op != "read" and "package.write" not in state.permissions:
            reasons.append("package writes are blocked in run mode")
        if call.name == "package.patch" and "package.write" not in state.permissions:
            reasons.append("package patches are blocked in run mode")
        if call.name == "shell.run" and "shell.run" not in state.permissions:
            reasons.append("shell.run permission is required")
    if call.name == "package.patch":
        path = str(args.get("path", ""))
        if not path:
            reasons.append("package.patch requires path")
        if path.startswith("/") or ".." in path.split("/"):
            reasons.append("package path must stay inside package_dir")
        diff = str(args.get("diff") or args.get("content") or "")
        if not diff.strip():
            reasons.append("package.patch requires diff content")
    if call.name == "package.read_write":
        path = str(args.get("path", ""))
        if op in {"read", "write", "str_replace", "json_set", "append_md"}:
            if not path:
                reasons.append("package.read_write requires path")
            if path.startswith("/") or ".." in path.split("/"):
                reasons.append("package path must stay inside package_dir")
        else:
            reasons.append(f"unknown package.read_write op: {op}")
    if call.name == "protocol.search" and not str(args.get("query", "")).strip():
        reasons.append("protocol.search requires query")
    if call.name == "shell.run":
        command = args.get("command")
        if not isinstance(command, list) or not command:
            reasons.append("shell.run requires command argv list")
        else:
            executable = str(command[0]).rsplit("/", 1)[-1]
            if executable in SHELL_DENIED_COMMANDS or executable not in SHELL_ALLOWED_COMMANDS:
                reasons.append(f"shell.run command is not allowed: {executable}")
            for item in command:
                if not isinstance(item, str):
                    reasons.append("shell.run command argv entries must be strings")
                    break
                lowered = item.lower()
                if ".env" in lowered or "secret" in lowered or "token" in lowered or "api_key" in lowered:
                    reasons.append("shell.run cannot access sensitive paths or names")
                    break
                if item.startswith("/") or ".." in item.split("/"):
                    reasons.append("shell.run paths must stay inside selected cwd")
                    break
        if str(args.get("cwd") or "package") not in {"package", "workspace", "runs"}:
            reasons.append("shell.run cwd must be one of: package, workspace, runs")
    if reasons:
        return GatekeeperDecision(call.name, "blocked", tuple(reasons))
    return GatekeeperDecision(call.name, "approved", ("tool call approved",))
