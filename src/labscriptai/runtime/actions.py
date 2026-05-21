"""Candidate action model for the LabscriptAI runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

SAFE_ACTION_TYPES = frozenset(
    {
        "simulate_protocol",
        "inspect_robot_state",
        "capture_deck_image",
        "mark_resource_unavailable",
        "choose_alternative_source",
        "request_human_confirmation",
        "propose_continuation_patch",
        "validate_continuation_patch",
        "execute_recovery_branch",
        "pause_run",
        "resume_run",
        "abort_run",
    }
)

READ_ONLY_ACTION_TYPES = frozenset(
    {
        "simulate_protocol",
        "inspect_robot_state",
        "capture_deck_image",
        "propose_continuation_patch",
        "validate_continuation_patch",
    }
)

HARDWARE_ACTION_TYPES = frozenset(
    {
        "capture_deck_image",
        "pause_run",
        "resume_run",
        "abort_run",
        "execute_recovery_branch",
    }
)

HARDWARE_MOVING_ACTION_TYPES = frozenset(
    {
        "resume_run",
        "abort_run",
        "execute_recovery_branch",
    }
)

FORBIDDEN_ACTION_TYPES = frozenset(
    {
        "start_run",
        "play_run",
        "move_labware",
        "move_pipette",
        "pick_up_tip",
        "aspirate",
        "dispense",
        "drop_tip",
        "run_shell_command",
    }
)


@dataclass(frozen=True)
class CandidateAction:
    """An LLM-proposed action before deterministic gatekeeper approval."""

    action_type: str
    reason: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    proposed_by: str = "model"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CandidateAction":
        action_type = payload.get("action_type") or payload.get("type")
        if not isinstance(action_type, str) or not action_type:
            raise ValueError("candidate action requires action_type")
        reason = payload.get("reason", "")
        if not isinstance(reason, str):
            raise ValueError("candidate action reason must be a string")
        parameters = payload.get("parameters", {})
        if not isinstance(parameters, Mapping):
            raise ValueError("candidate action parameters must be an object")
        normalized_parameters = dict(parameters)
        if (
            action_type == "request_human_confirmation"
            and "question" not in normalized_parameters
            and isinstance(normalized_parameters.get("message"), str)
        ):
            normalized_parameters["question"] = normalized_parameters["message"]
        proposed_by = payload.get("proposed_by", "model")
        if not isinstance(proposed_by, str):
            raise ValueError("candidate action proposed_by must be a string")
        return cls(
            action_type=action_type,
            reason=reason,
            parameters=normalized_parameters,
            proposed_by=proposed_by,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "reason": self.reason,
            "parameters": dict(self.parameters),
            "proposed_by": self.proposed_by,
        }
