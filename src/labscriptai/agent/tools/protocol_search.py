"""protocol.search wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.authoring.task_state import AuthoringTaskState
from labscriptai.authoring.tools.registry import AuthoringToolRegistry


class ProtocolSearchTool:
    name = "protocol.search"

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        # This intentionally registers the legacy implementation that existed
        # but was not exposed by AuthoringToolRegistry._tools.
        delegate = AuthoringToolRegistry(
            package_dir=state.package.dir,
            state=AuthoringTaskState(run_id=state.run_id, task_id=state.task_spec.task_id),
        )
        result = delegate._search_protocol_library(dict(args))
        return ToolResult(bool(result.ok), self.name, dict(result.content))
