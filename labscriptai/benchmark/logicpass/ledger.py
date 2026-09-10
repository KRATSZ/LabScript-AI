"""LogicPass Phase-1 state ledger (Well / Tip / Reagent).

Steps normalized analyze leaf commands and emits ``LedgerStepEvent`` snapshots
for the rule engine. Does **not** emit LP-L1–L6 verdicts.

Policies (frozen Phase 0):
- Evaluator ``physical_setup`` owns initial volumes and ``well_roles``.
- Unknown volume → ``tracking=unknown`` (never invent infinite stock).
- Unknown ``dead_volume_ul`` stays ``None`` (never coerce to 0).
- Unknown destination remains unknown after dispense.
- Tip dirtiness from evaluator ``dirty_source`` aspirates; ``dropTip*`` /
  new ``pickUpTip`` clear dirtiness.
- Candidate ``loadLiquid`` is cross-check only when evaluator volumes exist.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .types import (
    ExpectedCommand,
    InitialVolumeSpec,
    InputConflict,
    LedgerRunState,
    LedgerStepEvent,
    PhysicalSetup,
    ReagentBudget,
    TipState,
    WellRole,
    WellState,
    well_key,
)


def _as_initial_spec(
    value: float | InitialVolumeSpec | Mapping[str, Any],
) -> InitialVolumeSpec:
    if isinstance(value, InitialVolumeSpec):
        return value
    if isinstance(value, (int, float)):
        return InitialVolumeSpec(volume_ul=float(value))
    if isinstance(value, Mapping):
        vol = value.get("volume_ul", value.get("volume"))
        if vol is None:
            raise ValueError(f"initial volume mapping missing volume_ul: {value!r}")
        dead = value.get("dead_volume_ul", value.get("dead_volume"))
        max_v = value.get("max_volume_ul", value.get("max_volume"))
        return InitialVolumeSpec(
            volume_ul=float(vol),
            liquid_id=value.get("liquid_id") or value.get("liquidId"),
            dead_volume_ul=None if dead is None else float(dead),
            max_volume_ul=None if max_v is None else float(max_v),
        )
    raise TypeError(f"unsupported initial volume value: {type(value)!r}")


def _role_or_none(raw: str | None) -> WellRole | None:
    if raw is None:
        return None
    if raw in ("dirty_source", "protected_shared_source", "neutral"):
        return raw  # type: ignore[return-value]
    raise ValueError(
        f"invalid well_role {raw!r}; expected dirty_source|"
        "protected_shared_source|neutral"
    )


class StateLedger:
    """Mutable well / tip / reagent ledger stepped over ``ExpectedCommand``."""

    def __init__(self, physical_setup: PhysicalSetup | None = None) -> None:
        self.physical_setup = physical_setup or PhysicalSetup()
        self.wells: dict[str, WellState] = {}
        self.tips: dict[str, TipState] = {}
        self.reagents: dict[str, ReagentBudget] = {}
        self.events: list[LedgerStepEvent] = []
        self.input_conflicts: list[InputConflict] = []
        self.load_liquid_declarations: dict[str, float] = {}
        self._has_evaluator_volumes = bool(self.physical_setup.initial_volumes)
        self._seed_from_physical_setup()

    # ------------------------------------------------------------------ seed
    def _seed_from_physical_setup(self) -> None:
        setup = self.physical_setup
        for key, raw in setup.initial_volumes.items():
            spec = _as_initial_spec(raw)
            labware_id, well_name = key.split(":", 1) if ":" in key else (key, "")
            if not well_name:
                raise ValueError(
                    f"initial_volumes key {key!r} must be 'labwareId:wellName'"
                )
            # Explicit None in dead_volumes wins; missing key falls back to spec.
            dead = (
                setup.dead_volumes[key]
                if key in setup.dead_volumes
                else spec.dead_volume_ul
            )
            max_v = setup.max_volumes.get(key, spec.max_volume_ul)
            role = _role_or_none(setup.well_roles.get(key))
            well = WellState(
                labware_id=labware_id,
                well_name=well_name,
                liquid_id=spec.liquid_id,
                well_role=role,
                tracking="known",
                current_liquid_volume_ul=float(spec.volume_ul),
                max_volume_ul=None if max_v is None else float(max_v),
                dead_volume_ul=None if dead is None else float(dead),
                volume_provenance="evaluator_physical_setup",
                has_tracked_liquid=True,
            )
            self.wells[key] = well
            if spec.liquid_id:
                self._ensure_reagent(spec.liquid_id, key, float(spec.volume_ul), dead)

        for key, role_raw in setup.well_roles.items():
            role = _role_or_none(role_raw)
            well = self._ensure_well_slot(key)
            well.well_role = role

        for key, max_v in setup.max_volumes.items():
            well = self._ensure_well_slot(key)
            if well.max_volume_ul is None:
                well.max_volume_ul = float(max_v)

        for key, dead in setup.dead_volumes.items():
            well = self._ensure_well_slot(key)
            # Only attach dead overlay; do not invent known volume.
            well.dead_volume_ul = None if dead is None else float(dead)

        for liquid_id, demand in setup.reagent_demands.items():
            reagent = self._ensure_reagent(liquid_id, None, None, None)
            reagent.independent_demand_ul = float(demand)
            if liquid_id in setup.liquid_display_names:
                reagent.display_name = setup.liquid_display_names[liquid_id]

    def _ensure_well_slot(self, key: str) -> WellState:
        if key in self.wells:
            return self.wells[key]
        labware_id, _, well_name = key.partition(":")
        if not labware_id or not well_name:
            raise ValueError(f"invalid well key {key!r}")
        well = WellState(labware_id=labware_id, well_name=well_name, tracking="unknown")
        self.wells[key] = well
        return well

    def _ensure_reagent(
        self,
        liquid_id: str,
        source_well: str | None,
        initial_ul: float | None,
        dead_ul: float | None,
    ) -> ReagentBudget:
        reagent = self.reagents.get(liquid_id)
        if reagent is None:
            reagent = ReagentBudget(
                liquid_id=liquid_id,
                display_name=self.physical_setup.liquid_display_names.get(liquid_id),
                tracking="unknown",
            )
            self.reagents[liquid_id] = reagent
        if source_well and source_well not in reagent.source_wells:
            reagent.source_wells.append(source_well)
        if initial_ul is not None:
            if reagent.initial_volume_ul is None:
                reagent.initial_volume_ul = float(initial_ul)
                reagent.remaining_volume_ul = float(initial_ul)
                reagent.tracking = "known"
            else:
                reagent.initial_volume_ul += float(initial_ul)
                if reagent.remaining_volume_ul is None:
                    reagent.remaining_volume_ul = float(initial_ul)
                else:
                    reagent.remaining_volume_ul += float(initial_ul)
                reagent.tracking = "known"
        if dead_ul is not None and reagent.dead_volume_ul is None:
            reagent.dead_volume_ul = float(dead_ul)
        return reagent

    def _tip(self, pipette_id: str) -> TipState:
        tip = self.tips.get(pipette_id)
        if tip is None:
            tip = TipState(pipette_id=pipette_id)
            self.tips[pipette_id] = tip
        return tip

    def _well(self, labware_id: str, well_name: str) -> WellState:
        key = well_key(labware_id, well_name)
        if key not in self.wells:
            if key in self.physical_setup.max_volumes:
                max_v: float | None = float(self.physical_setup.max_volumes[key])
            elif labware_id in self.physical_setup.labware_max_ul:
                max_v = float(self.physical_setup.labware_max_ul[labware_id])
            else:
                max_v = None
            # Unknown init: never invent volume; stay tracking=unknown.
            self.wells[key] = WellState(
                labware_id=labware_id,
                well_name=well_name,
                tracking="unknown",
                well_role=_role_or_none(self.physical_setup.well_roles.get(key)),
                max_volume_ul=max_v,
                dead_volume_ul=(
                    None
                    if key not in self.physical_setup.dead_volumes
                    else (
                        None
                        if self.physical_setup.dead_volumes[key] is None
                        else float(self.physical_setup.dead_volumes[key])
                    )
                ),
            )
        well = self.wells[key]
        if (
            well.max_volume_ul is None
            and labware_id in self.physical_setup.labware_max_ul
        ):
            well.max_volume_ul = float(self.physical_setup.labware_max_ul[labware_id])
        return well

    # ------------------------------------------------------------------ run
    def run(self, commands: Iterable[ExpectedCommand]) -> LedgerRunState:
        for command in commands:
            self.step(command)
        return self.snapshot()

    def snapshot(self) -> LedgerRunState:
        return LedgerRunState(
            wells=dict(self.wells),
            tips=dict(self.tips),
            reagents=dict(self.reagents),
            events=list(self.events),
            input_conflicts=list(self.input_conflicts),
            load_liquid_declarations=dict(self.load_liquid_declarations),
        )

    def step(self, command: ExpectedCommand) -> LedgerStepEvent:
        ctype = command.command_type
        if ctype == "pickUpTip":
            event = self._step_pick_up_tip(command)
        elif ctype in ("dropTip", "dropTipInPlace"):
            event = self._step_drop_tip(command)
        elif ctype == "aspirate":
            event = self._step_aspirate(command)
        elif ctype == "dispense":
            event = self._step_dispense(command)
        elif ctype == "loadLiquid":
            event = self._step_load_liquid(command)
        else:
            # Non-state / unknown leaves are adapter concerns (LP-L5). Ledger
            # records a no-op event so callers can still align indices.
            event = LedgerStepEvent(
                step_index=command.step_index,
                command_id=command.command_id,
                command_type=ctype,
                pipette_id=command.pipette_id,
                labware_id=command.labware_id,
                well_name=command.well_name,
                volume_ul=command.volume_ul,
                notes=("non_state_or_unhandled",),
            )
        self.events.append(event)
        return event

    # --------------------------------------------------------------- commands
    def _step_pick_up_tip(self, command: ExpectedCommand) -> LedgerStepEvent:
        if not command.pipette_id:
            raise ValueError(f"{command.command_id}: pickUpTip requires pipette_id")
        tip = self._tip(command.pipette_id)
        tip.has_tip = True
        tip.current_volume_ul = 0.0
        tip.fluid_kind = None
        tip.dirty = False
        tip.dirty_from_labware_id = None
        tip.dirty_from_well_name = None
        tip.tip_labware_id = command.labware_id
        tip.tip_well_name = command.well_name
        return LedgerStepEvent(
            step_index=command.step_index,
            command_id=command.command_id,
            command_type=command.command_type,
            pipette_id=command.pipette_id,
            labware_id=tip.tip_labware_id,
            well_name=tip.tip_well_name,
            tip_has_tip=True,
            tip_dirty=False,
            tip_dirty_from=None,
            tip_current_ul=0.0,
            tip_cleared=True,
        )

    def _step_drop_tip(self, command: ExpectedCommand) -> LedgerStepEvent:
        if not command.pipette_id:
            raise ValueError(f"{command.command_id}: dropTip requires pipette_id")
        tip = self._tip(command.pipette_id)
        before_dirty = tip.dirty
        before_from = tip.dirty_from
        tip.has_tip = False
        tip.current_volume_ul = None
        tip.fluid_kind = None
        tip.dirty = False
        tip.dirty_from_labware_id = None
        tip.dirty_from_well_name = None
        tip.tip_labware_id = None
        tip.tip_well_name = None
        return LedgerStepEvent(
            step_index=command.step_index,
            command_id=command.command_id,
            command_type=command.command_type,
            pipette_id=command.pipette_id,
            labware_id=command.labware_id,
            well_name=command.well_name,
            tip_has_tip=False,
            tip_dirty=before_dirty,
            tip_dirty_from=before_from,
            tip_current_ul=None,
            tip_cleared=True,
        )

    def _step_aspirate(self, command: ExpectedCommand) -> LedgerStepEvent:
        if not command.pipette_id or not command.labware_id or not command.well_name:
            raise ValueError(
                f"{command.command_id}: aspirate requires pipette_id, "
                "labware_id, well_name"
            )
        if command.volume_ul is None:
            raise ValueError(f"{command.command_id}: aspirate requires volume_ul")

        well = self._well(command.labware_id, command.well_name)
        tip = self._tip(command.pipette_id)
        requested = float(command.volume_ul)
        tracking = well.tracking
        current = well.current_liquid_volume_ul
        unknown = tracking != "known" or current is None

        tip_dirty_before = tip.dirty
        tip_from_before = tip.dirty_from
        protected_while_dirty = (
            tip.dirty and well.well_role == "protected_shared_source"
        )

        tip_dirtied = False
        notes: list[str] = []
        if unknown:
            notes.append("source_volume_unknown")
            # Do not invent a numeric source; tip still receives the request.
        else:
            assert current is not None
            well.current_liquid_volume_ul = current - requested
            well.last_command_id = command.command_id
            if well.liquid_id and well.liquid_id in self.reagents:
                reagent = self.reagents[well.liquid_id]
                reagent.consumed_volume_ul += requested
                if reagent.remaining_volume_ul is not None:
                    reagent.remaining_volume_ul -= requested

        tip.current_volume_ul = (tip.current_volume_ul or 0.0) + requested
        tip.fluid_kind = "LIQUID"

        if well.well_role == "dirty_source":
            tip.dirty = True
            tip.dirty_from_labware_id = well.labware_id
            tip.dirty_from_well_name = well.well_name
            tip_dirtied = True

        return LedgerStepEvent(
            step_index=command.step_index,
            command_id=command.command_id,
            command_type=command.command_type,
            pipette_id=command.pipette_id,
            labware_id=command.labware_id,
            well_name=command.well_name,
            volume_ul=requested,
            liquid_id=well.liquid_id,
            well_tracking=tracking,
            well_current_ul=current,
            well_dead_ul=well.dead_volume_ul,
            well_max_ul=well.max_volume_ul,
            well_role=well.well_role,
            well_projected_ul=(
                None if unknown or current is None else current - requested
            ),
            tip_has_tip=tip.has_tip,
            tip_dirty=tip_dirty_before,
            tip_dirty_from=tip_from_before,
            tip_current_ul=tip.current_volume_ul,
            tip_dirtied=tip_dirtied,
            aspirate_from_protected_while_dirty=protected_while_dirty,
            volume_unknown=unknown,
            notes=tuple(notes),
        )

    def _step_dispense(self, command: ExpectedCommand) -> LedgerStepEvent:
        if not command.pipette_id or not command.labware_id or not command.well_name:
            raise ValueError(
                f"{command.command_id}: dispense requires pipette_id, "
                "labware_id, well_name"
            )
        if command.volume_ul is None:
            raise ValueError(f"{command.command_id}: dispense requires volume_ul")

        well = self._well(command.labware_id, command.well_name)
        tip = self._tip(command.pipette_id)
        add_ul = float(command.volume_ul)
        tracking = well.tracking
        current = well.current_liquid_volume_ul
        unknown = tracking != "known" or current is None
        notes: list[str] = []

        projected: float | None
        if unknown:
            # Unknown baseline stays unknown — never reset to 0.
            projected = None
            notes.append("destination_volume_unknown")
        else:
            assert current is not None
            projected = current + add_ul
            well.current_liquid_volume_ul = projected
            well.last_command_id = command.command_id

        if tip.current_volume_ul is not None:
            tip.current_volume_ul = tip.current_volume_ul - add_ul

        return LedgerStepEvent(
            step_index=command.step_index,
            command_id=command.command_id,
            command_type=command.command_type,
            pipette_id=command.pipette_id,
            labware_id=command.labware_id,
            well_name=command.well_name,
            volume_ul=add_ul,
            liquid_id=well.liquid_id,
            well_tracking=tracking,
            well_current_ul=current,
            well_dead_ul=well.dead_volume_ul,
            well_max_ul=well.max_volume_ul,
            well_role=well.well_role,
            well_projected_ul=projected,
            tip_has_tip=tip.has_tip,
            tip_dirty=tip.dirty,
            tip_dirty_from=tip.dirty_from,
            tip_current_ul=tip.current_volume_ul,
            volume_unknown=unknown,
            notes=tuple(notes),
        )

    def _step_load_liquid(self, command: ExpectedCommand) -> LedgerStepEvent:
        if not command.labware_id:
            raise ValueError(f"{command.command_id}: loadLiquid requires labware_id")

        volumes: dict[str, float] = {}
        if command.volume_by_well:
            volumes = {str(k): float(v) for k, v in command.volume_by_well.items()}
        elif command.well_name is not None and command.volume_ul is not None:
            volumes = {command.well_name: float(command.volume_ul)}
        else:
            raise ValueError(
                f"{command.command_id}: loadLiquid requires volume_by_well "
                "or well_name+volume_ul"
            )

        notes: list[str] = []
        last_well: str | None = None
        for well_name, vol in volumes.items():
            key = well_key(command.labware_id, well_name)
            self.load_liquid_declarations[key] = float(vol)
            last_well = well_name
            if self._has_evaluator_volumes:
                notes.append("loadLiquid_cross_check_only")
                well = self._ensure_well_slot(key)
                if (
                    well.tracking == "known"
                    and well.current_liquid_volume_ul is not None
                    and well.volume_provenance == "evaluator_physical_setup"
                    and abs(well.current_liquid_volume_ul - float(vol)) > 1e-9
                ):
                    self.input_conflicts.append(
                        InputConflict(
                            code="LP-INPUT-CONFLICT",
                            labware_id=command.labware_id,
                            well_name=well_name,
                            detail_text=(
                                f"Evaluator initial volume for {key} is "
                                f"{well.current_liquid_volume_ul} µL but candidate "
                                f"loadLiquid declares {vol} µL."
                            ),
                            evaluator_value=well.current_liquid_volume_ul,
                            candidate_value=float(vol),
                        )
                    )
                    well.volume_provenance = "conflict"
                # Never override evaluator SoT volumes from loadLiquid.
                continue

            # No evaluator volumes: may adopt protocol_declared (not independently
            # verified). Still never invent when volume missing — here it is given.
            well = self._well(command.labware_id, well_name)
            well.tracking = "known"
            well.current_liquid_volume_ul = float(vol)
            well.liquid_id = command.liquid_id or well.liquid_id
            well.volume_provenance = "protocol_declared"
            well.has_tracked_liquid = True
            well.last_command_id = command.command_id
            if well.liquid_id:
                self._ensure_reagent(well.liquid_id, key, float(vol), well.dead_volume_ul)
            notes.append("loadLiquid_protocol_declared")

        return LedgerStepEvent(
            step_index=command.step_index,
            command_id=command.command_id,
            command_type=command.command_type,
            labware_id=command.labware_id,
            well_name=last_well,
            volume_ul=None,
            liquid_id=command.liquid_id,
            notes=tuple(notes),
        )


def run_ledger(
    commands: Iterable[ExpectedCommand],
    physical_setup: PhysicalSetup | None = None,
) -> LedgerRunState:
    """Convenience: seed from evaluator setup and step all commands."""

    return StateLedger(physical_setup).run(commands)


__all__ = ["StateLedger", "run_ledger"]
