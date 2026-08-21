"""Shared LogicPass Phase-1 types (adapter ↔ ledger ↔ rules).

Adapter schema: ``logicpass.analyze_adapter.v2`` (blowout state-holding
semantics; see ``docs/research/logicpass/29_LOGICPASS_P0_P3_RESULTS.md``).

This module owns:

* **Command-stream contract** — :class:`ExpectedCommand`,
  :class:`NormalizedLeafCommand` / :class:`NormalizedCommand`,
  analyze dispositions + provenance.
* **Ledger state shapes** — Well / Tip / Reagent + step events (consumed by
  ``ledger.py``; rule verdicts stay in ``rules.py`` / ``evaluate.py``).

Disposition (every analyze ``commands[]`` entry, exactly one)::

    consumed_supported_atomic_leaf
        | explicitly_allowlisted_non_state
        | lp_l5

``lp_l5`` forces LogicPass ``outcome=unevaluable`` (≠ pass).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Protocol, runtime_checkable

# v2 = blowout* is recorded as a zero-transfer, state-holding action. This
# deliberately follows the P0 evaluation policy and is not a claim about the
# physical residual volume expelled by a real pipette.
ADAPTER_SCHEMA_VERSION = "logicpass.analyze_adapter.v2"
ALLOWLIST_REVISION = "phase3_modules_touchtip_v2_blowout_mix_state_holding"
PHYSICAL_SETUP_SCHEMA_VERSION = "logicpass.physical_setup.v0_audited"
SetupBasis = Literal["assumed", "evaluator"]
OT_VERSION_PROBE_BASELINE = "8.8.1"

LogicPassOutcome = Literal["pass", "fail", "unevaluable"]
WellRole = Literal["dirty_source", "protected_shared_source", "neutral"]
TrackingState = Literal["known", "unknown"]
VolumeProvenance = Literal[
    "evaluator_physical_setup",
    "protocol_declared",
    "conflict",
]

CommandDispositionKind = Literal[
    "consumed_supported_atomic_leaf",
    "explicitly_allowlisted_non_state",
    "lp_l5",
]

SupportedLeafCommandType = Literal[
    "loadLiquid",
    "pickUpTip",
    "dropTip",
    "dropTipInPlace",
    "aspirate",
    "dispense",
]

SUPPORTED_LEAF_COMMANDS: frozenset[str] = frozenset(
    {
        "loadLiquid",
        "pickUpTip",
        "dropTip",
        "dropTipInPlace",
        "aspirate",
        "dispense",
    }
)

# Non-state allowlist (Phase-0 base + Phase-3 expansion, v1 semantics).
# These commands are skipped for ledger stepping (not silent physical pass).
# Still fail-closed on missing / non-succeeded status.
#
# Blowout has a separate, auditable state-holding policy below. ``touchTip``
# stays allowlisted because it has no volume transfer in the L1/L4 model.
#
# Conservative exclusions that remain LP-L5: transfer/consolidate/distribute,
# aspirateInPlace/dispenseInPlace, liquidProbe, moveLabware, setTipState,
# custom. ``mix`` is *not* a compound parent here — same zero-net-volume
# family as blowout (PE 8.8.1 expands ``pipette.mix`` to aspirate/dispense).
# Note: ``moveLabware`` is *not* allowlisted → disposition ``lp_l5``.
ALLOWLISTED_NON_STATE_COMMANDS: frozenset[str] = frozenset(
    {
        # Phase-0 freeze base
        "loadLabware",
        "loadPipette",
        "loadModule",
        "loadLid",
        "loadLidStack",
        "home",
        "moveToWell",
        "moveToAddressableArea",
        "moveToAddressableAreaForDropTip",
        "waitForDuration",
        "waitForResume",
        "comment",
        "setRailLights",
        "setStatusBar",
        # Phase-3: PE pipette helper with no L1/L4 volume effect modeled
        "touchTip",
        # Phase-3: common module ops (no well/tip liquid ledger mutation)
        "temperatureModule/setTargetTemperature",
        "temperatureModule/waitForTemperature",
        "temperatureModule/deactivate",
        "magneticModule/engage",
        "magneticModule/disengage",
        "heaterShaker/closeLabwareLatch",
        "heaterShaker/openLabwareLatch",
        "heaterShaker/setAndWaitForShakeSpeed",
        "heaterShaker/deactivateShaker",
        "heaterShaker/setTargetTemperature",
        "heaterShaker/waitForTemperature",
        "heaterShaker/deactivateHeater",
        "thermocycler/openLid",
        "thermocycler/closeLid",
    }
)

BLOWOUT_STATE_HOLDING_COMMANDS: frozenset[str] = frozenset(
    {"blowout", "blowOut", "blowOutInPlace"}
)

# Mix is admitted like blowout: zero net well volume, not a compound parent
# and not a no-contact helper (unlike touchTip). A leftover ``mix``
# commandType cannot LP-L5 the whole exam. PE 8.8.1 typically expands
# ``pipette.mix(...)`` to aspirate/dispense leaves instead of emitting this.
MIX_STATE_HOLDING_COMMANDS: frozenset[str] = frozenset({"mix"})

STATE_HOLDING_ZERO_TRANSFER_COMMANDS: frozenset[str] = (
    BLOWOUT_STATE_HOLDING_COMMANDS | MIX_STATE_HOLDING_COMMANDS
)

LEGACY_CUSTOM_STATE_HOLDING_TYPES: frozenset[str] = frozenset(
    {"command.DELAY", "command.TOUCH_TIP"}
)

PARENT_OR_COMPOUND_COMMANDS: frozenset[str] = frozenset(
    {
        "transfer",
        "consolidate",
        "distribute",
    }
)

UNSUPPORTED_LIQUID_AFFECTING_EXAMPLES: frozenset[str] = frozenset(
    {
        "aspirateInPlace",
        "dispenseInPlace",
        "configureForVolume",
        "liquidProbe",
        "moveLabware",
        "setTipState",
        "custom",
        *PARENT_OR_COMPOUND_COMMANDS,
    }
)


def well_key(labware_id: str, well_name: str) -> str:
    """Stable well identity used across ledger + rules."""
    return f"{labware_id}:{well_name}"


def _ast_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _ast_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        return node.value
    return None


def _ast_finite_number(node: ast.AST | None) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            return None
        number = float(node.value)
        if number != number:
            return None
        return number
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _ast_finite_number(node.operand)
        return None if inner is None else -inner
    return None


def _call_kw(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _subscript_well(node: ast.AST | None) -> tuple[str, str] | None:
    if not isinstance(node, ast.Subscript):
        return None
    labware = _ast_name(node.value)
    well = _ast_str(node.slice)
    if labware and well:
        return labware, well
    return None


def assumed_physical_setup_from_protocol(
    source: str,
) -> tuple[PhysicalSetup, dict[str, Any]]:
    """Read ``load_liquid`` volumes from protocol source. No volume invention.

    Returns ``(PhysicalSetup, meta)`` with ``setup_basis=assumed``. Wells whose
    ``load_liquid`` call has no numeric ``volume`` are left unknown so LP-L1
    skips (``volume_rules=skipped``).
    """

    declared: dict[str, float] = {}
    skipped_no_volume: list[str] = []
    parse_error: str | None = None
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        parse_error = str(exc)
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != "load_liquid":
                continue
            volume = _ast_finite_number(_call_kw(node, "volume"))
            keys: list[str] = []
            receiver_well = _subscript_well(func.value)
            if receiver_well is not None:
                keys.append(well_key(*receiver_well))
            location_well = _subscript_well(_call_kw(node, "location"))
            if location_well is not None:
                keys.append(well_key(*location_well))
            wells_node = _call_kw(node, "wells")
            labware_name = _ast_name(func.value)
            if isinstance(wells_node, (ast.List, ast.Tuple)) and labware_name:
                for elt in wells_node.elts:
                    well = _ast_str(elt)
                    if well:
                        keys.append(well_key(labware_name, well))
            keys = list(dict.fromkeys(keys))
            if volume is None:
                skipped_no_volume.extend(keys or ["<unresolved>"])
                continue
            for key in keys:
                declared[key] = volume

    setup = PhysicalSetup(initial_volumes=dict(declared), setup_basis="assumed")
    meta = {
        "setup_basis": "assumed",
        "declared_wells": dict(declared),
        "skipped_no_volume": list(skipped_no_volume),
        "parse_error": parse_error,
        "volume_rules": "skipped" if not declared else "assumed",
    }
    return setup, meta


@runtime_checkable
class ExpectedCommand(Protocol):
    """Minimal normalized leaf shape the ledger steps over.

    Implemented by :class:`NormalizedLeafCommand` and :class:`NormalizedCommand`.
    """

    @property
    def step_index(self) -> int: ...

    @property
    def command_id(self) -> str: ...

    @property
    def command_type(self) -> str: ...

    @property
    def pipette_id(self) -> str | None: ...

    @property
    def labware_id(self) -> str | None: ...

    @property
    def well_name(self) -> str | None: ...

    @property
    def volume_ul(self) -> float | None: ...

    @property
    def liquid_id(self) -> str | None: ...

    @property
    def volume_by_well(self) -> Mapping[str, float] | None: ...

    @property
    def tip_labware_id(self) -> str | None: ...

    @property
    def tip_well_name(self) -> str | None: ...


@dataclass(frozen=True)
class CommandDisposition:
    """Exhaustive per-command disposition (exactly one kind)."""

    index: int
    command_id: str | None
    command_type: str | None
    kind: CommandDispositionKind
    reason: str | None = None


@dataclass(frozen=True)
class NormalizedLeafCommand:
    """Consumed supported atomic leaf from analyze JSON (adapter output)."""

    step_index: int
    command_id: str
    command_type: SupportedLeafCommandType
    status: str
    params: Mapping[str, Any] = field(default_factory=dict)
    result: Mapping[str, Any] | None = None
    pipette_id: str | None = None
    labware_id: str | None = None
    well_name: str | None = None
    volume_ul: float | None = None
    liquid_id: str | None = None
    volume_by_well: Mapping[str, float] | None = None
    tip_labware_id: str | None = None
    tip_well_name: str | None = None


@dataclass(frozen=True)
class NormalizedCommand:
    """Handcrafted / test-friendly leaf command (also satisfies ExpectedCommand)."""

    command_id: str
    command_type: str
    step_index: int
    pipette_id: str | None = None
    labware_id: str | None = None
    well_name: str | None = None
    volume_ul: float | None = None
    liquid_id: str | None = None
    volume_by_well: Mapping[str, float] | None = None
    tip_labware_id: str | None = None
    tip_well_name: str | None = None
    params: Mapping[str, Any] = field(default_factory=dict)
    result: Mapping[str, Any] | None = None
    status: str = "succeeded"


@dataclass(frozen=True)
class AnalyzeProvenance:
    """Frozen analyze provenance envelope (required keys always present).

    ``package_sha256`` is ``None`` iff no package *file* artifact was supplied.
    Directory presence alone does not select the string branch.
    """

    protocol_sha256: str | None
    package_sha256: str | None
    ot_version: str | None
    api_level: str | None
    parameter_values: Mapping[str, Any]
    adapter_schema_version: str
    command_status_summary: Mapping[str, int]
    analyze_source_path: str | None
    command_count: int
    analyze_wall_time: float | None = None


@dataclass(frozen=True)
class AnalyzeAdapterResult:
    """Adapter output for the ledger / rules layer.

    ``commands`` contains only consumed supported leaves (ordered).
    ``unevaluable`` is True when any disposition is ``lp_l5`` (or missing
    artifact). Callers must treat ``unevaluable`` as LogicPass non-pass.
    """

    unevaluable: bool
    commands: tuple[NormalizedLeafCommand, ...]
    dispositions: tuple[CommandDisposition, ...]
    provenance: AnalyzeProvenance
    lp_l5_reasons: tuple[str, ...] = ()
    liquids: tuple[Mapping[str, Any], ...] = ()
    labware: tuple[Mapping[str, Any], ...] = ()
    pipettes: tuple[Mapping[str, Any], ...] = ()
    raw_commands: tuple[Mapping[str, Any], ...] = ()
    error_code: str | None = None  # "LP-L5" when unevaluable via adapter

    @property
    def ok(self) -> bool:
        """True when the trace is evaluable (no LP-L5 dispositions)."""
        return not self.unevaluable

    @property
    def consumed_count(self) -> int:
        return len(self.commands)


# ---------------------------------------------------------------------------
# Ledger state (Well / Tip / Reagent) — mutated by ledger.py
# ---------------------------------------------------------------------------


@dataclass
class InitialVolumeSpec:
    volume_ul: float
    liquid_id: str | None = None
    dead_volume_ul: float | None = None
    max_volume_ul: float | None = None


@dataclass
class PhysicalSetup:
    """Evaluator-owned physical setup (authoritative for hard gates)."""

    initial_volumes: dict[str, float | InitialVolumeSpec | Mapping[str, Any]] = field(
        default_factory=dict
    )
    well_roles: dict[str, WellRole | str] = field(default_factory=dict)
    dead_volumes: dict[str, float | None] = field(default_factory=dict)
    max_volumes: dict[str, float] = field(default_factory=dict)
    reagent_demands: dict[str, float] = field(default_factory=dict)
    liquid_display_names: dict[str, str] = field(default_factory=dict)
    setup_basis: SetupBasis | str = "evaluator"


@dataclass
class WellState:
    labware_id: str
    well_name: str
    liquid_id: str | None = None
    well_role: WellRole | None = None
    tracking: TrackingState = "unknown"
    current_liquid_volume_ul: float | None = None
    max_volume_ul: float | None = None
    dead_volume_ul: float | None = None
    volume_provenance: VolumeProvenance | str | None = None
    has_tracked_liquid: bool = False
    last_command_id: str | None = None


@dataclass
class TipState:
    pipette_id: str
    has_tip: bool = False
    current_volume_ul: float | None = None
    fluid_kind: str | None = None
    dirty: bool = False
    dirty_from_labware_id: str | None = None
    dirty_from_well_name: str | None = None
    tip_labware_id: str | None = None
    tip_well_name: str | None = None

    @property
    def dirty_from(self) -> str | None:
        if self.dirty_from_labware_id and self.dirty_from_well_name:
            return well_key(self.dirty_from_labware_id, self.dirty_from_well_name)
        return None


@dataclass
class ReagentBudget:
    liquid_id: str
    display_name: str | None = None
    tracking: TrackingState = "unknown"
    initial_volume_ul: float | None = None
    remaining_volume_ul: float | None = None
    consumed_volume_ul: float = 0.0
    dead_volume_ul: float | None = None
    independent_demand_ul: float | None = None
    source_wells: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InputConflict:
    code: str
    labware_id: str
    well_name: str
    detail_text: str
    evaluator_value: float | None = None
    candidate_value: float | None = None


@dataclass(frozen=True)
class LedgerStepEvent:
    """Per-step snapshot emitted by the ledger for rule evaluation."""

    step_index: int
    command_id: str
    command_type: str
    pipette_id: str | None = None
    labware_id: str | None = None
    well_name: str | None = None
    volume_ul: float | None = None
    liquid_id: str | None = None
    well_tracking: TrackingState | None = None
    well_current_ul: float | None = None
    well_dead_ul: float | None = None
    well_max_ul: float | None = None
    well_role: WellRole | None = None
    well_projected_ul: float | None = None
    tip_has_tip: bool | None = None
    tip_dirty: bool | None = None
    tip_dirty_from: str | None = None
    tip_current_ul: float | None = None
    tip_dirtied: bool = False
    tip_cleared: bool = False
    aspirate_from_protected_while_dirty: bool = False
    volume_unknown: bool = False
    notes: tuple[str, ...] = ()


@dataclass
class LedgerRunState:
    wells: dict[str, WellState] = field(default_factory=dict)
    tips: dict[str, TipState] = field(default_factory=dict)
    reagents: dict[str, ReagentBudget] = field(default_factory=dict)
    events: list[LedgerStepEvent] = field(default_factory=list)
    input_conflicts: list[InputConflict] = field(default_factory=list)
    load_liquid_declarations: dict[str, float] = field(default_factory=dict)
