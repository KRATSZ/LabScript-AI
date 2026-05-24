"""package.read_write wrapper around the legacy authoring file tools."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.authoring.task_state import AuthoringTaskState
from labscriptai.authoring.tools.registry import AuthoringToolRegistry


class PackageReadWriteTool:
    name = "package.read_write"

    def __init__(self, *, skill_mode: str = "light", tool_profile: str = "kb") -> None:
        self.skill_mode = skill_mode
        self.tool_profile = tool_profile

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        op = str(args.get("op", ""))
        method_name = {
            "read": "_read_file",
            "write": "_write_file",
            "str_replace": "_str_replace",
            "json_set": "_json_set",
            "append_md": "_append_md",
        }.get(op)
        if method_name is None:
            return ToolResult(False, self.name, {"error": f"unknown op: {op}"})
        delegate = AuthoringToolRegistry(
            package_dir=state.package.dir,
            state=AuthoringTaskState(run_id=state.run_id, task_id=state.task_spec.task_id),
            skill_mode=self.skill_mode,
            tool_profile=self.tool_profile,
        )
        result = getattr(delegate, method_name)(dict(args))
        patch: dict[str, Any] = {}
        if result.ok:
            patch["package"] = state.refresh_package().package
        return ToolResult(bool(result.ok), self.name, dict(result.content), state_patch=patch)
