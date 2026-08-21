"""LP-L1–L6 rule evaluation over ledger step events.

Binary contributions follow the preserved
``Opentrons-Lab-Agent-materials/docs/research/logicpass/02_phase0_rules_v0.json``.
Phase-2 hardening notes:
``Opentrons-Lab-Agent-materials/docs/research/logicpass/14_PHASE2_HARDENING.md``.
Contamination roles come only from evaluator ``well_roles`` (no name regex).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

from .report import (
    CoverageCounts,
    LogicIssue,
    format_l1_detail,
    format_l2_detail,
    format_l3_detail,
    format_l4_detail,
    format_l5_detail,
    format_l6_detail,
)
from .types import LedgerRunState, well_key

# Phase-2 rule-engine freeze (Phase-0 JSON remains the semantic base).
RULES_SCHEMA_VERSION = "logicpass.phase2_rules.v1"

RuleOutcome = Literal[
    "pass",
    "fail",
    "skip",
    "report",
    "deferred",
    "unevaluable",
]


@dataclass(frozen=True)
class DynamicParamContext:
    """Evaluator-owned evidence for LP-L6 (executable-only; prose ignored).

    Defer vs include (Phase-2 freeze):

    * Default / ``deferred=True`` → excluded from the composite (coverage
      ``deferred``; never a domain hard error).
    * ``is_dynamic_task=False`` → not applicable (skip ``not_dynamic_task``).
    * Included only when ``is_dynamic_task=True`` and ``deferred=False``.
      Then hard-fail unless executable declaration/access evidence is present
      **and** ≥2 frozen Analyze ``parameter_values`` maps demonstrate wiring.
      Setup-card / manifest prose cannot satisfy or rescue.
    """

    is_dynamic_task: bool = False
    deferred: bool = True
    terms: tuple[str, ...] = ()
    executable_param_declared: bool = False
    frozen_analyze_values: tuple[Mapping[str, Any], ...] = ()

    @classmethod
    def deferred_excluded(cls) -> DynamicParamContext:
        """Explicit deferral — LP-L6 out of the composite."""

        return cls(is_dynamic_task=False, deferred=True)

    @classmethod
    def from_analyze_parameter_values(
        cls,
        parameter_value_maps: Sequence[Mapping[str, Any]],
        *,
        terms: Sequence[str] = (),
        executable_param_declared: bool = True,
    ) -> DynamicParamContext:
        """Include LP-L6 using ≥2 frozen Analyze ``parameter_values`` maps."""

        frozen = tuple(dict(m) for m in parameter_value_maps)
        resolved_terms = tuple(terms) if terms else tuple(
            sorted({str(k) for m in frozen for k in m})
        )
        return cls(
            is_dynamic_task=True,
            deferred=False,
            terms=resolved_terms or ("<dynamic>",),
            executable_param_declared=executable_param_declared,
            frozen_analyze_values=frozen,
        )


def build_dynamic_param_context(
    *,
    is_dynamic_task: bool,
    include_in_composite: bool,
    terms: Sequence[str] = (),
    executable_param_declared: bool = False,
    frozen_analyze_values: Sequence[Mapping[str, Any]] = (),
) -> DynamicParamContext:
    """Build LP-L6 context with an explicit defer-vs-include switch.

    ``include_in_composite=False`` always defers (excluded). When True and
    ``is_dynamic_task``, the rule evaluates to pass or hard-fail.
    """

    return DynamicParamContext(
        is_dynamic_task=is_dynamic_task,
        deferred=not include_in_composite,
        terms=tuple(terms),
        executable_param_declared=executable_param_declared,
        frozen_analyze_values=tuple(dict(v) for v in frozen_analyze_values),
    )


@dataclass
class RuleCoverage:
    code: str
    applicable: bool
    evaluated: bool
    skipped_reason: str | None = None
    outcome: RuleOutcome | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "applicable": self.applicable,
            "evaluated": self.evaluated,
            "skipped_reason": self.skipped_reason,
            "outcome": self.outcome,
        }


@dataclass
class RulesResult:
    """Domain + terminal rule findings before FinalPass algebra."""

    issues: list[LogicIssue] = field(default_factory=list)
    coverage: list[RuleCoverage] = field(default_factory=list)
    hard_error_codes: list[str] = field(default_factory=list)
    terminal_unevaluable: bool = False
    input_conflict: bool = False

    @property
    def has_hard_domain_error(self) -> bool:
        return bool(self.hard_error_codes)


def evaluate_rules(
    ledger: LedgerRunState,
    *,
    adapter_unevaluable: bool = False,
    lp_l5_reasons: Sequence[str] = (),
    lp_l5_locus: str = "analyze",
    lp_l5_step_index: int | None = None,
    lp_l5_command_id: str | None = None,
    lp_l5_command_type: str | None = None,
    dynamic: DynamicParamContext | None = None,
) -> RulesResult:
    """Evaluate LP-L1–L6 against a completed ledger snapshot.

    LP-L5 / input conflicts are recorded here; FinalPass algebra lives in
    ``evaluate.py``.
    """

    result = RulesResult()
    dynamic = dynamic or DynamicParamContext()

    _eval_l5(
        result,
        adapter_unevaluable=adapter_unevaluable,
        reasons=lp_l5_reasons,
        locus=lp_l5_locus,
        step_index=lp_l5_step_index,
        command_id=lp_l5_command_id,
        command_type=lp_l5_command_type,
    )
    _eval_input_conflicts(result, ledger)

    # Domain rules still run for diagnostics even after terminal gates.
    _eval_l1(result, ledger)
    _eval_l2(result, ledger)
    _eval_l3(result, ledger)
    _eval_l4(result, ledger)
    _eval_l6(result, dynamic)

    return result


def build_coverage_counts(coverage: Sequence[RuleCoverage]) -> CoverageCounts:
    skip_counts: dict[str, int] = {}
    evaluable = 0
    per_rule: list[dict[str, Any]] = []
    for row in coverage:
        per_rule.append(row.to_dict())
        if row.applicable and row.evaluated:
            evaluable += 1
        if row.skipped_reason:
            skip_counts[row.skipped_reason] = skip_counts.get(row.skipped_reason, 0) + 1
    return CoverageCounts(
        evaluable_denominator=evaluable,
        skip_counts=skip_counts,
        per_rule=per_rule,
    )


def _record_coverage(result: RulesResult, coverage: RuleCoverage) -> None:
    result.coverage.append(coverage)


def _add_hard(result: RulesResult, code: str) -> None:
    if code not in result.hard_error_codes:
        result.hard_error_codes.append(code)


def _eval_l5(
    result: RulesResult,
    *,
    adapter_unevaluable: bool,
    reasons: Sequence[str],
    locus: str,
    step_index: int | None = None,
    command_id: str | None = None,
    command_type: str | None = None,
) -> None:
    if not adapter_unevaluable and not reasons:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L5",
                applicable=True,
                evaluated=True,
                outcome="pass",
            ),
        )
        return

    reason = "; ".join(reasons) if reasons else "trace_incomplete"
    issue = LogicIssue(
        code="LP-L5",
        step_index=step_index,
        well=None,
        detail_text=format_l5_detail(
            locus=locus,
            reason=reason,
            step_index=step_index,
            command_id=command_id,
            command_type=command_type,
        ),
        severity="terminal",
        command_id=command_id,
        provenance="analyze_adapter",
    )
    result.issues.append(issue)
    result.terminal_unevaluable = True
    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L5",
            applicable=True,
            evaluated=True,
            outcome="unevaluable",
        ),
    )


def _eval_input_conflicts(result: RulesResult, ledger: LedgerRunState) -> None:
    if not ledger.input_conflicts:
        return
    result.input_conflict = True
    for conflict in ledger.input_conflicts:
        well = None
        if conflict.labware_id and conflict.well_name:
            well = well_key(conflict.labware_id, conflict.well_name)
        result.issues.append(
            LogicIssue(
                code=conflict.code or "LP-INPUT-CONFLICT",
                step_index=None,
                well=well,
                detail_text=conflict.detail_text
                or "Authoritative input conflict (LP-INPUT-CONFLICT).",
                severity="error",
                labware=conflict.labware_id,
                provenance="evaluator_physical_setup",
            )
        )


def _eval_l1(result: RulesResult, ledger: LedgerRunState) -> None:
    aspirates = [e for e in ledger.events if e.command_type == "aspirate"]
    if not aspirates:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L1",
                applicable=False,
                evaluated=False,
                skipped_reason="no_aspirate_commands",
                outcome="skip",
            ),
        )
        return

    known = [e for e in aspirates if not e.volume_unknown]
    unknown = [e for e in aspirates if e.volume_unknown]
    if not known:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L1",
                applicable=True,
                evaluated=False,
                skipped_reason="unknown_source_volume",
                outcome="skip",
            ),
        )
        return

    failed = False
    residual_skipped = False
    for event in known:
        assert event.volume_ul is not None
        assert event.labware_id is not None and event.well_name is not None
        current = event.well_current_ul
        if current is None:
            continue
        requested = float(event.volume_ul)
        dead = event.well_dead_ul
        kinds: list[str] = []
        if requested > current:
            kinds.append("empty" if current <= 0 else "partial_insufficient")
        if dead is None:
            residual_skipped = True
        elif (current - requested) < dead:
            kinds.append("dead_volume")
        for kind in kinds:
            failed = True
            result.issues.append(
                LogicIssue(
                    code="LP-L1",
                    step_index=event.step_index,
                    well=well_key(event.labware_id, event.well_name),
                    detail_text=format_l1_detail(
                        step_index=event.step_index,
                        requested_ul=requested,
                        labware=event.labware_id,
                        well=event.well_name,
                        current_ul=current,
                        dead_ul=dead,
                        kind=kind,
                    ),
                    severity="error",
                    labware=event.labware_id,
                    command_id=event.command_id,
                    provenance="ledger",
                )
            )
            _add_hard(result, "LP-L1")

    skipped_reason = None
    if unknown:
        skipped_reason = "unknown_source_volume_partial"
    elif residual_skipped and not failed:
        skipped_reason = "dead_volume_unknown_residual_skipped"

    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L1",
            applicable=True,
            evaluated=True,
            skipped_reason=skipped_reason,
            outcome="fail" if failed else "pass",
        ),
    )


def _eval_l2(result: RulesResult, ledger: LedgerRunState) -> None:
    """LP-L2: same-trace report-only; hard only vs immutable evaluator demands.

    Phase-2 freeze:

    * No ``PhysicalSetup.reagent_demands`` / ``independent_demand_ul`` →
      aggregate path consumption by stable reagent ID as ``severity=report``
      (summary of LP-L1; never enters ``hard_error_codes``).
    * Evaluator-owned immutable ``reagent_demands`` present → hard-fail when
      ``consumed_volume_ul > independent_demand_ul`` (budget mismatch).
      Within-budget reagents contribute a clean pass for that ID (no report
      noise). Candidate package / manifest declarations cannot invent demands.
    """

    reagents = {
        rid: reagent
        for rid, reagent in ledger.reagents.items()
        if rid and reagent.consumed_volume_ul > 0
    }
    # Include reagents with evaluator-owned independent demand even if unused.
    for rid, reagent in ledger.reagents.items():
        if reagent.independent_demand_ul is not None and rid:
            reagents[rid] = reagent

    if not reagents and not any(
        e.command_type == "aspirate" for e in ledger.events
    ):
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L2",
                applicable=False,
                evaluated=False,
                skipped_reason="no_reagent_consumption",
                outcome="skip",
            ),
        )
        return

    if not reagents:
        # Aspirates happened but no reagent IDs — same-trace report N/A.
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L2",
                applicable=True,
                evaluated=False,
                skipped_reason="no_stable_reagent_id",
                outcome="skip",
            ),
        )
        return

    hard_fail = False
    emitted_report = False
    saw_independent_demand = False
    for reagent_id, reagent in reagents.items():
        demand = reagent.independent_demand_ul
        if demand is None:
            # Same-trace aggregation is report-only (not an independent catch).
            result.issues.append(
                LogicIssue(
                    code="LP-L2",
                    step_index=None,
                    well=reagent.source_wells[0] if reagent.source_wells else None,
                    detail_text=format_l2_detail(
                        reagent_id=str(reagent_id),
                        consumed_ul=reagent.consumed_volume_ul,
                        demand_ul=None,
                        remaining_ul=reagent.remaining_volume_ul,
                        mode="report",
                    ),
                    severity="report",
                    provenance="same_trace",
                )
            )
            emitted_report = True
            continue

        saw_independent_demand = True
        demand_ul = float(demand)
        if reagent.consumed_volume_ul > demand_ul:
            hard_fail = True
            _add_hard(result, "LP-L2")
            result.issues.append(
                LogicIssue(
                    code="LP-L2",
                    step_index=None,
                    well=reagent.source_wells[0] if reagent.source_wells else None,
                    detail_text=format_l2_detail(
                        reagent_id=str(reagent_id),
                        consumed_ul=reagent.consumed_volume_ul,
                        demand_ul=demand_ul,
                        remaining_ul=reagent.remaining_volume_ul,
                        mode="hard",
                    ),
                    severity="error",
                    provenance="evaluator_reagent_demand",
                    hint="Budget mismatch vs immutable evaluator reagent_demands.",
                )
            )

    if hard_fail:
        outcome: RuleOutcome = "fail"
    elif emitted_report and not saw_independent_demand:
        outcome = "report"
    elif saw_independent_demand:
        # Evaluator demands present and all within budget.
        outcome = "pass"
    else:
        outcome = "pass"

    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L2",
            applicable=True,
            evaluated=True,
            skipped_reason=None,
            outcome=outcome,
        ),
    )


def _eval_l3(result: RulesResult, ledger: LedgerRunState) -> None:
    # Applicability: evaluator labeled at least one dirty and one protected well,
    # or the trace actually marked a protected-while-dirty aspirate.
    roles = {w.well_role for w in ledger.wells.values() if w.well_role}
    events = [
        e
        for e in ledger.events
        if e.command_type == "aspirate" and e.aspirate_from_protected_while_dirty
    ]
    has_role_pair = (
        "dirty_source" in roles and "protected_shared_source" in roles
    )
    if not has_role_pair and not events:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L3",
                applicable=False,
                evaluated=False,
                skipped_reason="no_evaluator_contamination_roles",
                outcome="skip",
            ),
        )
        return

    failed = False
    for event in events:
        assert event.labware_id is not None and event.well_name is not None
        protected = well_key(event.labware_id, event.well_name)
        dirty_well = event.tip_dirty_from or "unknown"
        pipette = event.pipette_id or "unknown"
        failed = True
        result.issues.append(
            LogicIssue(
                code="LP-L3",
                step_index=event.step_index,
                well=protected,
                detail_text=format_l3_detail(
                    step_index=event.step_index,
                    pipette_id=pipette,
                    dirty_well=dirty_well,
                    protected_well=protected,
                ),
                severity="error",
                labware=event.labware_id,
                command_id=event.command_id,
                provenance="evaluator_well_roles",
                hint="Replace tip after dirty_source aspirate before protected_shared_source.",
            )
        )
        _add_hard(result, "LP-L3")

    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L3",
            applicable=True,
            evaluated=True,
            skipped_reason=None,
            outcome="fail" if failed else "pass",
        ),
    )


def _eval_l4(result: RulesResult, ledger: LedgerRunState) -> None:
    dispenses = [e for e in ledger.events if e.command_type == "dispense"]
    if not dispenses:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L4",
                applicable=False,
                evaluated=False,
                skipped_reason="no_dispense_commands",
                outcome="skip",
            ),
        )
        return

    evaluable = [
        e
        for e in dispenses
        if not e.volume_unknown
        and e.well_projected_ul is not None
        and e.well_max_ul is not None
    ]
    if not evaluable:
        reason = (
            "destination_volume_unknown"
            if any(e.volume_unknown for e in dispenses)
            else "capacity_unknown"
        )
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L4",
                applicable=True,
                evaluated=False,
                skipped_reason=reason,
                outcome="skip",
            ),
        )
        return

    failed = False
    for event in evaluable:
        assert event.volume_ul is not None
        assert event.labware_id is not None and event.well_name is not None
        assert event.well_projected_ul is not None and event.well_max_ul is not None
        if event.well_projected_ul > event.well_max_ul:
            failed = True
            result.issues.append(
                LogicIssue(
                    code="LP-L4",
                    step_index=event.step_index,
                    well=well_key(event.labware_id, event.well_name),
                    detail_text=format_l4_detail(
                        step_index=event.step_index,
                        add_ul=float(event.volume_ul),
                        labware=event.labware_id,
                        well=event.well_name,
                        projected_ul=float(event.well_projected_ul),
                        max_ul=float(event.well_max_ul),
                    ),
                    severity="error",
                    labware=event.labware_id,
                    command_id=event.command_id,
                    provenance="ledger",
                )
            )
            _add_hard(result, "LP-L4")

    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L4",
            applicable=True,
            evaluated=True,
            skipped_reason=None,
            outcome="fail" if failed else "pass",
        ),
    )


def _eval_l6(result: RulesResult, dynamic: DynamicParamContext) -> None:
    """LP-L6: defer vs executable fail/pass (Phase-2 freeze).

    * Deferred / excluded → coverage ``deferred``, skip ``deferred``.
    * Not a dynamic task → skip ``not_dynamic_task``.
    * Included dynamic tasks → hard-fail unless executable declaration/access
      evidence **and** ≥2 distinct frozen Analyze ``parameter_values`` maps
      demonstrate wiring. Prose cannot satisfy.
    """

    if dynamic.deferred:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L6",
                applicable=False,
                evaluated=False,
                skipped_reason="deferred",
                outcome="deferred",
            ),
        )
        return

    if not dynamic.is_dynamic_task:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L6",
                applicable=False,
                evaluated=False,
                skipped_reason="not_dynamic_task",
                outcome="skip",
            ),
        )
        return

    terms = dynamic.terms or ("<dynamic>",)
    values = dynamic.frozen_analyze_values
    v1 = values[0] if len(values) >= 1 else None
    v2 = values[1] if len(values) >= 2 else None
    wired = (
        dynamic.executable_param_declared
        and len(values) >= 2
        and _values_demonstrate_wiring(values)
    )
    if wired:
        _record_coverage(
            result,
            RuleCoverage(
                code="LP-L6",
                applicable=True,
                evaluated=True,
                outcome="pass",
            ),
        )
        return

    fail_reason = _l6_fail_reason(dynamic)
    for term in terms:
        result.issues.append(
            LogicIssue(
                code="LP-L6",
                step_index=None,
                well=None,
                detail_text=format_l6_detail(term=term, v1=v1, v2=v2),
                severity="error",
                provenance="executable_params",
                hint=(
                    f"{fail_reason}; prose/setup_card/manifest text cannot "
                    "satisfy LP-L6."
                ),
            )
        )
    _add_hard(result, "LP-L6")
    _record_coverage(
        result,
        RuleCoverage(
            code="LP-L6",
            applicable=True,
            evaluated=True,
            skipped_reason=fail_reason,
            outcome="fail",
        ),
    )


def _l6_fail_reason(dynamic: DynamicParamContext) -> str:
    values = dynamic.frozen_analyze_values
    if not dynamic.executable_param_declared:
        return "missing_executable_param_declaration"
    if len(values) < 2:
        return "need_two_frozen_analyze_parameter_values"
    if not _values_demonstrate_wiring(values):
        return "frozen_analyze_values_not_wired"
    return "executable_evidence_incomplete"


def _values_demonstrate_wiring(values: Sequence[Mapping[str, Any]]) -> bool:
    """Require ≥2 frozen Analyze maps that differ (wiring, not prose)."""

    if len(values) < 2:
        return False
    first = dict(values[0])
    second = dict(values[1])
    # Identical empties or identical non-empty maps do not demonstrate wiring.
    if first == second:
        return False
    # At least one map must carry a concrete parameter key/value.
    return bool(first) or bool(second)


__all__ = [
    "RULES_SCHEMA_VERSION",
    "DynamicParamContext",
    "RuleCoverage",
    "RuleOutcome",
    "RulesResult",
    "build_coverage_counts",
    "build_dynamic_param_context",
    "evaluate_rules",
]
