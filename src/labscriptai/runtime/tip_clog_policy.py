"""Ordinary vs dangerous TIP_CLOG policy (Flex15 F09 vs F10).

Ordinary clog (proposal-level Recover allowed; gated auto tip-swap when all checks pass):
  - destination_role=waste / pre-sample tip path
  - aspirate interrupted with zero destination delivery
  - sealed/bent tip before dispense into assay

Dangerous clog (must escalate / stop):
  - mid-dispense into sample / live-cell / assay well
  - destination well volume unknown (partial delivery)
  - identity/contamination unknown after clog into precious well

v4.1 gated branch ``ordinary_tip_swap_then_reeval`` (one tip-swap then re-eval):
  ALL of: ordinary class; clog at aspirate/waste; dest received vol=0; tip discardable;
  source identity intact; tip budget OK. Fail / second attempt → escalate.
"""

from __future__ import annotations

from typing import Any, Mapping

ORDINARY = "ordinary"
DANGEROUS = "dangerous"

# Gatekeeper / MCP recovery branch id (v4.1).
ORDINARY_TIP_SWAP_BRANCH = "ordinary_tip_swap_then_reeval"

_DANGEROUS_DEST_ROLES = frozenset(
    {
        "live_cell",
        "live_cell_culture",
        "culture",
        "assay",
        "sample",
        "precious_sample",
        "master_mix_well",
    }
)
_ORDINARY_DEST_ROLES = frozenset({"waste", "trash", "waste_chute"})
_ORDINARY_FAULT_PHASES = frozenset(
    {
        "aspirate",
        "pre_dispense",
        "pre-dispense",
        "waste_dispense",
        "waste",
    }
)


def classify_tip_clog(
    *,
    destination_role: str | None = None,
    dispense_interrupted: bool | None = None,
    well_volume_unknown: bool | None = None,
    destination_volume_ul: float | None = None,
    fault_phase: str | None = None,
    context: Mapping[str, Any] | None = None,
) -> str:
    """Return ``ordinary`` or ``dangerous`` for a TIP_CLOG / overpressure fault."""

    ctx = dict(context or {})
    if ctx.get("clog_class") in {ORDINARY, DANGEROUS}:
        return str(ctx["clog_class"])
    if str(ctx.get("tip_clog_class") or "").lower() in {ORDINARY, DANGEROUS}:
        return str(ctx.get("tip_clog_class")).lower()

    role = str(destination_role or ctx.get("destination_role") or "").strip().lower()
    interrupted = (
        dispense_interrupted
        if dispense_interrupted is not None
        else bool(ctx.get("dispense_interrupted"))
    )
    volume_unknown = (
        well_volume_unknown
        if well_volume_unknown is not None
        else bool(ctx.get("well_volume_unknown") or ctx.get("volume_unknown"))
    )
    dest_vol = destination_volume_ul
    if dest_vol is None and "destination_volume_ul" in ctx:
        try:
            dest_vol = float(ctx["destination_volume_ul"])
        except (TypeError, ValueError):
            dest_vol = None
    phase = str(fault_phase or ctx.get("fault_phase") or ctx.get("command_phase") or "").lower()

    if volume_unknown or interrupted:
        return DANGEROUS
    if role in _DANGEROUS_DEST_ROLES and (interrupted or volume_unknown or phase in {"dispense", "mid_dispense"}):
        return DANGEROUS
    if role in _DANGEROUS_DEST_ROLES and phase == "dispense":
        return DANGEROUS
    if "mid-dispense" in phase or "mid_dispense" in phase:
        return DANGEROUS
    if dest_vol is not None and dest_vol > 0 and role in _DANGEROUS_DEST_ROLES:
        return DANGEROUS

    if role in _ORDINARY_DEST_ROLES:
        return ORDINARY
    if phase in _ORDINARY_FAULT_PHASES:
        return ORDINARY
    if dest_vol == 0:
        return ORDINARY

    # Conservative default when context is ambiguous: treat as dangerous.
    if role in _DANGEROUS_DEST_ROLES:
        return DANGEROUS
    return ORDINARY if role or phase else DANGEROUS


def _tips_remaining(ctx: Mapping[str, Any]) -> int | None:
    raw = ctx.get("tips_remaining")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _dest_volume(ctx: Mapping[str, Any]) -> float | None:
    if "destination_volume_ul" not in ctx and "destination_received_volume_ul" not in ctx:
        return None
    raw = ctx.get("destination_volume_ul", ctx.get("destination_received_volume_ul"))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def ordinary_tip_swap_gate(
    context: Mapping[str, Any] | None = None,
    *,
    tip_swaps_already: int = 0,
) -> dict[str, Any]:
    """Gate for v4.1 ``ordinary_tip_swap_then_reeval`` (ALL conditions required).

    Returns ``allowed`` plus structured ``checks`` / ``block_reasons`` for harness + MCP.
    One tip-swap then re-eval; a second attempt or any failed check → not allowed (escalate).
    """

    ctx = dict(context or {})
    clog_class = classify_tip_clog(context=ctx)
    phase = str(ctx.get("fault_phase") or ctx.get("command_phase") or "").lower()
    role = str(ctx.get("destination_role") or "").strip().lower()
    dest_vol = _dest_volume(ctx)
    tips = _tips_remaining(ctx)
    tip_discardable = bool(
        ctx.get("tip_disposable")
        or ctx.get("tip_safely_discardable")
        or (ctx.get("tip_attached") and role in _ORDINARY_DEST_ROLES)
        or phase in _ORDINARY_FAULT_PHASES
    )
    source_identity_intact = not bool(
        ctx.get("source_identity_unknown")
        or ctx.get("identity_unknown")
        or ctx.get("contamination_unknown")
    )
    # Waste / aspirate-before-delivery: zero destination delivery required.
    zero_delivery = dest_vol == 0 or (
        role in _ORDINARY_DEST_ROLES and dest_vol is None and not ctx.get("well_volume_unknown")
    )
    phase_ok = phase in _ORDINARY_FAULT_PHASES or role in _ORDINARY_DEST_ROLES
    budget_ok = tips is not None and tips > 0
    one_swap_budget = tip_swaps_already < 1 and not bool(ctx.get("ordinary_tip_swap_exhausted"))

    checks = {
        "clog_class_ordinary": clog_class == ORDINARY,
        "phase_aspirate_or_waste": phase_ok,
        "destination_received_volume_zero": zero_delivery,
        "tip_safely_discardable": tip_discardable,
        "source_identity_intact": source_identity_intact,
        "tip_budget_ok": budget_ok,
        "one_tip_swap_then_reeval": one_swap_budget,
    }
    block_reasons = [name for name, ok in checks.items() if not ok]
    allowed = not block_reasons
    return {
        "allowed": allowed,
        "branch": ORDINARY_TIP_SWAP_BRANCH,
        "clog_class": clog_class,
        "checks": checks,
        "block_reasons": block_reasons,
        "tip_swaps_already": tip_swaps_already,
        "max_tip_swaps": 1,
        "on_fail": "escalate",
    }


def tip_clog_actionability(
    clog_class: str,
    *,
    context: Mapping[str, Any] | None = None,
    tip_swaps_already: int = 0,
) -> dict[str, Any]:
    """Map clog class to recovery actionability (mirrors MCP decision policy)."""

    if clog_class == ORDINARY:
        gate = ordinary_tip_swap_gate(context, tip_swaps_already=tip_swaps_already)
        return {
            "clog_class": ORDINARY,
            "actionability": "manual_confirmation_required",
            "auto_executable": False,
            "escalate_to_human": False,
            "hard_stop": False,
            "recommended_manual_action": "change_tip_then_retry_non_sample_path",
            "recommended_branch": ORDINARY_TIP_SWAP_BRANCH,
            "rationale": (
                "ordinary_tip_clog_executor_not_available"
                if gate["allowed"]
                else "ordinary_tip_clog_pre_sample_or_waste"
            ),
            "flex15_ref": "F09",
            "tip_swap_gate": gate,
        }
    return {
        "clog_class": DANGEROUS,
        "actionability": "manual_only",
        "auto_executable": False,
        "escalate_to_human": True,
        "hard_stop": True,
        "recommended_manual_action": "void_or_escalate_partial_volume_well",
        "rationale": "dangerous_tip_clog_mid_dispense_volume_unknown",
        "flex15_ref": "F10",
    }
