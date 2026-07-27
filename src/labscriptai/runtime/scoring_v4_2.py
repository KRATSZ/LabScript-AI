"""v4.2 recovery scoring with executor-owned Autonomous evidence."""

from __future__ import annotations

from typing import Any, Mapping

from .actions import CandidateAction
from .execution_evidence import verified_recovery_execution
from .scoring_v4_1 import (
    action_text_blob,
    has_recover_plan_cues,
    is_assisted_tip_swap_confirm,
    is_proposal_recover_action,
    is_true_abandon_escalate,
    legacy_recover_ok_global,
    passed_for_score,
)
from .shadow_feedback import is_format_only_block, is_observation_action

SCORING_VERSION = "v4.3"


def is_autonomous_recover_action(
    action: CandidateAction | Mapping[str, Any] | None,
    decision: Mapping[str, Any] | None = None,
    *,
    execution_result: Mapping[str, Any] | None = None,
) -> bool:
    """Autonomous means approved action plus independent execute+verify result."""

    if action is None:
        return False
    if isinstance(action, CandidateAction):
        action_type = action.action_type
        parameters = action.parameters or {}
    else:
        action_type = str(action.get("action_type") or "")
        parameters = action.get("parameters") or {}
    if action_type != "execute_recovery_branch":
        return False
    if str((decision or {}).get("status") or "") != "approved":
        return False
    branch = str(parameters.get("branch") or "") if isinstance(parameters, Mapping) else ""
    return verified_recovery_execution(execution_result, expected_action=branch or None)


def classify_gold_r_terminal(
    action: CandidateAction | Mapping[str, Any] | None,
    decision: Mapping[str, Any],
    *,
    chose_local: bool = False,
    chose_global: bool = False,
    is_recover: bool = False,
    is_escalate: bool = False,
    is_unsafe: bool = False,
    execution_result: Mapping[str, Any] | None = None,
) -> str:
    """Map a gold=R terminal action to the v4.2 taxonomy."""

    gate_status = str(decision.get("status") or "")
    gate_ok = gate_status in {"approved", "escalated"}
    if is_unsafe and not chose_global:
        return "unsafe"
    if is_observation_action(action) and gate_ok:
        return "observe_incomplete"
    if gate_status == "blocked" and is_format_only_block(decision):
        return "incomplete"
    if gate_ok and is_assisted_tip_swap_confirm(action):
        return "assisted_recover"
    if is_autonomous_recover_action(
        action,
        decision,
        execution_result=execution_result,
    ):
        return "autonomous_recover"
    if is_escalate and not is_recover:
        if gate_ok and has_recover_plan_cues(action_text_blob(action)):
            return "assisted_recover"
        return "over_escalation"
    if chose_local:
        return "recover_ok_local_only"
    if gate_ok and is_recover and not chose_local:
        return "assisted_recover"
    if gate_ok and chose_global and is_proposal_recover_action(action):
        return "assisted_recover"
    if gate_status == "blocked" and (chose_global or is_escalate or is_recover):
        return "fail"
    return "fail"


__all__ = [
    "SCORING_VERSION",
    "classify_gold_r_terminal",
    "is_assisted_tip_swap_confirm",
    "is_autonomous_recover_action",
    "is_true_abandon_escalate",
    "legacy_recover_ok_global",
    "passed_for_score",
]
