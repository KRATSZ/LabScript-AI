"""v4.7 layered shadow loop with non-terminal missing-tip housekeeping.

The frozen v4.5 harness treats an approved ``mark_resource_unavailable`` as a
terminal action unless the fault is an ordinary clog.  v4.7 keeps that behavior
for ordinary clogs and adds a separate missing-tip chain:

``mark_resource_unavailable`` -> next-tip recovery branch or escalation.

Resource marking updates shadow state, but it is never sufficient on its own to
claim recovery.  This module is development-only and does not mutate the frozen
v4.5/v2/v3 implementations or artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

from .actions import CandidateAction
from .shadow_feedback import (
    MAX_DECISION_STEPS,
    MAX_FEEDBACK_ROUNDS,
    MultistepShadowResult,
    ProposeFn,
    apply_shadow_observation,
    apply_shadow_pending_verify,
    gate_ok,
    is_observation_action,
    is_pending_verify_recovery_action,
)
from .shadow_feedback_v4_5 import run_gatekeeper_feedback_loop_v4_5
from .state import RuntimeState

HARNESS_VERSION = "v4.7"
TIP_PHYSICALLY_MISSING = "TIP_PHYSICALLY_MISSING"
NEXT_TIP_BRANCH = "retry_pick_up_tip_with_next_candidate"
MISSING_TIP_PENDING = "missing_tip_terminal_action"
ESCALATION_ACTION_TYPES = frozenset(
    {"request_human_confirmation", "pause_run", "abort_run"}
)


@dataclass
class MultistepShadowResultV47(MultistepShadowResult):
    """v4.7 result fields for housekeeping and terminal completeness."""

    housekeeping_actions: list[CandidateAction] = field(default_factory=list)
    pending_recovery: bool = False
    terminal_action_complete: bool = False
    repeated_resource_mark: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "housekeeping_action_types": [
                    action.action_type for action in self.housekeeping_actions
                ],
                "pending_recovery": self.pending_recovery,
                "terminal_action_complete": self.terminal_action_complete,
                "repeated_resource_mark": self.repeated_resource_mark,
            }
        )
        return payload


def is_missing_tip_state(state: RuntimeState) -> bool:
    """Return whether visible runtime evidence identifies a missing physical tip."""

    observed = state.observed
    signals = {
        str(observed.get(key) or "").strip().upper()
        for key in ("error_signal", "error_type", "error_leaf", "error_category")
    }
    if TIP_PHYSICALLY_MISSING in signals:
        return True
    return any(str(risk.code).strip().upper() == TIP_PHYSICALLY_MISSING for risk in state.risks)


def is_missing_tip_housekeeping_action(
    action: CandidateAction | Mapping[str, Any] | None,
    state: RuntimeState,
) -> bool:
    """Return whether an approved action only records the failed tip resource."""

    return bool(
        action is not None
        and _action_type(action) == "mark_resource_unavailable"
        and is_missing_tip_state(state)
    )


def apply_missing_tip_housekeeping(
    state: RuntimeState,
    action: CandidateAction,
) -> RuntimeState:
    """Commit one failed-tip mark and expose a neutral follow-up requirement."""

    resource_id = str(action.parameters.get("resource_id") or "").strip()
    if not resource_id:
        raise ValueError("missing-tip housekeeping requires resource_id")

    committed = dict(state.committed)
    unavailable = list(committed.get("unavailable_resources") or [])
    if resource_id in unavailable:
        raise ValueError(f"resource already unavailable: {resource_id}")
    unavailable.append(resource_id)
    committed["unavailable_resources"] = unavailable

    observed = dict(state.observed)
    marked = list(observed.get("missing_tip_marked_resources") or [])
    if resource_id not in marked:
        marked.append(resource_id)
    observed["missing_tip_marked_resources"] = marked
    observed["last_marked_unavailable"] = resource_id
    observed["pending_recovery"] = MISSING_TIP_PENDING
    observed["recovery_chain"] = list(observed.get("recovery_chain") or []) + [
        "mark_resource_unavailable"
    ]
    _append_shadow_step(
        observed,
        action_type=action.action_type,
        kind="missing_tip_resource_housekeeping",
        status="completed",
    )
    observed["last_shadow_recovery_step"] = {
        "action_type": action.action_type,
        "status": "completed_pending_recovery",
        "kind": "missing_tip_resource_housekeeping",
        "message": (
            "The failed tip resource is recorded as unavailable. Select the next state-derived "
            "recovery or escalation action; resource marking alone is not terminal."
        ),
    }
    return replace(state, committed=committed, observed=observed)


def apply_missing_tip_terminal_action(
    state: RuntimeState,
    action: CandidateAction,
) -> RuntimeState:
    """Record the terminal next-tip or escalation decision after housekeeping."""

    observed = dict(state.observed)
    observed.pop("pending_recovery", None)
    branch = str(action.parameters.get("branch") or "")
    chain_item = branch if action.action_type == "execute_recovery_branch" else action.action_type
    observed["recovery_chain"] = list(observed.get("recovery_chain") or []) + [chain_item]
    observed["missing_tip_terminal_action"] = chain_item
    _append_shadow_step(
        observed,
        action_type=action.action_type,
        kind="missing_tip_terminal_decision",
        status="completed",
    )
    return replace(state, observed=observed)


def is_missing_tip_terminal_action(action: CandidateAction) -> bool:
    """Return whether an action resolves the missing-tip decision chain."""

    if action.action_type in ESCALATION_ACTION_TYPES:
        return True
    return bool(
        action.action_type == "execute_recovery_branch"
        and str(action.parameters.get("branch") or "") == NEXT_TIP_BRANCH
    )


def run_multistep_shadow_loop_v4_7(
    *,
    state: RuntimeState,
    propose: ProposeFn,
    allowed_action_types: Sequence[str],
    max_decision_steps: int = MAX_DECISION_STEPS,
    max_format_rounds: int = MAX_FEEDBACK_ROUNDS,
) -> MultistepShadowResultV47:
    """Run v4.5 policy with v4.7 missing-tip continuation semantics."""

    result = MultistepShadowResultV47(final_state=state)
    current = state
    total_format_rounds = 0
    first_step_exec_at_1: bool | None = None

    for step_idx in range(1, max_decision_steps + 1):
        loop = run_gatekeeper_feedback_loop_v4_5(
            state=current,
            propose=propose,
            allowed_action_types=allowed_action_types,
            max_rounds=max_format_rounds,
        )
        result.decision_steps.append(loop)
        result.decision_steps_used = step_idx
        total_format_rounds += loop.feedback_rounds_used
        if first_step_exec_at_1 is None:
            first_step_exec_at_1 = loop.execution_valid_at_1

        action = loop.final_action
        decision = loop.final_decision
        result.final_state = current

        if action is None or decision is None:
            result.stopped_reason = (
                "missing_tip_followup_incomplete"
                if result.pending_recovery
                else "pending_verify_incomplete"
                if result.pending_verify_actions
                else "no_proposal"
            )
            result.pending_verify = bool(result.pending_verify_actions)
            break

        result.final_action = action
        result.final_decision = decision

        if gate_ok(decision) and is_observation_action(action):
            result.observation_actions.append(action)
            result.observation_steps_used = len(result.observation_actions)
            current = apply_shadow_observation(current, action)
            result.final_state = current
            if step_idx < max_decision_steps:
                continue
            result.stopped_reason = "max_decision_steps_exhausted"
            break

        if gate_ok(decision) and is_missing_tip_housekeeping_action(action, current):
            resource_id = str(action.parameters.get("resource_id") or "").strip()
            unavailable = set(current.committed.get("unavailable_resources") or [])
            already_marked = set(current.observed.get("missing_tip_marked_resources") or [])
            if resource_id in unavailable or resource_id in already_marked:
                result.repeated_resource_mark = resource_id
                result.pending_recovery = True
                result.execution_valid_at_k = True
                result.stopped_reason = "repeated_resource_mark"
                break

            result.housekeeping_actions.append(action)
            current = apply_missing_tip_housekeeping(current, action)
            result.final_state = current
            result.pending_recovery = True
            result.recovery_chain = list(current.observed.get("recovery_chain") or [])
            if step_idx < max_decision_steps:
                continue
            result.execution_valid_at_k = True
            result.stopped_reason = "missing_tip_housekeeping_budget_exhausted"
            break

        if gate_ok(decision) and is_pending_verify_recovery_action(action, current):
            result.pending_verify_actions.append(action)
            result.pending_verify_steps_used = len(result.pending_verify_actions)
            current = apply_shadow_pending_verify(current, action)
            result.final_state = current
            result.pending_verify = bool(current.observed.get("pending_verify"))
            result.recovery_chain = list(current.observed.get("recovery_chain") or [])
            if step_idx < max_decision_steps:
                continue
            result.execution_valid_at_k = True
            result.stopped_reason = "pending_verify_budget_exhausted"
            break

        if gate_ok(decision):
            result.execution_valid_at_k = True
            if result.pending_recovery:
                if is_missing_tip_terminal_action(action):
                    current = apply_missing_tip_terminal_action(current, action)
                    result.final_state = current
                    result.pending_recovery = False
                    result.terminal_action_complete = True
                    result.recovery_chain = list(current.observed.get("recovery_chain") or [])
                    result.stopped_reason = "approved_or_escalated"
                else:
                    result.stopped_reason = "missing_tip_followup_incomplete"
                break

            result.pending_verify = bool(
                current.observed.get("pending_verify")
                and action.action_type in ESCALATION_ACTION_TYPES
            )
            result.terminal_action_complete = True
            result.recovery_chain = list(current.observed.get("recovery_chain") or [])
            result.stopped_reason = "approved_or_escalated"
            break

        result.stopped_reason = loop.stopped_reason or "blocked"
        break
    else:
        result.stopped_reason = result.stopped_reason or "max_decision_steps_exhausted"

    result.feedback_rounds_used = total_format_rounds
    result.execution_valid_at_1 = bool(first_step_exec_at_1)
    if not result.execution_valid_at_k and result.decision_steps:
        last = result.decision_steps[-1]
        if last.execution_valid_at_k and result.stopped_reason in {
            "max_decision_steps_exhausted",
            "pending_verify_budget_exhausted",
            "missing_tip_housekeeping_budget_exhausted",
        }:
            result.execution_valid_at_k = True
    return result


def _action_type(action: CandidateAction | Mapping[str, Any]) -> str:
    if isinstance(action, CandidateAction):
        return action.action_type
    return str(action.get("action_type") or "")


def _append_shadow_step(
    observed: dict[str, Any],
    *,
    action_type: str,
    kind: str,
    status: str,
) -> None:
    steps = list(observed.get("shadow_decision_steps") or [])
    steps.append(
        {
            "step": len(steps) + 1,
            "action_type": action_type,
            "status": status,
            "kind": kind,
        }
    )
    observed["shadow_decision_steps"] = steps
