"""LogicPass Phase-1 package — public API for FinalPass_v2.

Comparable gate::

    FinalPass_v2 = SimPass ∧ LogicPass

Closed LogicPass outcomes: ``pass`` | ``fail`` | ``unevaluable``.
Only ``pass`` sets ``logic_pass=true``; unevaluable/fail force
``final_pass_v2=false``. Reviewer/judge scores never enter this gate.
"""

from __future__ import annotations

from labscriptai.benchmark.logicpass.analyze_adapter import (
    ADAPTER_SCHEMA_VERSION,
    load_analyze_json,
)
from labscriptai.benchmark.logicpass.evaluate import (
    CLOSED_LOGICPASS_OUTCOMES,
    FinalPassV2Result,
    InvalidLogicPassOutcome,
    combine_final_pass_v2,
    evaluate_from_ledger,
    evaluate_logicpass,
    evaluate_logicpass_noncomparable,
    outcome_from_rules,
)
from labscriptai.benchmark.logicpass.ledger import StateLedger, run_ledger
from labscriptai.benchmark.logicpass.report import CoverageCounts, LogicIssue
from labscriptai.benchmark.logicpass.rules import (
    RULES_SCHEMA_VERSION,
    DynamicParamContext,
    RuleCoverage,
    RulesResult,
    build_dynamic_param_context,
    evaluate_rules,
)
from labscriptai.benchmark.logicpass.types import (
    ALLOWLIST_REVISION,
    PHYSICAL_SETUP_SCHEMA_VERSION,
    AnalyzeAdapterResult,
    AnalyzeProvenance,
    CommandDisposition,
    ExpectedCommand,
    InitialVolumeSpec,
    InputConflict,
    LedgerRunState,
    LedgerStepEvent,
    LogicPassOutcome,
    NormalizedCommand,
    NormalizedLeafCommand,
    PhysicalSetup,
    ReagentBudget,
    TipState,
    WellState,
    assumed_physical_setup_from_protocol,
    well_key,
)

# Alias matching the paper formula spelling.
FinalPass_v2 = combine_final_pass_v2


def final_pass_v2(*, sim_pass: bool, logic_pass: bool) -> bool:
    """Compose ``FinalPass_v2 = SimPass ∧ LogicPass`` (bool form)."""

    return bool(sim_pass) and bool(logic_pass)


__all__ = [
    # Adapter
    "ADAPTER_SCHEMA_VERSION",
    "ALLOWLIST_REVISION",
    "PHYSICAL_SETUP_SCHEMA_VERSION",
    "AnalyzeAdapterResult",
    "AnalyzeProvenance",
    "CommandDisposition",
    "load_analyze_json",
    # Ledger
    "ExpectedCommand",
    "InitialVolumeSpec",
    "InputConflict",
    "LedgerRunState",
    "LedgerStepEvent",
    "NormalizedCommand",
    "NormalizedLeafCommand",
    "PhysicalSetup",
    "ReagentBudget",
    "StateLedger",
    "TipState",
    "WellState",
    "assumed_physical_setup_from_protocol",
    "run_ledger",
    "well_key",
    # Rules / report
    "RULES_SCHEMA_VERSION",
    "CoverageCounts",
    "DynamicParamContext",
    "LogicIssue",
    "RuleCoverage",
    "RulesResult",
    "build_dynamic_param_context",
    "evaluate_rules",
    # Evaluate / FinalPass_v2
    "CLOSED_LOGICPASS_OUTCOMES",
    "FinalPassV2Result",
    "FinalPass_v2",
    "InvalidLogicPassOutcome",
    "LogicPassOutcome",
    "combine_final_pass_v2",
    "evaluate_from_ledger",
    "evaluate_logicpass",
    "evaluate_logicpass_noncomparable",
    "final_pass_v2",
    "outcome_from_rules",
]
