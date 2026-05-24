"""error.parse MCP wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState, ErrorRef
from labscriptai.agent.tools import ToolResult
from labscriptai.runtime.adapters.mcp import OpentronsMcpRuntimeAdapter


class ErrorParseTool:
    name = "error.parse"

    def __init__(self, *, mcp_adapter: Any = None) -> None:
        self.mcp_adapter = mcp_adapter

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        if self.mcp_adapter is None and not (args.get("robot_ip") or args.get("run_id")):
            parsed = {"raw_error": args.get("raw_error")}
        else:
            adapter = self.mcp_adapter or OpentronsMcpRuntimeAdapter()
            try:
                parsed = adapter.call_tool("parse_error", dict(args))
            except Exception:
                return ToolResult(False, self.name, {"error": "mcp_unavailable"}, error="mcp_unavailable")
        return ToolResult(
            True,
            self.name,
            parsed,
            state_patch={
                "latest_error": ErrorRef(
                    category=str(parsed.get("category") or parsed.get("error_category") or "runtime_error"),
                    raw=args.get("raw_error"),
                    parsed=parsed,
                    source="robot",
                )
            },
        )
