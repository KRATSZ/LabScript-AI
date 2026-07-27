"""Trusted execution evidence for paper-facing runtime recovery scores."""

from __future__ import annotations

from typing import Any, Mapping


SUPPORTED_EXECUTED_RECOVERY_ACTIONS = frozenset(
    {
        "retry_pick_up_tip_with_next_candidate",
        "suggest_new_destination_slot",
        "wait_and_poll_module_status",
        "reconcile_state_first",
        "ordinary_tip_swap_then_reeval",
    }
)


def verified_recovery_execution(
    execution_result: Mapping[str, Any] | None,
    *,
    expected_action: str | None = None,
) -> bool:
    """Return true only for executor-produced execute-and-verify evidence.

    Model-authored candidate parameters are deliberately excluded. The expected
    structure is the result returned by the MCP ``execute_protocol_recovery``
    tool, either as the full result or its ``data`` object.
    """

    if not isinstance(execution_result, Mapping):
        return False
    data = execution_result.get("data")
    if isinstance(data, Mapping):
        payload = data
    else:
        payload = execution_result

    verification = payload.get("verification")
    if not isinstance(verification, Mapping):
        return False

    executed_action = str(
        payload.get("executed_action") or verification.get("action") or ""
    ).strip()
    if executed_action not in SUPPORTED_EXECUTED_RECOVERY_ACTIONS:
        return False
    if expected_action and executed_action != expected_action:
        return False

    required_true = (
        payload.get("success_checked") is True,
        payload.get("verified_success") is True,
        verification.get("success_checked") is True,
        verification.get("verified_success") is True,
        verification.get("original_error_cleared") is True,
        verification.get("final_run_succeeded") is True,
    )
    if not all(required_true):
        return False
    if verification.get("command_required") is True:
        if verification.get("command_succeeded") is not True:
            return False
        if str(verification.get("fixit_command_status") or "").lower() != "succeeded":
            return False
    return True
