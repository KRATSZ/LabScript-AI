"""Task-level state for the authoring loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuthoringTaskState:
    run_id: str
    task_id: str
    phase: str = "drafting"
    tool_calls: int = 0
    skill_loads: int = 0
    simulator_calls: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def with_counts(
        self,
        *,
        tool_calls: int = 0,
        skill_loads: int = 0,
        simulator_calls: int = 0,
        phase: str | None = None,
        note: str | None = None,
    ) -> "AuthoringTaskState":
        return AuthoringTaskState(
            run_id=self.run_id,
            task_id=self.task_id,
            phase=phase or self.phase,
            tool_calls=self.tool_calls + tool_calls,
            skill_loads=self.skill_loads + skill_loads,
            simulator_calls=self.simulator_calls + simulator_calls,
            notes=self.notes + ((note,) if note else ()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "phase": self.phase,
            "tool_calls": self.tool_calls,
            "skill_loads": self.skill_loads,
            "simulator_calls": self.simulator_calls,
            "notes": list(self.notes),
        }
