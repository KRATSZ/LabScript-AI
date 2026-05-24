"""recovery.suggest MCP wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.runtime.adapters.mcp import OpentronsMcpRuntimeAdapter


class RecoverySuggestTool:
    name = "recovery.suggest"

    def __init__(self, *, mcp_adapter: Any = None) -> None:
        self.mcp_adapter = mcp_adapter

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        adapter = self.mcp_adapter
        if adapter is None:
            if not args.get("robot_ip"):
                return ToolResult(False, self.name, {"error": "mcp_unavailable"}, error="mcp_unavailable")
            adapter = OpentronsMcpRuntimeAdapter()
        try:
            content = adapter.call_tool("suggest_recovery_action", dict(args))
        except Exception:
            return ToolResult(False, self.name, {"error": "mcp_unavailable"}, error="mcp_unavailable")
        return ToolResult(not bool(content.get("error")), self.name, content)
