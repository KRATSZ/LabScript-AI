"""v4.5 development feedback harness using the layered Gatekeeper policy."""

from __future__ import annotations

from collections.abc import Sequence

from .actions import CandidateAction
from .policy_v4_5 import evaluate_action_v4_5
from .shadow_feedback import (
    MAX_DECISION_STEPS,
    MAX_FEEDBACK_ROUNDS,
    FeedbackLoopResult,
    MultistepShadowResult,
    ProposalAttempt,
    ProposeFn,
    apply_shadow_observation,
    apply_shadow_pending_verify,
    build_format_feedback_prompt,
    gate_ok,
    is_format_only_block,
    is_observation_action,
    is_pending_verify_recovery_action,
)
from .state import RuntimeState

HARNESS_VERSION = "v4.5"


def run_gatekeeper_feedback_loop_v4_5(
    *,
    state: RuntimeState,
    propose: ProposeFn,
    allowed_action_types: Sequence[str],
    max_rounds: int = MAX_FEEDBACK_ROUNDS,
) -> FeedbackLoopResult:
    """Run format-only feedback with the v4.5 development Gatekeeper."""

    result = FeedbackLoopResult()
    feedback: str | None = None

    for attempt_idx in range(1, max_rounds + 1):
        action = propose(state, feedback)
        if action is None:
            result.stopped_reason = "no_proposal"
            return result
        if not isinstance(action, CandidateAction):
            action = CandidateAction.from_mapping(action)
        decision = evaluate_action_v4_5(action, state)
        result.attempts.append(
            ProposalAttempt(
                attempt=attempt_idx,
                action=action,
                decision=decision,
                feedback_sent=feedback,
            )
        )

        if gate_ok(decision):
            result.final_action = action
            result.final_decision = decision
            result.execution_valid_at_1 = attempt_idx == 1
            result.execution_valid_at_k = True
            result.feedback_rounds_used = attempt_idx - 1
            result.stopped_reason = "approved_or_escalated"
            return result

        if is_format_only_block(decision) and attempt_idx < max_rounds:
            feedback = build_format_feedback_prompt(
                decision,
                allowed_action_types=allowed_action_types,
            )
            continue

        result.final_action = action
        result.final_decision = decision
        result.execution_valid_at_1 = False
        result.execution_valid_at_k = False
        result.feedback_rounds_used = attempt_idx - 1
        result.stopped_reason = (
            "safety_blocked" if decision.status == "blocked" else "blocked"
        )
        return result

    last = result.attempts[-1]
    result.final_action = last.action
    result.final_decision = last.decision
    result.execution_valid_at_1 = False
    result.execution_valid_at_k = False
    result.feedback_rounds_used = max_rounds - 1
    result.stopped_reason = "max_rounds_exhausted"
    return result


def run_multistep_shadow_loop_v4_5(
    *,
    state: RuntimeState,
    propose: ProposeFn,
    allowed_action_types: Sequence[str],
    max_decision_steps: int = MAX_DECISION_STEPS,
    max_format_rounds: int = MAX_FEEDBACK_ROUNDS,
) -> MultistepShadowResult:
    """Run the bounded multi-step shadow loop through the v4.5 Gatekeeper."""

    result = MultistepShadowResult(final_state=state)
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
            if result.pending_verify_actions:
                result.execution_valid_at_k = True
                result.stopped_reason = "pending_verify_incomplete"
                result.pending_verify = True
            else:
                result.stopped_reason = "no_proposal"
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
            result.pending_verify = bool(
                current.observed.get("pending_verify")
                and action.action_type
                in {"request_human_confirmation", "abort_run", "pause_run"}
            )
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
        if last.execution_valid_at_k and (
            result.stopped_reason
            in {"max_decision_steps_exhausted", "pending_verify_budget_exhausted"}
            or gate_ok(result.final_decision)  # type: ignore[arg-type]
        ):
            result.execution_valid_at_k = True
    return result
