"""Development policy fixes layered on top of the frozen v4.4 contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .actions import CandidateAction
from .gatekeeper import GatekeeperDecision, evaluate_action
from .holdout_benchmark import action_matches
from .recovery_contract import validate_alternative_source
from .state import RuntimeState
from .tip_clog_policy import ordinary_tip_swap_gate

POLICY_VERSION = "v4.5"
STOP_ACTION_TYPES = frozenset({"pause_run", "abort_run"})
_BLOCKER_REASON_PREFIX = "blocker risks must be resolved first:"


def evaluate_action_v4_5(
    action: CandidateAction,
    state: RuntimeState,
) -> GatekeeperDecision:
    """Apply v4.5 stop semantics without changing the frozen v4.4 Gatekeeper."""

    decision = evaluate_action(action, state)
    if action.action_type == "choose_alternative_source" and decision.approved:
        decision = _validate_state_required_source_contract(action, state)
        if decision.blocked:
            return decision
    if action.action_type == "execute_recovery_branch" and decision.approved:
        decision = _validate_recovery_branch_contract(action, state)
        if decision.blocked:
            return decision
    if action.action_type not in STOP_ACTION_TYPES or not decision.blocked:
        return decision

    remaining_reasons = tuple(
        reason
        for reason in decision.reasons
        if not reason.startswith(_BLOCKER_REASON_PREFIX)
    )
    if remaining_reasons:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=remaining_reasons,
        )

    return GatekeeperDecision(
        action_type=action.action_type,
        status="approved",
        reasons=("stop action approved; existing blockers do not prevent stopping",),
    )


def _validate_state_required_source_contract(
    action: CandidateAction,
    state: RuntimeState,
) -> GatekeeperDecision:
    required_volume_raw = _first_present(
        action.parameters,
        state.expected,
        state.committed,
        state.observed,
        key="required_volume_ul",
    )
    try:
        required_volume = (
            float(required_volume_raw) if required_volume_raw is not None else None
        )
    except (TypeError, ValueError):
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=("required_volume_ul in action or runtime state must be numeric",),
        )

    required_liquid = str(
        state.expected.get("required_liquid_id")
        or state.committed.get("required_liquid_id")
        or state.observed.get("required_liquid_id")
        or action.parameters.get("liquid_id")
        or ""
    ).strip()
    validation = validate_alternative_source(
        state,
        source_id=str(action.parameters.get("source_id") or ""),
        liquid_id=required_liquid or None,
        required_volume_ul=required_volume,
    )
    if not validation.ok:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=validation.reasons,
        )
    return GatekeeperDecision(
        action_type=action.action_type,
        status="approved",
        reasons=("action approved; annotated source satisfies state requirements",),
    )


def _validate_recovery_branch_contract(
    action: CandidateAction,
    state: RuntimeState,
) -> GatekeeperDecision:
    branch = str(action.parameters.get("branch") or "")
    validators = {
        "retry_pick_up_tip_with_next_candidate": _validate_next_tip_retry,
        "wait_and_poll_module_status": _validate_module_poll,
        "reconcile_state_first": _validate_reconciliation,
        "ordinary_tip_swap_then_reeval": _validate_ordinary_tip_swap,
    }
    validator = validators.get(branch)
    if validator is None:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="approved",
            reasons=("action approved",),
        )
    reasons = validator(state)
    if reasons:
        return GatekeeperDecision(
            action_type=action.action_type,
            status="blocked",
            reasons=tuple(reasons),
        )
    return GatekeeperDecision(
        action_type=action.action_type,
        status="approved",
        reasons=(f"{branch} satisfies the state-derived recovery gate",),
    )


def _validate_next_tip_retry(state: RuntimeState) -> list[str]:
    ctx = _state_context(state)
    reasons: list[str] = []
    retry_count = _number(ctx.get("retry_count"))
    retry_limit = _number(ctx.get("retry_limit", ctx.get("retry_max")))
    if retry_count is not None and retry_limit is not None and retry_count >= retry_limit:
        reasons.append("next-tip retry limit has been reached")

    tips_remaining = _number(ctx.get("tips_remaining"))
    tips_required = _number(ctx.get("tips_required_total"))
    if tips_required is None:
        components = (
            _number(ctx.get("tips_still_needed")),
            _number(ctx.get("reserved_sterile_tips")),
            _number(ctx.get("remaining_probe_tip_cost")),
        )
        present = [value for value in components if value is not None]
        tips_required = sum(present) if present else None
    if (
        tips_remaining is not None
        and tips_required is not None
        and tips_remaining < tips_required
    ):
        reasons.append(
            f"tip inventory {tips_remaining:g} is below required total {tips_required:g}"
        )
    return reasons


def _validate_module_poll(state: RuntimeState) -> list[str]:
    ctx = _state_context(state)
    reasons: list[str] = []
    if ctx.get("fault_latched") is True:
        reasons.append("module fault is latched")

    poll_count = _number(ctx.get("poll_count"))
    max_polls = _number(ctx.get("max_poll_count", ctx.get("max_polls")))
    if poll_count is not None and max_polls is not None and poll_count >= max_polls:
        reasons.append("module poll budget is exhausted")

    elapsed_wait = _number(ctx.get("elapsed_wait_s"))
    max_wait = _number(ctx.get("max_wait_s"))
    if elapsed_wait is not None and max_wait is not None and elapsed_wait >= max_wait:
        reasons.append("module wait-time budget is exhausted")
    return reasons


def _validate_reconciliation(state: RuntimeState) -> list[str]:
    committed = dict(state.committed)
    observed = dict(state.observed)
    reasons: list[str] = []
    raw_diffs = observed.get("reconciliation_diff_types")
    diffs = {
        str(item).strip().lower()
        for item in raw_diffs
        if str(item).strip()
    } if isinstance(raw_diffs, (list, tuple, set)) else set()
    if not diffs or not diffs.issubset({"module_status"}):
        reasons.append("reconciliation is not limited to module status")

    committed_hash = str(committed.get("deck_layout_hash") or "").strip()
    observed_hash = str(
        observed.get("deck_layout_hash")
        or observed.get("observed_deck_layout_hash")
        or ""
    ).strip()
    if committed_hash and observed_hash and committed_hash != observed_hash:
        reasons.append("observed deck hash differs from committed state")
    if observed.get("labware_identity_match") is False:
        reasons.append("observed labware identity differs from committed state")

    identity_keys = {
        "labware_id",
        "labware_slot",
        "module_id",
        "module_slot",
        *(
            key
            for key in committed
            if key.startswith("slot_") or key.endswith("_slot")
        ),
    }
    mismatched = [
        key
        for key in sorted(identity_keys)
        if key in committed and key in observed and committed[key] != observed[key]
    ]
    if mismatched:
        reasons.append(
            "observed placement or identity differs for: " + ", ".join(mismatched)
        )
    return reasons


def _validate_ordinary_tip_swap(state: RuntimeState) -> list[str]:
    ctx = _state_context(state)
    if "operation_phase" in ctx and "fault_phase" not in ctx:
        ctx["fault_phase"] = ctx["operation_phase"]
    if "destination_delivered_volume_ul" in ctx and "destination_volume_ul" not in ctx:
        ctx["destination_volume_ul"] = ctx["destination_delivered_volume_ul"]
    if ctx.get("delivered_volume_known") is False:
        ctx["well_volume_unknown"] = True
    if ctx.get("source_identity_intact") is False:
        ctx["source_identity_unknown"] = True
    tip_swaps = int(_number(ctx.get("ordinary_tip_swaps_already")) or 0)
    gate = ordinary_tip_swap_gate(ctx, tip_swaps_already=tip_swaps)
    if gate["allowed"]:
        return []
    return [
        "ordinary tip-swap gate failed: " + ", ".join(gate["block_reasons"])
    ]


def _state_context(state: RuntimeState) -> dict[str, Any]:
    return {**dict(state.expected), **dict(state.committed), **dict(state.observed)}


def _number(raw: Any) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _first_present(*containers: Mapping[str, Any], key: str) -> Any:
    for container in containers:
        if key in container:
            return container[key]
    return None


def action_matches_v4_5(
    action: CandidateAction,
    spec: Mapping[str, Any],
    state: RuntimeState,
) -> bool:
    """Match actions while allowing state-proven redundant liquid identity."""

    if action_matches(action, spec):
        return True
    if action.action_type != "choose_alternative_source":
        return False

    expected_parameters = spec.get("parameters")
    if not isinstance(expected_parameters, Mapping):
        return False
    expected_liquid = str(expected_parameters.get("liquid_id") or "").strip()
    expected_source = str(expected_parameters.get("source_id") or "").strip()
    actual_source = str(action.parameters.get("source_id") or "").strip()
    if not expected_liquid or not expected_source or actual_source != expected_source:
        return False
    if "liquid_id" in action.parameters:
        return False

    missing_parameters = set(expected_parameters).difference(action.parameters)
    if missing_parameters != {"liquid_id"}:
        return False
    if _annotated_liquid_ids(state, actual_source) != {expected_liquid}:
        return False

    validation = validate_alternative_source(
        state,
        source_id=actual_source,
        liquid_id=expected_liquid,
    )
    if not validation.ok:
        return False

    enriched = CandidateAction(
        action_type=action.action_type,
        reason=action.reason,
        parameters={**dict(action.parameters), "liquid_id": expected_liquid},
        proposed_by=action.proposed_by,
    )
    return action_matches(enriched, spec)


def _annotated_liquid_ids(state: RuntimeState, source_id: str) -> set[str]:
    liquid_ids: set[str] = set()
    for container in (state.expected, state.committed, state.observed):
        for key in (
            "annotated_alternative_sources",
            "alternative_sources",
            "liquid_inventory",
        ):
            _collect_source_liquids(liquid_ids, container.get(key), source_id)

        if (
            container.get("annotated_backup_exists") is True
            and str(container.get("backup_source_id") or "").strip() == source_id
        ):
            liquid_id = str(container.get("liquid_id") or "").strip()
            if liquid_id:
                liquid_ids.add(liquid_id)
    return liquid_ids


def _collect_source_liquids(target: set[str], raw: Any, source_id: str) -> None:
    if isinstance(raw, Mapping):
        record = raw.get(source_id)
        if isinstance(record, Mapping) and record.get("annotated") is not False:
            liquid_id = str(record.get("liquid_id") or "").strip()
            if liquid_id:
                target.add(liquid_id)
        return

    if not isinstance(raw, (list, tuple)):
        return
    for record in raw:
        if not isinstance(record, Mapping) or record.get("annotated") is False:
            continue
        record_id = str(record.get("source_id") or record.get("id") or "").strip()
        if record_id != source_id:
            continue
        liquid_id = str(record.get("liquid_id") or "").strip()
        if liquid_id:
            target.add(liquid_id)
