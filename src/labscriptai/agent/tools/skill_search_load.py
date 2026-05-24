"""skill.search_load wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.authoring.skills import SkillLoader


class SkillSearchLoadTool:
    name = "skill.search_load"

    def __init__(self, *, skill_mode: str = "light", skill_loader: SkillLoader | None = None) -> None:
        self.skill_mode = skill_mode
        self.skill_loader = skill_loader or SkillLoader()

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        op = str(args.get("op", "list"))
        if op == "list":
            return ToolResult(True, self.name, {"skills": self.skill_loader.list_skills()})
        name = str(args.get("name", ""))
        if self.skill_mode == "light" and name not in {"common_errors", "deck_layout"}:
            return ToolResult(False, self.name, {"error": "skill disabled in light mode"})
        content = self.skill_loader.get_content(name)
        if content is None:
            return ToolResult(False, self.name, {"error": "unknown skill", "available": self.skill_loader.list_skills()})
        return ToolResult(
            True,
            self.name,
            {"name": name, "content": content},
            state_patch={"loaded_skills_append": name, "counters": {"skill_loads": 1}},
        )
