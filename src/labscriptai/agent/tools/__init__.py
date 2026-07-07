"""Unified tool primitives and registration for the runtime wrappers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Mapping, TypeAlias, get_args

from labscriptai.runtime.gatekeeper import GatekeeperDecision

ToolName: TypeAlias = Literal[
    "package.read_write",
    "package.patch",
    "package.validate",
    "package.simulate",
    "robot.inspect",
    "run.control",
    "error.parse",
    "recovery.suggest",
    "skill.search_load",
    "memory.read_write",
    "protocol.search",
    "shell.run",
]
TOOL_NAMES = frozenset(get_args(ToolName))


@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    arguments: Mapping[str, Any] = field(default_factory=dict)
    reason: str = ""
    proposed_by: str = "model"
    call_id: str | None = None

    @classmethod
    def from_model(cls, raw: Mapping[str, Any]) -> "ToolCall":
        from ._legacy_names import normalize_tool_call

        return normalize_tool_call(raw)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": _safe_args(self.arguments),
            "reason": self.reason,
            "proposed_by": self.proposed_by,
            "call_id": self.call_id,
        }


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    name: ToolName
    content: Mapping[str, Any]
    decision: GatekeeperDecision | None = None
    state_patch: Mapping[str, Any] = field(default_factory=dict)
    duration_ms: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "name": self.name,
            "content": dict(self.content),
            "decision": self.decision.to_dict() if self.decision else None,
            "state_patch": _jsonable_patch(self.state_patch),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


def _safe_args(arguments: Mapping[str, Any]) -> dict[str, Any]:
    safe = dict(arguments)
    if "content" in safe and isinstance(safe["content"], str):
        safe["content"] = f"<{len(safe['content'])} chars>"
    return safe


def _jsonable_patch(patch: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(patch), default=str))


def register_default_tools(
    registry: Any,
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
) -> None:
    from .error_parse import ErrorParseTool
    from .memory_read_write import MemoryReadWriteTool
    from .package_patch import PackagePatchTool
    from .package_read_write import PackageReadWriteTool
    from .package_simulate import PackageSimulateTool
    from .package_validate import PackageValidateTool
    from .protocol_search import ProtocolSearchTool
    from .recovery_suggest import RecoverySuggestTool
    from .robot_inspect import RobotInspectTool
    from .run_control import RunControlTool
    from .shell_run import ShellRunTool
    from .skill_search_load import SkillSearchLoadTool

    registry.register(PackageReadWriteTool(skill_mode=skill_mode, tool_profile=tool_profile))
    registry.register(PackagePatchTool(skill_mode=skill_mode, tool_profile=tool_profile))
    registry.register(PackageValidateTool())
    registry.register(
        PackageSimulateTool(
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            simulation_timeout_sec=simulation_timeout_sec,
        )
    )
    registry.register(RobotInspectTool(adapter_factory=robot_adapter_factory, mcp_adapter=mcp_adapter))
    registry.register(RunControlTool(adapter=robot_control_adapter, live_control_enabled=live_control_enabled))
    registry.register(ErrorParseTool(mcp_adapter=mcp_adapter))
    registry.register(RecoverySuggestTool(mcp_adapter=mcp_adapter))
    registry.register(SkillSearchLoadTool(skill_mode=skill_mode))
    registry.register(MemoryReadWriteTool(memory_dir=memory_dir))
    registry.register(ProtocolSearchTool())
    registry.register(ShellRunTool(workspace_root=workspace_root))
