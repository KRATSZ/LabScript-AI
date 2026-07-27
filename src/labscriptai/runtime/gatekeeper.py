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
from .recovery_contract import validate_alternative_source
from .state import RuntimeState

SUPPORTED_RECOVERY_BRANCHES = frozenset(
    {
        "retry_pick_up_tip_with_next_candidate",
        "suggest_new_destination_slot",
        "wait_and_poll_module_status",
        "reconcile_state_first",
        "continuation_patch",
        # v4.1 gated ordinary TIP_CLOG: one tip-swap then re-eval (see tip_clog_policy).
        "ordinary_tip_swap_then_reeval",
    }
)


def is_supported_recovery_branch(branch: str) -> bool:
    return branch in SUPPORTED_RECOVERY_BRANCHES


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
    autonomy_mode = str(state.expected.get("autonomy_mode", "conservative"))

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

    observed_pause = state.observed.get("observed_pause_s")
    max_pause = state.observed.get("max_pause_s")
    try:
        pause_breached = (
            observed_pause is not None
            and max_pause is not None
            and float(observed_pause) > float(max_pause)
        )
    except (TypeError, ValueError):
        pause_breached = False
    if pause_breached and action.action_type in {
        "mark_resource_unavailable",
        "choose_alternative_source",
        "propose_continuation_patch",
        "validate_continuation_patch",
        "resume_run",
    }:
        reasons.append("biology pause window exceeded; recovery continuation requires escalation")
    if pause_breached and action.action_type == "execute_recovery_branch":
        branch = str(action.parameters.get("branch") or "")
        if branch != "wait_and_poll_module_status":
            reasons.append("biology pause window exceeded; recovery continuation requires escalation")

    if action.action_type in HARDWARE_ACTION_TYPES and not state.has_robot_identity:
        reasons.append("hardware action requires robot identity in runtime state")

    if action.action_type in HARDWARE_MOVING_ACTION_TYPES:
        if state.phase not in {"paused", "recovering", "running"}:
            reasons.append(f"{action.action_type} is not allowed while phase is {state.phase}")
        if state.blocker_risks:
            blocker_codes = ", ".join(risk.code for risk in state.blocker_risks)
            reasons.append(f"blocker risks must be resolved first: {blocker_codes}")

    if action.action_type == "resume_run":
        if not action.parameters.get("human_confirmed") and autonomy_mode != "auto":
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
        source_id = str(action.parameters.get("source_id") or "").strip()
        if not source_id:
            reasons.append("choose_alternative_source requires source_id")
        else:
            required_volume = action.parameters.get("required_volume_ul")
            try:
                required_volume_ul = (
                    float(required_volume) if required_volume is not None else None
                )
            except (TypeError, ValueError):
                reasons.append("choose_alternative_source required_volume_ul must be numeric")
                required_volume_ul = None
            source_result = validate_alternative_source(
                state,
                source_id=source_id,
                liquid_id=str(action.parameters.get("liquid_id") or "") or None,
                required_volume_ul=required_volume_ul,
            )
            reasons.extend(source_result.reasons)

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
        if not is_supported_recovery_branch(str(branch or "")):
            reasons.append("execute_recovery_branch requires a supported branch")
        if not action.parameters.get("human_confirmed") and autonomy_mode != "auto":
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
