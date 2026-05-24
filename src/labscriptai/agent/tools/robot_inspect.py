"""robot.inspect read-only wrapper."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.runtime.adapters.mcp import OpentronsMcpRuntimeAdapter
from labscriptai.runtime.adapters.robot_http import RobotHttpConfig, RobotHttpReadOnlyAdapter


class RobotInspectTool:
    name = "robot.inspect"

    def __init__(
        self,
        *,
        adapter_factory: Callable[..., Any] | None = None,
        mcp_adapter: Any = None,
    ) -> None:
        self.adapter_factory = adapter_factory
        self.mcp_adapter = mcp_adapter

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        source = str(args.get("source", "http"))
        run_id = args.get("run_id")
        if source == "mcp":
            adapter = self.mcp_adapter or OpentronsMcpRuntimeAdapter()
            robot_ip = str(args.get("robot_ip") or args.get("host") or state.robot_status.get("host"))
            content = adapter.call_tool("robot_status", {"robot_ip": robot_ip})
            return ToolResult(
                ok=not bool(content.get("error")),
                name=self.name,
                content=content,
                state_patch={"robot_status": content, "run_status": {"observed": content}},
            )
        host = str(args.get("host") or state.robot_status.get("host"))
        port = args.get("port")
        if self.adapter_factory is not None:
            adapter = self.adapter_factory(host=host, port=port)
        else:
            adapter = RobotHttpReadOnlyAdapter(
                RobotHttpConfig(host=host, port=int(port) if port is not None else None)
            )
        snapshot = adapter.snapshot(run_id=str(run_id) if run_id else None)
        runtime_state = adapter.state_from_snapshot(run_id=state.run_id, snapshot=snapshot)
        run_status = {
            "observed": dict(runtime_state.observed),
            "completed_commands": list(runtime_state.completed_commands),
            "failed_commands": list(runtime_state.failed_commands),
            "remaining_plan": list(runtime_state.remaining_plan),
        }
        return ToolResult(
            ok=True,
            name=self.name,
            content=snapshot,
            state_patch={
                "phase": runtime_state.phase,
                "robot_status": dict(runtime_state.robot),
                "run_status": run_status,
            },
        )
