"""Combine SimPass + LogicPass into FinalPass_v2 (closed result algebra).

Outcomes: ``pass`` | ``fail`` | ``unevaluable``.
Only ``pass`` sets ``logic_pass=true``. Unevaluable/fail ⇒ ``final_pass_v2=false``.
No reviewer / judge score enters this gate.

Comparable path: :func:`evaluate_logicpass` requires an
:class:`AnalyzeAdapterResult` (or explicit missing-analyze). Caller-built
``commands`` / ``ledger`` alone cannot vacuous-pass the comparable gate.
Non-comparable unit helpers: :func:`evaluate_logicpass_noncomparable` and
:func:`evaluate_from_ledger`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .ledger import run_ledger
from .report import CoverageCounts, LogicIssue, issues_to_dicts
from .rules import (
    DynamicParamContext,
    RulesResult,
    build_coverage_counts,
    evaluate_rules,
)
from .types import (
    AnalyzeAdapterResult,
    AnalyzeProvenance,
    CommandDisposition,
    ExpectedCommand,
    LedgerRunState,
    LogicPassOutcome,
    PhysicalSetup,
)

CLOSED_LOGICPASS_OUTCOMES: frozenset[str] = frozenset({"pass", "fail", "unevaluable"})


class InvalidLogicPassOutcome(ValueError):
    """Raised when a value outside the closed ``pass|fail|unevaluable`` enum is used."""


@dataclass
class FinalPassV2Result:
    """Public LogicPass / FinalPass_v2 evaluation result."""

    sim_pass: bool
    outcome: LogicPassOutcome
    logic_pass: bool
    final_pass_v2: bool
    issues: list[LogicIssue] = field(default_factory=list)
    coverage: CoverageCounts = field(default_factory=CoverageCounts)
    ledger: LedgerRunState | None = None
    rules: RulesResult | None = None
    provenance: AnalyzeProvenance | None = None
    input_conflicts: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sim_pass": self.sim_pass,
            "outcome": self.outcome,
            "logic_pass": self.logic_pass,
            "final_pass_v2": self.final_pass_v2,
            "issues": issues_to_dicts(self.issues),
            "coverage": self.coverage.to_dict(),
            "input_conflicts": [
                c.__dict__ if hasattr(c, "__dict__") else c for c in self.input_conflicts
            ],
            "provenance": None
            if self.provenance is None
            else {
                "protocol_sha256": self.provenance.protocol_sha256,
                "package_sha256": self.provenance.package_sha256,
                "ot_version": self.provenance.ot_version,
                "api_level": self.provenance.api_level,
                "parameter_values": dict(self.provenance.parameter_values),
                "adapter_schema_version": self.provenance.adapter_schema_version,
                "command_status_summary": dict(self.provenance.command_status_summary),
                "analyze_source_path": self.provenance.analyze_source_path,
                "command_count": self.provenance.command_count,
                "analyze_wall_time": self.provenance.analyze_wall_time,
            },
        }


def combine_final_pass_v2(
    *,
    sim_pass: bool,
    outcome: LogicPassOutcome | str,
) -> tuple[bool, bool]:
    """Map closed outcome + SimPass → (logic_pass, final_pass_v2).

    Rejects any value outside ``pass`` | ``fail`` | ``unevaluable``.
    """

    if outcome not in CLOSED_LOGICPASS_OUTCOMES:
        raise InvalidLogicPassOutcome(
            f"Invalid LogicPass outcome {outcome!r}; "
            f"expected one of {sorted(CLOSED_LOGICPASS_OUTCOMES)}"
        )
    logic_pass = outcome == "pass"
    final_pass_v2 = bool(sim_pass) and logic_pass
    return logic_pass, final_pass_v2


def outcome_from_rules(rules: RulesResult) -> LogicPassOutcome:
    """Apply frozen result algebra to a ``RulesResult``."""

    if rules.terminal_unevaluable:
        return "unevaluable"
    if rules.input_conflict or rules.has_hard_domain_error:
        return "fail"
    return "pass"


def _first_lp_l5_disposition(
    dispositions: Sequence[CommandDisposition],
) -> CommandDisposition | None:
    for disposition in dispositions:
        if disposition.kind == "lp_l5":
            return disposition
    return None


def _result_from_rules(
    *,
    sim_pass: bool,
    rules: RulesResult,
    ledger: LedgerRunState,
    provenance: AnalyzeProvenance | None = None,
) -> FinalPassV2Result:
    outcome = outcome_from_rules(rules)
    logic_pass, final_pass_v2 = combine_final_pass_v2(
        sim_pass=sim_pass, outcome=outcome
    )
    return FinalPassV2Result(
        sim_pass=bool(sim_pass),
        outcome=outcome,
        logic_pass=logic_pass,
        final_pass_v2=final_pass_v2,
        issues=list(rules.issues),
        coverage=build_coverage_counts(rules.coverage),
        ledger=ledger,
        rules=rules,
        provenance=provenance,
        input_conflicts=list(ledger.input_conflicts),
    )


def evaluate_logicpass(
    *,
    sim_pass: bool,
    adapter: AnalyzeAdapterResult | None = None,
    ledger: LedgerRunState | None = None,
    commands: Iterable[ExpectedCommand] | None = None,
    physical_setup: PhysicalSetup | None = None,
    dynamic: DynamicParamContext | None = None,
    missing_analyze: bool = False,
) -> FinalPassV2Result:
    """Comparable LogicPass + FinalPass_v2 (requires Analyze provenance).

    Comparable gate path:

    * Requires an :class:`AnalyzeAdapterResult`, or explicit
      ``missing_analyze=True`` / missing adapter → LP-L5 ``unevaluable``.
    * Caller-supplied ``commands`` / ``ledger`` without an adapter **cannot**
      vacuous-pass; they are ignored and map to LP-L5.
    * ``adapter`` + caller ``ledger`` / ``commands`` is rejected — ledger is
      always derived from ``adapter.commands``.

    For unit tests that intentionally bypass Analyze provenance, use
    :func:`evaluate_logicpass_noncomparable` or :func:`evaluate_from_ledger`.
    """

    if adapter is not None and ledger is not None:
        raise ValueError(
            "evaluate_logicpass rejects caller-supplied ledger with adapter; "
            "ledger is always derived from adapter.commands"
        )
    if adapter is not None and commands is not None:
        raise ValueError(
            "evaluate_logicpass rejects caller-supplied commands with adapter; "
            "use adapter.commands only"
        )

    # Close Analyze-provenance bypass: no adapter ⇒ LP-L5, even if the caller
    # supplied a handcrafted command stream or ledger.
    if adapter is None:
        _ = missing_analyze  # explicit missing_analyze=True is the same branch
        empty = LedgerRunState()
        rules = evaluate_rules(
            empty,
            adapter_unevaluable=True,
            lp_l5_reasons=("missing_analyze_artifact",),
            lp_l5_locus="analyze_artifact",
            dynamic=dynamic,
        )
        return _result_from_rules(
            sim_pass=sim_pass, rules=rules, ledger=empty, provenance=None
        )

    provenance = adapter.provenance
    adapter_unevaluable = bool(adapter.unevaluable)
    lp_l5_reasons = tuple(adapter.lp_l5_reasons)
    if adapter_unevaluable and not lp_l5_reasons:
        lp_l5_reasons = ("adapter_unevaluable",)

    lp_l5_step_index: int | None = None
    lp_l5_command_id: str | None = None
    lp_l5_command_type: str | None = None
    lp_l5_locus = "analyze"
    first_l5 = _first_lp_l5_disposition(adapter.dispositions)
    if first_l5 is not None:
        if first_l5.index >= 0:
            lp_l5_step_index = first_l5.index
        lp_l5_command_id = first_l5.command_id
        lp_l5_command_type = first_l5.command_type
        if first_l5.reason == "missing_analyze_artifact":
            lp_l5_locus = "analyze_artifact"

    if adapter_unevaluable:
        # Fail-closed: do not vacuous-pass on an incomplete trace.
        built_ledger = LedgerRunState()
    else:
        built_ledger = run_ledger(adapter.commands, physical_setup)

    rules = evaluate_rules(
        built_ledger,
        adapter_unevaluable=adapter_unevaluable,
        lp_l5_reasons=lp_l5_reasons,
        lp_l5_locus=lp_l5_locus,
        lp_l5_step_index=lp_l5_step_index,
        lp_l5_command_id=lp_l5_command_id,
        lp_l5_command_type=lp_l5_command_type,
        dynamic=dynamic,
    )
    return _result_from_rules(
        sim_pass=sim_pass,
        rules=rules,
        ledger=built_ledger,
        provenance=provenance,
    )


def evaluate_logicpass_noncomparable(
    *,
    sim_pass: bool,
    ledger: LedgerRunState | None = None,
    commands: Iterable[ExpectedCommand] | None = None,
    physical_setup: PhysicalSetup | None = None,
    dynamic: DynamicParamContext | None = None,
    adapter_unevaluable: bool = False,
    lp_l5_reasons: Sequence[str] = (),
    lp_l5_locus: str = "analyze",
    lp_l5_step_index: int | None = None,
    lp_l5_command_id: str | None = None,
    lp_l5_command_type: str | None = None,
) -> FinalPassV2Result:
    """Non-comparable helper for unit tests (no Analyze provenance required).

    Builds / accepts a ledger from caller commands. Results from this helper
    are **not** comparable FinalPass_v2 scores — use :func:`evaluate_logicpass`
    with an Analyze adapter for the frozen comparable gate.
    """

    if ledger is None:
        if commands is None:
            raise ValueError(
                "evaluate_logicpass_noncomparable requires ledger or commands"
            )
        ledger = run_ledger(commands, physical_setup)

    rules = evaluate_rules(
        ledger,
        adapter_unevaluable=adapter_unevaluable,
        lp_l5_reasons=lp_l5_reasons,
        lp_l5_locus=lp_l5_locus,
        lp_l5_step_index=lp_l5_step_index,
        lp_l5_command_id=lp_l5_command_id,
        lp_l5_command_type=lp_l5_command_type,
        dynamic=dynamic,
    )
    return _result_from_rules(
        sim_pass=sim_pass, rules=rules, ledger=ledger, provenance=None
    )


def evaluate_from_ledger(
    *,
    sim_pass: bool,
    ledger: LedgerRunState,
    adapter_unevaluable: bool = False,
    lp_l5_reasons: Sequence[str] = (),
    dynamic: DynamicParamContext | None = None,
) -> FinalPassV2Result:
    """Non-comparable convenience for unit tests that already built a ledger."""

    return evaluate_logicpass_noncomparable(
        sim_pass=sim_pass,
        ledger=ledger,
        adapter_unevaluable=adapter_unevaluable,
        lp_l5_reasons=lp_l5_reasons,
        dynamic=dynamic,
    )


__all__ = [
    "CLOSED_LOGICPASS_OUTCOMES",
    "FinalPassV2Result",
    "InvalidLogicPassOutcome",
    "combine_final_pass_v2",
    "evaluate_from_ledger",
    "evaluate_logicpass",
    "evaluate_logicpass_noncomparable",
    "outcome_from_rules",
]
