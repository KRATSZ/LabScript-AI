"""Tool registry for the unified agent skeleton."""

from __future__ import annotations

import time
from importlib import import_module
from typing import Any, Callable, Literal, Mapping, Protocol

from labscriptai.agent.gatekeeper import evaluate_tool_call
from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolCall, ToolName, ToolResult
from labscriptai.runtime.trace import TraceEvent


def _model_trace_actor(state: AgentState) -> str:
    if state.mode == "author":
        return state.current_role
    return "model"


class ToolHandler(Protocol):
    name: ToolName

    def spec(self) -> dict[str, Any]: ...

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult: ...


class ToolRegistry:
    def __init__(self, *, skill_mode: str = "light", tool_profile: str = "kb") -> None:
        self.skill_mode = skill_mode
        self.tool_profile = tool_profile
        self._handlers: dict[ToolName, ToolHandler] = {}

    def register(self, handler: ToolHandler) -> None:
        self._handlers[handler.name] = handler

    def list_specs(self, *, mode: Literal["author", "run"]) -> list[dict[str, Any]]:
        if mode == "author":
            names = ["read_file", "write_file", "apply_patch", "json_set", "append_md"]
            if self.tool_profile in {"simulate", "kb", "kb_strong"}:
                names.extend(["run_simulate", "validate_package"])
            if self.tool_profile in {"kb", "kb_strong"} and self.skill_mode != "off":
                names.append("load_skill")
            # protocol.search is registered below, but the legacy authoring
            # surface forgot to expose search_protocol_library. P1 keeps the
            # model-visible surface byte-compatible with tests/test_authoring_agent.py.
            return [{"name": name} for name in sorted(names)]
        return [
            {"name": name}
            for name in [
                "robot.inspect",
                "error.parse",
                "recovery.suggest",
                "run.control",
                "package.read_write",
                "package.patch",
                "package.validate",
                "package.simulate",
                "skill.search_load",
                "memory.read_write",
                "protocol.search",
                "shell.run",
            ]
        ]

    def call_with_gating(self, call: ToolCall, state: AgentState) -> ToolResult:
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="candidate_tool_call",
                actor=_model_trace_actor(state),
                payload=call.to_dict(),
                state_hash=state.stable_hash(),
            )
        )
        decision = evaluate_tool_call(call, state)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="gatekeeper_decision",
                actor="gatekeeper",
                payload=decision.to_dict(),
                state_hash=state.stable_hash(),
            )
        )
        if decision.blocked or decision.escalated:
            return ToolResult(
                ok=False,
                name=call.name,
                content={"blocked": decision.blocked, "escalated": decision.escalated},
                decision=decision,
                error="; ".join(decision.reasons),
            )
        handler = self._handlers.get(call.name)
        if handler is None:
            result = ToolResult(False, call.name, {"error": "unregistered tool"}, decision=decision)
        else:
            started = time.monotonic()
            try:
                result = handler(call.arguments, state)
            except Exception as exc:  # pragma: no cover - tool boundary.
                result = ToolResult(
                    False,
                    call.name,
                    {"error": f"{type(exc).__name__}: {exc}"},
                    error=f"{type(exc).__name__}: {exc}",
                )
            duration_ms = int((time.monotonic() - started) * 1000)
            result = ToolResult(
                ok=result.ok,
                name=result.name,
                content=result.content,
                decision=decision,
                state_patch=result.state_patch,
                duration_ms=result.duration_ms if result.duration_ms is not None else duration_ms,
                error=result.error,
            )
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="tool_result",
                actor="tool",
                payload=result.to_dict(),
                state_hash=state.stable_hash(),
            )
        )
        return result


def build_default_registry(
    *,
    skill_mode: str = "light",
    tool_profile: str = "kb",
    opentrons_python: str | None = None,
    workspace_root: Any = None,
    simulation_timeout_sec: int = 180,
    robot_adapter_factory: Callable[..., Any] | None = None,
    robot_control_adapter: Any = None,
    live_control_enabled: bool = False,
    mcp_adapter: Any = None,
    memory_dir: Any = None,
) -> ToolRegistry:
    register_default_tools = import_module("labscriptai.agent.tools.__init__").register_default_tools

    registry = ToolRegistry(skill_mode=skill_mode, tool_profile=tool_profile)
    register_default_tools(
        registry,
        skill_mode=skill_mode,
        tool_profile=tool_profile,
        opentrons_python=opentrons_python,
        workspace_root=workspace_root,
        simulation_timeout_sec=simulation_timeout_sec,
        robot_adapter_factory=robot_adapter_factory,
        robot_control_adapter=robot_control_adapter,
        live_control_enabled=live_control_enabled,
        mcp_adapter=mcp_adapter,
        memory_dir=memory_dir,
    )
    return registry
