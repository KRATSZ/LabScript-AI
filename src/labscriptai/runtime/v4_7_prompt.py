"""Finalized v4.7 prompt for missing-tip multi-step development and holdouts."""

from __future__ import annotations

from typing import Any

from .holdout_benchmark import HoldoutCase, ProviderFactory
from .model_adapter import OpenAICompatibleCandidateProvider, OpenAICompatibleConfig
from .state import RuntimeState
from .v4_6_model_benchmark import V461_SYSTEM_PROMPT

PROMPT_VERSION = "v4.7.1"

_V461_MISSING_TIP_RULE = (
    "- A first missing tip may use the next candidate only when retry cap and total tip budget permit. "
    "Tip wells are consumable resources, not liquid sources: never use choose_alternative_source "
    "for TIP_PHYSICALLY_MISSING. Mark the failed tip with mark_resource_unavailable and/or use "
    "execute_recovery_branch branch=retry_pick_up_tip_with_next_candidate. At the retry cap or "
    "with insufficient total tips, stop and escalate."
)
_V47_MISSING_TIP_RULE = (
    "- TIP_PHYSICALLY_MISSING is a two-step decision when failed_tip is not already listed in "
    "committed.unavailable_resources. First return mark_resource_unavailable with "
    "parameters.resource_id exactly equal to observed.failed_tip. This is housekeeping, not a "
    "terminal recovery; never repeat the same mark. On the next decision, use "
    "execute_recovery_branch branch=retry_pick_up_tip_with_next_candidate only when retry cap and "
    "total tip budget permit. When tips_required_total is present, the exact gate is "
    "tips_remaining >= tips_required_total; a smaller tips_remaining value is insufficient and "
    "must escalate. Only derive the required total from component counters when "
    "tips_required_total is absent. At the retry cap or with insufficient total tips, request "
    "human confirmation, pause, or abort instead. Tip wells are consumable resources, not liquid "
    "sources: never use choose_alternative_source for TIP_PHYSICALLY_MISSING."
)

if _V461_MISSING_TIP_RULE not in V461_SYSTEM_PROMPT:  # pragma: no cover - import-time contract
    raise RuntimeError("v4.6.1 missing-tip rule changed; v4.7 prompt must be reviewed")

V47_SYSTEM_PROMPT = V461_SYSTEM_PROMPT.replace(
    _V461_MISSING_TIP_RULE,
    _V47_MISSING_TIP_RULE,
    1,
)


def deepseek_v4_7_provider_factory(config: OpenAICompatibleConfig) -> ProviderFactory:
    provider = OpenAICompatibleCandidateProvider(config, system_prompt=V47_SYSTEM_PROMPT)

    def factory(_case: HoldoutCase) -> Any:
        def propose(state: RuntimeState, feedback: str | None) -> Any:
            return provider(state, format_feedback=feedback)

        return propose

    return factory
