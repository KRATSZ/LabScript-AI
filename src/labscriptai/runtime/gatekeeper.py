"""Deterministic action gatekeeper for the LabscriptAI runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actions import (
    FORBIDDEN_ACTION_TYPES,
    HARDWARE_ACTION_TYPES,
    HARDWARE_MOVING_ACTION_TYPES,
    READ_ONLY_ACTION_TYPES,
    SAFE_ACTION_TYPES,
    CandidateAction,
)
from .continuation import validate_continuation_patch
from .state import RuntimeState


@dataclass(frozen=True)
class GatekeeperDecision:
    action_type: str
    status: str
    reasons: tuple[str, ...]

    @property
    def approved(self) -> bool:
        return self.status == "approved"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    @property
    def escalated(self) -> bool:
        return self.status == "escalated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "status": self.status,
            "approved": self.approved,
            "reasons": list(self.reasons),
        }


def evaluate_action(action: CandidateAction, state: RuntimeState) -> GatekeeperDecision:
    """Approve, block, or escalate a candidate action deterministically."""

    reasons: list[str] = []

    if action.action_type in FORBIDDEN_ACTION_TYPES:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=(f"forbidden action type: {action.action_type}",),
        )

    if action.action_type not in SAFE_ACTION_TYPES:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=(f"unknown action type: {action.action_type}",),
        )

    if not action.reason.strip():
        reasons.append("candidate action must include a reason")

    if action.action_type in HARDWARE_ACTION_TYPES and not state.has_robot_identity:
        reasons.append("hardware action requires robot identity in runtime state")

    if action.action_type in HARDWARE_MOVING_ACTION_TYPES:
        if state.phase not in {"paused", "recovering", "running"}:
            reasons.append(f"{action.action_type} is not allowed while phase is {state.phase}")
        if state.blocker_risks:
            blocker_codes = ", ".join(risk.code for risk in state.blocker_risks)
            reasons.append(f"blocker risks must be resolved first: {blocker_codes}")

    if action.action_type == "resume_run":
        if not action.parameters.get("human_confirmed"):
            if reasons:
                return GatekeeperDecision(
                    action_type=action.action_type,
                    status="blocked",
                    reasons=tuple(reasons),
                )
            return GatekeeperDecision(
                action_type=action.action_type,
                status="escalated",
                reasons=("resume_run requires explicit human_confirmed=true",),
            )

    if action.action_type == "choose_alternative_source":
        if not action.parameters.get("source_id"):
            reasons.append("choose_alternative_source requires source_id")

    if action.action_type == "mark_resource_unavailable":
        if not action.parameters.get("resource_id"):
            reasons.append("mark_resource_unavailable requires resource_id")

    if action.action_type == "request_human_confirmation":
        if not action.parameters.get("question"):
            reasons.append("request_human_confirmation requires question")

    if action.action_type in {"propose_continuation_patch", "validate_continuation_patch"}:
        patch = action.parameters.get("patch")
        if not isinstance(patch, dict):
            reasons.append(f"{action.action_type} requires parameters.patch")
        else:
            patch_result = validate_continuation_patch(patch, state)
            reasons.extend(patch_result.reasons)

    if action.action_type == "execute_recovery_branch":
        branch = action.parameters.get("branch")
        if branch not in {
            "retry_pick_up_tip_with_next_candidate",
            "suggest_new_destination_slot",
            "wait_and_poll_module_status",
            "reconcile_state_first",
            "continuation_patch",
        }:
            reasons.append("execute_recovery_branch requires a supported branch")
        if not action.parameters.get("human_confirmed"):
            reasons.append("execute_recovery_branch requires human_confirmed=true")
        patch = action.parameters.get("patch")
        if branch == "continuation_patch":
            if not isinstance(patch, dict):
                reasons.append("continuation_patch branch requires parameters.patch")
            else:
                patch_result = validate_continuation_patch(
                    patch,
                    state,
                    require_human_confirmation=True,
                )
                reasons.extend(patch_result.reasons)

    if reasons:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=tuple(reasons),
        )

    approved_reason = "read-only action approved" if action.action_type in READ_ONLY_ACTION_TYPES else "action approved"
    return GatekeeperDecision(
        action_type=action.action_type,
        status="approved",
        reasons=(approved_reason,),
    )
