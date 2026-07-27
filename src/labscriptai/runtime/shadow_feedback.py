"""MAX≤3 Gatekeeper format-only feedback + bounded multi-step shadow loop.

Format feedback is deterministic and must never leak gold labels, R/E hints,
or biology/risk answers. Safety blocks do not retry.

Multi-step (v4 / v4.1): observation actions (``inspect_robot_state``,
``capture_deck_image``) are non-terminal. Ordinary-clog tip quarantine
(``mark_resource_unavailable``) and gated ``ordinary_tip_swap_then_reeval``
are also non-terminal until verify or the decision-step budget is exhausted,
so Assisted vs Autonomous scoring remains distinguishable. The outer loop
continues until a terminal recover / escalate / abort / verify action is
approved, a safety block occurs, or ``MAX_DECISION_STEPS`` is exhausted.
Safety policy is never relaxed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping, Sequence

from .actions import FORBIDDEN_ACTION_TYPES, READ_ONLY_ACTION_TYPES, CandidateAction
from .gatekeeper import GatekeeperDecision, evaluate_action
from .state import RuntimeState
from .tip_clog_policy import (
    ORDINARY,
    ORDINARY_TIP_SWAP_BRANCH,
    classify_tip_clog,
)

MAX_FEEDBACK_ROUNDS = 3
MAX_DECISION_STEPS = 3

# Non-terminal in the multi-step shadow loop (observe then continue).
OBSERVATION_ACTION_TYPES = frozenset(
    {
        "inspect_robot_state",
        "capture_deck_image",
    }
)

# Observation keys copied into synthetic observe payloads (never gold / traps).
_OBSERVE_FACT_KEYS: tuple[str, ...] = (
    "error_signal",
    "error_type",
    "anomaly",
    "tip_clog_class",
    "fault_phase",
    "destination_role",
    "destination_volume_ul",
    "tips_remaining",
    "tips_still_needed",
    "door_status",
    "vision_gate_required",
    "annotated_backup_exists",
    "backup_source_id",
    "liquid_id",
    "tip_contaminated",
    "tip_disposable",
    "tip_attached",
    "required_sensors",
    "resume_requires",
    "next_command",
    "multi_step_hook",
    "observe_then_recover",
    "context_pack",
)

# Schema / missing-field issues → eligible for format-only retry.
_FORMAT_REASON_MARKERS: tuple[str, ...] = (
    "candidate action must include a reason",
    "requires source_id",
    "requires resource_id",
    "requires question",
    "requires parameters.patch",
    "requires a supported branch",
    "requires human_confirmed=true",
    "unknown action type:",
    "forbidden action type:",
    "patch.schema_version must be",
    "patch.recovery_type is invalid",
    "patch.operations must be",
    "must be an object",
    "requires tip",
    "requires source_well",
    "requires destination_well",
    "requires source",
    "requires destination",
    "operations[",
)

# Ledger / phase / risk issues → safety block, no retry.
_SAFETY_REASON_MARKERS: tuple[str, ...] = (
    "blocker risks must be resolved first",
    "is not allowed while phase is",
    "hardware action requires robot identity",
    "reuses already used",
    "exceeds available",
    "already transferred",
    "unavailable resource",
    "execution of a recovery patch requires",
    "must not reuse",
    "not an annotated alternative",
    "not annotated for substitution",
    "liquid_id",
    "has no observed available volume",
    "must retire the contaminated or clogged current tip",
    "must select a fresh tip",
    "resume_run requires explicit human_confirmed",
)

HEADLINE_PROVIDERS = frozenset({"deepseek", "deepseek_with_gold_fallback", "gold_scripted"})


def is_headline_provider(provider: str) -> bool:
    """True when provider counts toward headline (model) metrics."""

    return provider in HEADLINE_PROVIDERS


ProposeFn = Callable[[RuntimeState, str | None], CandidateAction]


@dataclass(frozen=True)
class ProposalAttempt:
    attempt: int
    action: CandidateAction
    decision: GatekeeperDecision
    feedback_sent: str | None = None


@dataclass
class FeedbackLoopResult:
    attempts: list[ProposalAttempt] = field(default_factory=list)
    final_action: CandidateAction | None = None
    final_decision: GatekeeperDecision | None = None
    execution_valid_at_1: bool = False
    execution_valid_at_k: bool = False
    feedback_rounds_used: int = 0
    stopped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_count": len(self.attempts),
            "execution_valid_at_1": self.execution_valid_at_1,
            "execution_valid_at_k": self.execution_valid_at_k,
            "feedback_rounds_used": self.feedback_rounds_used,
            "stopped_reason": self.stopped_reason,
            "attempts": [
                {
                    "attempt": item.attempt,
                    "action": item.action.to_dict(),
                    "gatekeeper": item.decision.to_dict(),
                    "feedback_sent": item.feedback_sent,
                }
                for item in self.attempts
            ],
        }


def is_format_only_block(decision: GatekeeperDecision | Mapping[str, Any]) -> bool:
    """True when Gatekeeper blocked only for schema/format issues."""

    if isinstance(decision, GatekeeperDecision):
        status = decision.status
        reasons = decision.reasons
    else:
        status = str(decision.get("status") or "")
        reasons = tuple(decision.get("reasons") or ())

    if status != "blocked" or not reasons:
        return False

    for reason in reasons:
        text = str(reason)
        if any(marker in text for marker in _SAFETY_REASON_MARKERS):
            return False

    for reason in reasons:
        text = str(reason)
        if not any(marker in text for marker in _FORMAT_REASON_MARKERS):
            return False

    return True


def build_format_feedback_prompt(
    decision: GatekeeperDecision,
    *,
    allowed_action_types: Sequence[str],
) -> str:
    """Deterministic format-only feedback template (no gold / biology leakage)."""

    allowed = ", ".join(sorted(set(allowed_action_types)))
    forbidden = ", ".join(sorted(FORBIDDEN_ACTION_TYPES))
    reason_lines = "\n".join(f"- {reason}" for reason in decision.reasons)
    return (
        "Your previous candidate action was BLOCKED by the Gatekeeper for format/schema issues only.\n"
        "Revise and return exactly one JSON object with fields: action_type, reason, parameters.\n"
        "\n"
        "Gatekeeper rejection reasons:\n"
        f"{reason_lines}\n"
        "\n"
        f"Allowed action_type values for this case: {allowed}\n"
        f"Forbidden action_type values (never propose these): {forbidden}\n"
        "\n"
        "Do not include gold labels, recover-vs-escalate hints, tip counts, or biology answers."
    )


def gate_ok(decision: GatekeeperDecision | Mapping[str, Any]) -> bool:
    status = decision.status if isinstance(decision, GatekeeperDecision) else decision.get("status")
    return status in {"approved", "escalated"}


def is_observation_action(action: CandidateAction | Mapping[str, Any] | None) -> bool:
    """True when the action is a non-terminal observation / sense step."""

    if action is None:
        return False
    action_type = (
        action.action_type if isinstance(action, CandidateAction) else str(action.get("action_type") or "")
    )
    return action_type in OBSERVATION_ACTION_TYPES


def _action_type(action: CandidateAction | Mapping[str, Any] | None) -> str:
    if action is None:
        return ""
    if isinstance(action, CandidateAction):
        return action.action_type
    return str(action.get("action_type") or "")


def _action_params(action: CandidateAction | Mapping[str, Any] | None) -> Mapping[str, Any]:
    if action is None:
        return {}
    if isinstance(action, CandidateAction):
        return action.parameters
    params = action.get("parameters")
    return params if isinstance(params, Mapping) else {}


def build_shadow_observation_payload(state: RuntimeState, action: CandidateAction) -> dict[str, Any]:
    """Case-specific synthetic observation facts (no gold / R-E leakage)."""

    observed = dict(state.observed)
    facts: dict[str, Any] = {}
    for key in _OBSERVE_FACT_KEYS:
        if key in observed and observed[key] not in (None, "", []):
            facts[key] = observed[key]
    # Surface committed tip inventory if present without inventing answers.
    unavailable = state.committed.get("unavailable_resources")
    if unavailable:
        facts["unavailable_resources"] = list(unavailable)
    purpose = _action_params(action).get("purpose")
    if purpose:
        facts["inspect_purpose"] = purpose
    lines = [f"{key}={facts[key]!r}" for key in sorted(facts)]
    summary = "; ".join(lines) if lines else "no additional sensor facts beyond current risks"
    message = (
        f"Observation completed via {action.action_type}. Case-specific facts: {summary}. "
        "Reconcile with runtime_state.observed and risks already present; propose the next "
        "recovery or escalation action. No gold label is provided."
    )
    return {
        "action_type": action.action_type,
        "status": "completed",
        "facts": facts,
        "message": message,
    }


def apply_shadow_observation(state: RuntimeState, action: CandidateAction) -> RuntimeState:
    """Merge a synthetic observation result without leaking gold / R-E labels."""

    observed = dict(state.observed)
    steps = list(observed.get("shadow_decision_steps") or [])
    payload = build_shadow_observation_payload(state, action)
    steps.append(
        {
            "step": len(steps) + 1,
            "action_type": action.action_type,
            "status": "completed",
            "kind": "observation",
        }
    )
    observed["shadow_decision_steps"] = steps
    observed["last_shadow_observation"] = payload
    return state.with_observation(observed)


def is_pending_verify_recovery_action(
    action: CandidateAction | Mapping[str, Any] | None,
    state: RuntimeState,
) -> bool:
    """True when approved recover step still needs tip-swap / verify follow-up (v4.1).

    Enables Assisted vs Autonomous distinction: mark_unavailable or gated tip-swap alone
    is not the end of the story while decision steps remain.
    """

    if action is None:
        return False
    action_type = _action_type(action)
    params = _action_params(action)
    observed = dict(state.observed)
    clog_class = classify_tip_clog(context=observed)
    tip_swaps = int(observed.get("ordinary_tip_swaps_already") or 0)

    if action_type == "mark_resource_unavailable":
        if clog_class != ORDINARY:
            return False
        # Already verified after a tip-swap → terminal.
        if observed.get("ordinary_tip_swap_verified"):
            return False
        return True

    if action_type == "execute_recovery_branch":
        branch = str(params.get("branch") or "")
        if branch != ORDINARY_TIP_SWAP_BRANCH:
            return False
        # Worker 1 Autonomous: tip-swap already success-checked → terminal.
        if params.get("verified_success") is True or params.get("success_checked") is True:
            return False
        if str(params.get("verify_status") or "").lower() in {"ok", "success", "passed"}:
            return False
        if observed.get("ordinary_tip_swap_verified"):
            return False
        # Even if gate fails mid-chain, keep non-terminal only when still ordinary and
        # verify not done — caller may escalate next.
        return clog_class == ORDINARY and not observed.get("ordinary_tip_swap_exhausted")

    if action_type in {"propose_continuation_patch", "validate_continuation_patch"}:
        # Tip-swap shaped patches are non-terminal until verify when ordinary clog.
        if clog_class != ORDINARY:
            return False
        patch = params.get("patch") if isinstance(params.get("patch"), Mapping) else {}
        ops = patch.get("operations") if isinstance(patch, Mapping) else None
        if not isinstance(ops, list):
            return False
        has_use_tip = any(
            isinstance(op, Mapping) and str(op.get("op_type") or "") == "use_tip" for op in ops
        )
        return has_use_tip and not observed.get("ordinary_tip_swap_verified")

    return False


def apply_shadow_pending_verify(
    state: RuntimeState,
    action: CandidateAction,
) -> RuntimeState:
    """Apply mark_unavailable / tip-swap side effects; leave verify pending."""

    observed = dict(state.observed)
    committed = dict(state.committed)
    unavailable = list(committed.get("unavailable_resources") or [])
    steps = list(observed.get("shadow_decision_steps") or [])
    params = dict(action.parameters)
    action_type = action.action_type
    kind = "pending_verify"

    if action_type == "mark_resource_unavailable":
        resource_id = str(params.get("resource_id") or "pipette.current_tip")
        if resource_id not in unavailable:
            unavailable.append(resource_id)
        committed["unavailable_resources"] = unavailable
        observed["last_marked_unavailable"] = resource_id
        observed["pending_verify"] = "ordinary_tip_swap"
        observed["recovery_chain"] = list(observed.get("recovery_chain") or []) + [
            "mark_resource_unavailable"
        ]
        kind = "mark_unavailable_pending_tip_swap"

    elif action_type == "execute_recovery_branch" and str(params.get("branch") or "") == ORDINARY_TIP_SWAP_BRANCH:
        tip_swaps = int(observed.get("ordinary_tip_swaps_already") or 0) + 1
        observed["ordinary_tip_swaps_already"] = tip_swaps
        tips = observed.get("tips_remaining")
        try:
            if tips is not None:
                observed["tips_remaining"] = max(0, int(tips) - 1)
        except (TypeError, ValueError):
            pass
        observed["pending_verify"] = "ordinary_tip_swap_reeval"
        observed["recovery_chain"] = list(observed.get("recovery_chain") or []) + [
            ORDINARY_TIP_SWAP_BRANCH
        ]
        if tip_swaps >= 1:
            # One tip-swap consumed; next failure must escalate.
            observed["ordinary_tip_swap_exhausted"] = True
        kind = "tip_swap_pending_reeval"

    elif action_type in {"propose_continuation_patch", "validate_continuation_patch"}:
        observed["pending_verify"] = "continuation_patch_tip_swap"
        observed["recovery_chain"] = list(observed.get("recovery_chain") or []) + [action_type]
        kind = "patch_pending_verify"

    steps.append(
        {
            "step": len(steps) + 1,
            "action_type": action_type,
            "status": "completed",
            "kind": kind,
            "pending_verify": observed.get("pending_verify"),
        }
    )
    observed["shadow_decision_steps"] = steps
    observed["last_shadow_recovery_step"] = {
        "action_type": action_type,
        "status": "completed_pending_verify",
        "kind": kind,
        "message": (
            "Recovery step applied in shadow; verification or tip-swap follow-up still required "
            "before claiming Autonomous Recover. Escalate if tip-swap already exhausted."
        ),
    }
    # with_observation only updates observed; merge committed via replace pattern.
    updated = state.with_observation(observed)
    if committed != dict(state.committed):
        updated = replace(updated, committed=committed)
    return updated


@dataclass
class MultistepShadowResult:
    """Outer multi-step shadow loop result (observation continues; terminal scores)."""

    decision_steps: list[FeedbackLoopResult] = field(default_factory=list)
    observation_actions: list[CandidateAction] = field(default_factory=list)
    pending_verify_actions: list[CandidateAction] = field(default_factory=list)
    final_action: CandidateAction | None = None
    final_decision: GatekeeperDecision | None = None
    final_state: RuntimeState | None = None
    execution_valid_at_1: bool = False
    execution_valid_at_k: bool = False
    feedback_rounds_used: int = 0
    decision_steps_used: int = 0
    observation_steps_used: int = 0
    pending_verify_steps_used: int = 0
    stopped_reason: str = ""
    # Worker 1 scoring hooks: True when loop ended still needing tip-swap verify.
    pending_verify: bool = False
    recovery_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_steps_used": self.decision_steps_used,
            "observation_steps_used": self.observation_steps_used,
            "pending_verify_steps_used": self.pending_verify_steps_used,
            "execution_valid_at_1": self.execution_valid_at_1,
            "execution_valid_at_k": self.execution_valid_at_k,
            "feedback_rounds_used": self.feedback_rounds_used,
            "stopped_reason": self.stopped_reason,
            "pending_verify": self.pending_verify,
            "recovery_chain": list(self.recovery_chain),
            "observation_action_types": [a.action_type for a in self.observation_actions],
            "pending_verify_action_types": [a.action_type for a in self.pending_verify_actions],
            "decision_steps": [step.to_dict() for step in self.decision_steps],
            "final_action": self.final_action.to_dict() if self.final_action else None,
            "final_decision": self.final_decision.to_dict() if self.final_decision else None,
        }

    @property
    def attempts(self) -> list[ProposalAttempt]:
        """Flattened attempts across decision steps (trace compatibility)."""

        flat: list[ProposalAttempt] = []
        for step in self.decision_steps:
            flat.extend(step.attempts)
        return flat


def run_multistep_shadow_loop(
    *,
    state: RuntimeState,
    propose: ProposeFn,
    allowed_action_types: Sequence[str],
    max_decision_steps: int = MAX_DECISION_STEPS,
    max_format_rounds: int = MAX_FEEDBACK_ROUNDS,
) -> MultistepShadowResult:
    """Bounded multi-step shadow: observe / pending-verify may continue.

    Safety blocks never retry. Format-only blocks still get ≤``max_format_rounds``
    Gatekeeper format feedback per decision step. Observation and ordinary-clog
    tip-swap chain actions are non-terminal while steps remain (v4.1).
    """

    result = MultistepShadowResult(final_state=state)
    current = state
    total_format_rounds = 0
    first_step_exec_at_1: bool | None = None

    for step_idx in range(1, max_decision_steps + 1):
        loop = run_gatekeeper_feedback_loop(
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
            # After a pending-verify step, exhausted scripted queues are incomplete recover
            # (Assisted-eligible), not a crash. Keep prior approved action as final.
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
            # Non-terminal: record observation and continue (if steps remain).
            result.observation_actions.append(action)
            result.observation_steps_used = len(result.observation_actions)
            current = apply_shadow_observation(current, action)
            result.final_state = current
            if step_idx < max_decision_steps:
                continue
            result.stopped_reason = "max_decision_steps_exhausted"
            break

        if gate_ok(decision) and is_pending_verify_recovery_action(action, current):
            # Non-terminal recover chain: mark_unavailable → tip-swap → verify.
            result.pending_verify_actions.append(action)
            result.pending_verify_steps_used = len(result.pending_verify_actions)
            current = apply_shadow_pending_verify(current, action)
            result.final_state = current
            result.pending_verify = bool(current.observed.get("pending_verify"))
            result.recovery_chain = list(current.observed.get("recovery_chain") or [])
            if step_idx < max_decision_steps:
                continue
            # Budget exhausted while still pending verify → not Autonomous yet.
            result.execution_valid_at_k = True
            result.stopped_reason = "pending_verify_budget_exhausted"
            break

        if gate_ok(decision):
            result.execution_valid_at_k = True
            # Clear pending_verify when a terminal escalate / abort / unrelated recover lands.
            if current.observed.get("pending_verify") and action.action_type in {
                "request_human_confirmation",
                "abort_run",
                "pause_run",
            }:
                result.pending_verify = True
            else:
                result.pending_verify = False
            result.recovery_chain = list(current.observed.get("recovery_chain") or [])
            result.stopped_reason = "approved_or_escalated"
            break

        # Format exhausted or safety block — terminal (no further decision steps).
        result.stopped_reason = loop.stopped_reason or "blocked"
        break
    else:
        result.stopped_reason = result.stopped_reason or "max_decision_steps_exhausted"

    result.feedback_rounds_used = total_format_rounds
    result.execution_valid_at_1 = bool(first_step_exec_at_1)
    # If we only observed until step budget, execution_valid_at_k reflects whether
    # the last observation (or blocked terminal) cleared Gatekeeper on its step.
    if not result.execution_valid_at_k and result.decision_steps:
        last = result.decision_steps[-1]
        if last.execution_valid_at_k and (
            result.stopped_reason
            in {"max_decision_steps_exhausted", "pending_verify_budget_exhausted"}
            or gate_ok(result.final_decision)  # type: ignore[arg-type]
        ):
            result.execution_valid_at_k = True
    return result


def run_gatekeeper_feedback_loop(
    *,
    state: RuntimeState,
    propose: ProposeFn,
    allowed_action_types: Sequence[str],
    max_rounds: int = MAX_FEEDBACK_ROUNDS,
) -> FeedbackLoopResult:
    """Run proposal → Gatekeeper loop with format-only retries (MAX≤3)."""

    result = FeedbackLoopResult()
    feedback: str | None = None

    for attempt_idx in range(1, max_rounds + 1):
        action = propose(state, feedback)
        if action is None:
            result.stopped_reason = "no_proposal"
            return result
        if not isinstance(action, CandidateAction):
            action = CandidateAction.from_mapping(action)
        decision = evaluate_action(action, state)
        sent_feedback = feedback
        result.attempts.append(
            ProposalAttempt(
                attempt=attempt_idx,
                action=action,
                decision=decision,
                feedback_sent=sent_feedback,
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
            feedback = build_format_feedback_prompt(decision, allowed_action_types=allowed_action_types)
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


def wrap_candidate_provider(provider: Callable[[RuntimeState], CandidateAction]) -> ProposeFn:
    """Adapt a legacy single-argument provider for the feedback loop."""

    def propose(state: RuntimeState, feedback: str | None) -> CandidateAction:
        del feedback
        raw = provider(state)
        if raw is None:
            return None  # type: ignore[return-value]
        if not isinstance(raw, CandidateAction):
            return CandidateAction.from_mapping(raw)
        return raw

    return propose
