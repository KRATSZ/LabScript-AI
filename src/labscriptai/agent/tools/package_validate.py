"""package.validate wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState, ErrorRef
from labscriptai.agent.tools import ToolResult
from labscriptai.benchmark.package_validator import validate_package


class PackageValidateTool:
    name = "package.validate"

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        result = validate_package(
            state.package.dir,
            simulation_pass=bool(args.get("simulation_pass", False)),
        ).to_dict()
        patch: dict[str, Any] = {
            "phase": "validating",
            "package": state.refresh_package(last_validation=result).package,
        }
        if not result.get("ok"):
            patch["latest_error"] = ErrorRef(
                category="validation_failed",
                raw=result,
                parsed=result,
                source="validate",
            )
        else:
            patch["latest_error"] = None
        return ToolResult(bool(result.get("ok")), self.name, {"validation": result}, state_patch=patch)
