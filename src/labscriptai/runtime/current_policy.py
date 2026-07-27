"""Current deterministic policy entrypoint for real runtime action gating."""

from __future__ import annotations

from .actions import CandidateAction
from .gatekeeper import GatekeeperDecision
from .policy_v4_5 import POLICY_VERSION, evaluate_action_v4_5
from .state import RuntimeState

CURRENT_POLICY_VERSION = POLICY_VERSION


def evaluate_runtime_action(
    action: CandidateAction,
    state: RuntimeState,
) -> GatekeeperDecision:
    """Evaluate a live/runtime action with the current state-derived policy."""

    return evaluate_action_v4_5(action, state)


__all__ = ["CURRENT_POLICY_VERSION", "evaluate_runtime_action"]
