"""package.simulate wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.state import AgentState, ErrorRef
from labscriptai.agent.tools import ToolResult
from labscriptai.authoring.task_state import AuthoringTaskState
from labscriptai.authoring.tools.registry import AuthoringToolRegistry
from labscriptai.runtime.adapters.simulator import simulate_protocol_package


class PackageSimulateTool:
    name = "package.simulate"

    def __init__(
        self,
        *,
        opentrons_python: str | None = None,
        workspace_root: Path | None = None,
        simulation_timeout_sec: int = 180,
    ) -> None:
        self.opentrons_python = opentrons_python
        self.workspace_root = workspace_root
        self.simulation_timeout_sec = simulation_timeout_sec

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        if state.mode == "author":
            delegate = AuthoringToolRegistry(
                package_dir=state.package.dir,
                state=AuthoringTaskState(run_id=state.run_id, task_id=state.task_spec.task_id),
                opentrons_python=self.opentrons_python,
                workspace_root=self.workspace_root,
                simulation_timeout_sec=self.simulation_timeout_sec,
            )
            result = delegate._run_simulate({})
            content = dict(result.content)
            ok = bool(result.ok)
        else:
            content = simulate_protocol_package(
                state.package.dir,
                simulation_pass=bool(args.get("simulation_pass", False)),
            )
            ok = bool(content.get("ok"))
        patch: dict[str, Any] = {
            "phase": "simulating",
            "counters": {"simulator_calls": 1},
        }
        if not ok:
            patch["latest_error"] = ErrorRef(
                category="simulation_failed",
                raw=content,
                parsed=content,
                source="simulate",
            )
        else:
            patch["latest_error"] = None
        return ToolResult(ok, self.name, content, state_patch=patch)
