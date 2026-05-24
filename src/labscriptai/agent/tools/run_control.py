"""run.control P1 dry-run wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult


class RunControlTool:
    name = "run.control"

    def __init__(self, *, adapter: Any = None, live_control_enabled: bool = False) -> None:
        self.adapter = adapter
        self.live_control_enabled = live_control_enabled

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        action_type = str(args.get("action_type", ""))
        dry_run = bool(args.get("dry_run", not self.live_control_enabled))
        content: dict[str, Any] = {"action_type": action_type, "dry_run": dry_run}
        patch: dict[str, Any] = {}
        if not dry_run:
            if self.adapter is None:
                return ToolResult(
                    False,
                    self.name,
                    {"error": "robot_adapter_unavailable", **content},
                    error="robot_adapter_unavailable",
                )
            run_id = str(args.get("run_id") or state.run_id)
            if action_type == "execute_recovery_branch" and hasattr(self.adapter, "execute_suggested_recovery"):
                result = self.adapter.execute_suggested_recovery(
                    robot_ip=str(args.get("robot_ip") or state.robot_status.get("host") or ""),
                    run_id=run_id,
                    suggestion=args,
                )
            elif hasattr(self.adapter, "control_run"):
                result = self.adapter.control_run(run_id=run_id, action_type=action_type)
            else:
                return ToolResult(
                    False,
                    self.name,
                    {"error": "robot_adapter_does_not_support_control", **content},
                    error="robot_adapter_does_not_support_control",
                )
            content["result"] = result
            if isinstance(result, Mapping) and result.get("error"):
                return ToolResult(False, self.name, content, error=str(result.get("error")))
        if action_type == "abort_run":
            patch["phase"] = "aborted"
        elif action_type == "pause_run":
            patch["phase"] = "paused"
        elif action_type in {"resume_run", "execute_recovery_branch"}:
            patch["phase"] = "running"
        return ToolResult(True, self.name, content, state_patch=patch)
