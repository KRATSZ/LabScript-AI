#!/usr/bin/env python3
"""Plan IR → Tecan Fluent worklist GWL + pyFluent XML script. stdin JSON → stdout JSON."""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_PYFLUENT = _HERE / "pyfluent"
if str(_PYFLUENT) not in sys.path:
    sys.path.insert(0, str(_PYFLUENT))

from FluentLabware import LabwareType, Nest_position  # noqa: E402
from Protocol import InvalidStateException, Protocol  # noqa: E402

PLAN_SCHEMA_ID = "bpl.plan_ir.lh.v0"
LH_PRIMITIVES = frozenset({"ASPIRATE", "DISPENSE", "MIX", "PICK_TIPS", "DROP_TIPS", "WAIT"})
DEFAULT_LIQUID_CLASS = "Water Free Single"
MIX_LIQUID_CLASS = "Water Mix"
DEFAULT_FLUENT_SN = "19905"

# Plan IR resource.type → pyFluent labware + nest. Unknown types fall back to 96-well flat.
LABWARE_BY_TYPE: dict[str, LabwareType] = {
    "plate": LabwareType.WELL_96_FLAT,
    "reservoir": LabwareType.SBS_Trough,
    "tube_rack": LabwareType.WELL_24_FLAT,
}
NEST_BY_TYPE: dict[str, Nest_position] = {
    "plate": Nest_position.Nest61mm_Pos,
    "reservoir": Nest_position.Trough_100ml,
    "tube_rack": Nest_position.Nest61mm_Pos,
}


class CompileError(Exception):
    def __init__(self, stage: str, error: str, hint: str) -> None:
        super().__init__(error)
        self.stage = stage
        self.error = error
        self.hint = hint


def fail(stage: str, error: str, hint: str) -> dict[str, Any]:
    return {"ok": False, "stage": stage, "error": error, "hint": hint}


def fmt_volume(volume: float) -> str:
    if float(volume) == int(volume):
        return str(int(volume))
    return str(volume)


def tip_mask(channels: list[int]) -> int:
    mask = 0
    for channel in channels:
        mask |= 1 << int(channel)
    return mask if mask else 255


def infer_tip_type(resource: dict[str, Any]) -> str:
    max_vol = resource.get("max_volume_ul")
    try:
        volume = float(max_vol) if max_vol is not None else 200.0
    except (TypeError, ValueError):
        volume = 200.0
    if volume <= 10:
        return "10ul"
    if volume <= 50:
        return "50ul"
    if volume <= 200:
        return "200ul"
    return "1000ul"


def slot_position(slot: Any, fallback: int) -> int:
    try:
        number = int(str(slot).strip())
        if number >= 1:
            return number
    except (TypeError, ValueError):
        pass
    return fallback


def as_primitive(raw: Any) -> str:
    return str(raw or "").strip().upper().replace("-", "_")


def parse_locs(value: Any, *, field: str, step_no: int) -> list[tuple[str, str]]:
    """Turn 'plate:A1', 'plate:A1,plate:B1', or a list of those into [(id, well)]."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out: list[tuple[str, str]] = []
        for item in value:
            out.extend(parse_locs(item, field=field, step_no=step_no))
        return out
    text = str(value).strip()
    if not text:
        return []
    parts = [part.strip() for part in text.split(",") if part.strip()]
    result: list[tuple[str, str]] = []
    for part in parts:
        if ":" not in part:
            raise CompileError(
                "mapping",
                f"Step {step_no} {field} {part!r} must look like plate:A1.",
                "Use resource_id:WELL (example: plate:A1).",
            )
        resource_id, well = part.split(":", 1)
        resource_id = resource_id.strip()
        well = well.strip().upper()
        if not resource_id or not well:
            raise CompileError(
                "mapping",
                f"Step {step_no} {field} {part!r} must look like plate:A1.",
                "Use resource_id:WELL (example: plate:A1).",
            )
        result.append((resource_id, well))
    return result


def well_token(raw: Any) -> str:
    text = str(raw or "").strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.strip().upper()


def well_on_labware(well: str, rtype: str) -> bool:
    token = well.strip().upper()
    if len(token) < 2 or not token[0].isalpha() or not token[1:].isdigit():
        return False
    row = token[0]
    col = int(token[1:])
    kind = (rtype or "").strip().lower()
    if kind == "tube_rack":
        return "A" <= row <= "D" and 1 <= col <= 6
    if kind in {"plate", "tiprack"}:
        return "A" <= row <= "H" and 1 <= col <= 12
    return True


def worklist_line(kind: str, rack: str, well: str, volume: float, liquid: str, channels: list[int]) -> str:
    return (
        f"{kind};{rack};;;{well};;{fmt_volume(volume)};{liquid};;{tip_mask(channels)};"
    )


def translate_state_error(exc: InvalidStateException, step_no: int, primitive: str) -> CompileError:
    message = str(exc)
    if primitive == "ASPIRATE":
        return CompileError(
            "state_machine",
            f"Step {step_no} aspirates before any PICK_TIPS — the head has no tips on.",
            "Add a PICK_TIPS step before ASPIRATE.",
        )
    if primitive == "DISPENSE":
        return CompileError(
            "state_machine",
            f"Step {step_no} dispenses before any PICK_TIPS — the head has no tips on.",
            "Add a PICK_TIPS step before DISPENSE.",
        )
    if primitive == "MIX":
        return CompileError(
            "state_machine",
            f"Step {step_no} mixes before any PICK_TIPS — the head has no tips on.",
            "Add a PICK_TIPS step before MIX.",
        )
    if primitive == "DROP_TIPS":
        return CompileError(
            "state_machine",
            f"Step {step_no} drops tips but the head is already empty.",
            "PICK_TIPS first, or remove this extra DROP_TIPS.",
        )
    if primitive == "PICK_TIPS":
        return CompileError(
            "state_machine",
            f"Step {step_no} picks tips while tips are already on — DROP_TIPS first.",
            "Insert DROP_TIPS before the next PICK_TIPS.",
        )
    return CompileError(
        "state_machine",
        f"Step {step_no} ({primitive}) is illegal for the current FCA state: {message}",
        "PICK_TIPS before pipetting, DROP_TIPS before picking again.",
    )


class FluentCompiler:
    def __init__(self, plan: dict[str, Any]) -> None:
        self.plan = plan
        self.warnings: list[str] = []
        self.worklist: list[str] = []
        self._mix_count_adjust = 0  # worklist A/D for MIX replace the single XML LihaMix
        self.resources: dict[str, dict[str, Any]] = {}
        self.tipracks: dict[str, dict[str, Any]] = {}
        self.loaded_channels: list[int] = []
        self.liquid_class = DEFAULT_LIQUID_CLASS
        sn = str(os.environ.get("FLUENT_SN") or DEFAULT_FLUENT_SN).strip() or DEFAULT_FLUENT_SN
        self.protocol = Protocol(fluent_sn=sn, output_file="fluent_unused.gwl")

    def compile(self) -> dict[str, Any]:
        self._parse_resources()
        self._check_initial_volumes()
        self._add_deck_labware()
        steps = self.plan.get("steps")
        if not isinstance(steps, list) or not steps:
            raise CompileError(
                "mapping",
                "Plan has no steps — nothing to compile.",
                "Add at least PICK_TIPS → ASPIRATE → DISPENSE → DROP_TIPS.",
            )
        plan_id = str(self.plan.get("plan_id") or self.plan.get("protocol_name") or "plan")
        self.worklist.append(f"C; Plan IR {plan_id} compiled for Tecan FluentControl Load Worklist")
        self.worklist.append("C; WellPos uses alphanumeric form (A1, B1, …). Column-major 96-well: A1=1, B1=2, H1=8, A2=9")
        self.worklist.append(f"C; LiquidClass default: {DEFAULT_LIQUID_CLASS}; TipMask is an 8-channel bitmask (ch0=1, all eight=255)")
        self.worklist.append("C; MIX steps are expanded to aspirate/dispense cycles")

        fca = self.protocol.fca()
        for index, raw in enumerate(steps, start=1):
            if not isinstance(raw, dict):
                raise CompileError(
                    "mapping",
                    f"Step {index} must be an object.",
                    "Each steps[] entry needs primitive_type and the fields for that primitive.",
                )
            primitive = as_primitive(raw.get("primitive_type") or raw.get("type"))
            if primitive not in LH_PRIMITIVES:
                raise CompileError(
                    "mapping",
                    f"Step {index} has unknown primitive_type {primitive or '(missing)'!r}.",
                    f"LH subset is {', '.join(sorted(LH_PRIMITIVES))}.",
                )
            try:
                self._emit_step(fca, index, primitive, raw)
            except InvalidStateException as exc:
                raise translate_state_error(exc, index, primitive) from exc
            except ValueError as exc:
                raise CompileError(
                    "mapping",
                    f"Step {index}: {self._humanize_value_error(str(exc))}",
                    "Declare the labware in resources[] and point the step at that id.",
                ) from exc

        script_xml = self.protocol.get_script()
        worklist_gwl = "\n".join(self.worklist) + "\n"
        return {
            "ok": True,
            "worklist_gwl": worklist_gwl,
            "script_xml": script_xml,
            "command_count": self.protocol.get_command_count() + self._mix_count_adjust,
            "warnings": self.warnings,
        }

    def _humanize_value_error(self, message: str) -> str:
        if "未定义" in message:
            start = message.find("'")
            end = message.find("'", start + 1) if start >= 0 else -1
            label = message[start + 1 : end] if start >= 0 and end > start else "that labware"
            return f"{label!r} is not on the worktable — add it to resources[]."
        return message

    def _parse_resources(self) -> None:
        raw_list = self.plan.get("resources")
        if not isinstance(raw_list, list) or not raw_list:
            raise CompileError(
                "mapping",
                "Plan has no resources.",
                "Add a tiprack plus a plate or reservoir in resources[].",
            )
        for item in raw_list:
            if not isinstance(item, dict):
                raise CompileError(
                    "mapping",
                    "Each resource must be an object with id and type.",
                    "Example: {\"id\": \"plate\", \"type\": \"plate\", \"slot\": \"2\"}.",
                )
            resource_id = str(item.get("id") or "").strip()
            rtype = str(item.get("type") or "").strip().lower()
            if not resource_id:
                raise CompileError(
                    "mapping",
                    "A resource is missing id.",
                    "Give every resource a stable id (the left side of plate:A1).",
                )
            record = {**item, "id": resource_id, "type": rtype}
            self.resources[resource_id] = record
            if rtype == "tiprack":
                self.tipracks[resource_id] = record

    def _check_initial_volumes(self) -> None:
        volumes = self.plan.get("initial_volumes_ul") or self.plan.get("initial_volumes") or {}
        if not volumes:
            return
        if not isinstance(volumes, dict):
            self.warnings.append("initial_volumes_ul is not an object; ignored (volume checks belong upstream).")
            return
        for key, value in volumes.items():
            try:
                locs = parse_locs(key, field="initial_volumes_ul", step_no=0)
            except CompileError:
                self.warnings.append(f"initial_volumes_ul key {key!r} is not resource:well; ignored.")
                continue
            try:
                amount = float(value)
            except (TypeError, ValueError):
                continue
            for resource_id, _well in locs:
                resource = self.resources.get(resource_id)
                max_vol = None if resource is None else resource.get("max_volume_ul")
                if max_vol is None:
                    continue
                try:
                    limit = float(max_vol)
                except (TypeError, ValueError):
                    continue
                if amount > limit:
                    raise CompileError(
                        "mapping",
                        f"initial_volumes_ul {key} is {fmt_volume(amount)} µL, above {resource_id} max_volume_ul {fmt_volume(limit)}.",
                        "Lower the starting volume or use a well that can hold it.",
                    )

    def _add_deck_labware(self) -> None:
        next_pos = 1
        for resource_id, resource in self.resources.items():
            rtype = resource["type"]
            if rtype == "tiprack":
                continue
            labware = LABWARE_BY_TYPE.get(rtype)
            nest = NEST_BY_TYPE.get(rtype)
            if labware is None:
                self.warnings.append(
                    f"Resource {resource_id!r} has unknown type {rtype!r}; using 96 Well Flat."
                )
                labware = LabwareType.WELL_96_FLAT
                nest = Nest_position.Nest61mm_Pos
            elif rtype == "tube_rack":
                self.warnings.append(
                    f"Resource {resource_id!r} (tube_rack) mapped to {labware.value}."
                )
            position = slot_position(resource.get("slot"), next_pos)
            self.protocol.add_labware(labware, resource_id, nest, position)
            next_pos = max(next_pos, position) + 1

    def _require_resource(self, resource_id: str, step_no: int, action: str) -> dict[str, Any]:
        resource = self.resources.get(resource_id)
        if resource is None:
            raise CompileError(
                "mapping",
                f"Step {step_no} {action} '{resource_id}', which is not in resources.",
                f"Add a resource with id '{resource_id}', or point the step at a declared plate.",
            )
        if resource["type"] == "tiprack":
            raise CompileError(
                "mapping",
                f"Step {step_no} {action} tiprack '{resource_id}' — pipetting needs a plate or reservoir.",
                "Use a plate/reservoir id on the left of resource:WELL.",
            )
        return resource

    def _channels_for_wells(self, n_wells: int, step_no: int, action: str) -> list[int]:
        loaded = list(self.loaded_channels or self.protocol.fca().current_channels or [])
        if not loaded:
            return []
        if n_wells > len(loaded):
            raise CompileError(
                "mapping",
                f"Step {step_no} {action} {n_wells} wells but only {len(loaded)} tip(s) loaded.",
                "Pick as many tips as wells, or pipette fewer wells in this step.",
            )
        return loaded[:n_wells]

    def _volume(self, raw: dict[str, Any], step_no: int, primitive: str) -> float:
        if raw.get("volume_ul") is None:
            raise CompileError(
                "mapping",
                f"Step {step_no} {primitive} needs volume_ul.",
                "Set volume_ul to a number greater than 0.",
            )
        try:
            volume = float(raw["volume_ul"])
        except (TypeError, ValueError) as exc:
            raise CompileError(
                "mapping",
                f"Step {step_no} volume_ul must be a number.",
                "Example: \"volume_ul\": 50.",
            ) from exc
        if volume <= 0:
            raise CompileError(
                "mapping",
                f"Step {step_no} volume_ul must be > 0.",
                "Use a positive microlitre volume.",
            )
        return volume

    def _emit_step(self, fca: Any, step_no: int, primitive: str, raw: dict[str, Any]) -> None:
        if primitive == "PICK_TIPS":
            self._pick_tips(fca, step_no, raw)
            return
        if primitive == "DROP_TIPS":
            if raw.get("to_waste") is False:
                self.warnings.append(
                    f"Step {step_no} DROP_TIPS to_waste=false; Fluent drop still goes to the waste chute."
                )
            fca.drop_tips()
            self.loaded_channels = []
            self.worklist.append("B;")
            return
        if primitive == "WAIT":
            duration = raw.get("duration_s")
            label = fmt_volume(float(duration)) if duration is not None else "?"
            self.worklist.append(f"C; WAIT duration_s={label} (no FluentControl worklist command)")
            self.warnings.append(
                f"Step {step_no} WAIT has no GWL command; emitted as a C; comment."
            )
            return
        if primitive == "ASPIRATE":
            self._pipette(fca, step_no, raw, kind="A", field="source", action="aspirates from", method="aspirate")
            return
        if primitive == "DISPENSE":
            self._pipette(fca, step_no, raw, kind="D", field="destination", action="dispenses into", method="dispense")
            return
        if primitive == "MIX":
            self._mix(fca, step_no, raw)
            return

    def _pick_tips(self, fca: Any, step_no: int, raw: dict[str, Any]) -> None:
        positions_raw = raw.get("tip_positions") or ()
        if isinstance(positions_raw, str):
            positions = [positions_raw]
        elif isinstance(positions_raw, (list, tuple)):
            positions = list(positions_raw)
        else:
            raise CompileError(
                "mapping",
                f"Step {step_no} PICK_TIPS tip_positions must be a list.",
                "Example: \"tip_positions\": [\"A1\"].",
            )
        wells = [well_token(item) for item in positions if str(item).strip()]
        if not wells:
            raise CompileError(
                "mapping",
                f"Step {step_no} PICK_TIPS needs tip_positions.",
                "Example: \"tip_positions\": [\"A1\"].",
            )
        for well in wells:
            if not well_on_labware(well, "tiprack"):
                raise CompileError(
                    "mapping",
                    f"Step {step_no} PICK_TIPS well {well} is not on a tiprack (A1–H12).",
                    "Use a tip well that exists (A1–H12).",
                )
        tip_rack_id = str(raw.get("tip_rack") or "").strip()
        if tip_rack_id:
            rack = self.tipracks.get(tip_rack_id) or self.resources.get(tip_rack_id)
            if rack is None:
                raise CompileError(
                    "mapping",
                    f"Step {step_no} PICK_TIPS tip_rack '{tip_rack_id}' is not in resources.",
                    "Point tip_rack at a declared tiprack id.",
                )
            if rack.get("type") != "tiprack":
                raise CompileError(
                    "mapping",
                    f"Step {step_no} PICK_TIPS tip_rack '{tip_rack_id}' is type {rack.get('type')!r}, not tiprack.",
                    "Use the tiprack resource id.",
                )
        elif len(self.tipracks) == 1:
            rack = next(iter(self.tipracks.values()))
        elif not self.tipracks:
            raise CompileError(
                "mapping",
                f"Step {step_no} PICK_TIPS needs a tiprack resource.",
                "Add {\"id\": \"tips\", \"type\": \"tiprack\", \"slot\": \"1\"}.",
            )
        else:
            raise CompileError(
                "mapping",
                f"Step {step_no} PICK_TIPS does not say which tip_rack to use.",
                "Set tip_rack to one of: " + ", ".join(sorted(self.tipracks)) + ".",
            )
        channels = list(range(len(wells)))
        fca.get_tips(infer_tip_type(rack), channels)
        self.loaded_channels = channels

    def _pipette(
        self,
        fca: Any,
        step_no: int,
        raw: dict[str, Any],
        *,
        kind: str,
        field: str,
        action: str,
        method: str,
    ) -> None:
        locs = parse_locs(raw.get(field), field=field, step_no=step_no)
        if not locs:
            raise CompileError(
                "mapping",
                f"Step {step_no} {as_primitive(raw.get('primitive_type'))} needs {field} like plate:A1.",
                f"Set \"{field}\" to a declared resource well.",
            )
        volume = self._volume(raw, step_no, as_primitive(raw.get("primitive_type")))
        channels = self._channels_for_wells(len(locs), step_no, action)
        liquid = str(raw.get("liquid_class") or self.liquid_class)
        grouped: list[tuple[str, list[str]]] = []
        for resource_id, well in locs:
            resource = self._require_resource(resource_id, step_no, action)
            if not well_on_labware(well, str(resource.get("type") or "")):
                bounds = "A1–D6" if resource.get("type") == "tube_rack" else "A1–H12"
                raise CompileError(
                    "mapping",
                    f"Step {step_no} {action} well {well} is not on {resource_id} ({bounds}).",
                    f"Use a well that exists on that labware ({bounds}).",
                )
            if grouped and grouped[-1][0] == resource_id:
                grouped[-1][1].append(well)
            else:
                grouped.append((resource_id, [well]))
        channel_offset = 0
        for resource_id, wells in grouped:
            used = channels[channel_offset : channel_offset + len(wells)] or channels
            getattr(fca, method)(
                volume,
                resource_id,
                wells=",".join(wells),
                liquid_class=liquid,
                channels=used,
            )
            channel_offset += len(wells)
        for well_index, (resource_id, well) in enumerate(locs):
            well_channels = [channels[well_index]] if well_index < len(channels) else channels
            self.worklist.append(worklist_line(kind, resource_id, well, volume, liquid, well_channels))

    def _mix(self, fca: Any, step_no: int, raw: dict[str, Any]) -> None:
        locs = parse_locs(
            raw.get("location") or raw.get("source") or raw.get("destination"),
            field="location",
            step_no=step_no,
        )
        if not locs:
            raise CompileError(
                "mapping",
                f"Step {step_no} MIX needs location like plate:A1.",
                "Set \"location\" to the well being mixed.",
            )
        volume = self._volume(raw, step_no, "MIX")
        try:
            cycles = int(raw.get("cycles") or 3)
        except (TypeError, ValueError):
            cycles = 3
        cycles = max(1, cycles)
        channels = self._channels_for_wells(len(locs), step_no, "mixes")
        resource_id, wells = locs[0][0], [well for _rid, well in locs]
        if any(rid != resource_id for rid, _well in locs):
            raise CompileError(
                "mapping",
                f"Step {step_no} MIX spans more than one labware.",
                "Keep one MIX step per plate.",
            )
        self._require_resource(resource_id, step_no, "mixes")
        fca.mix(
            cycles,
            volume,
            resource_id,
            wells=",".join(wells),
            liquid_class=MIX_LIQUID_CLASS,
            channels=channels,
        )
        liquid = str(raw.get("liquid_class") or self.liquid_class)
        for _ in range(cycles):
            for well_index, (_rid, well) in enumerate(locs):
                well_channels = [channels[well_index]] if well_index < len(channels) else channels
                self.worklist.append(worklist_line("A", resource_id, well, volume, liquid, well_channels))
                self.worklist.append(worklist_line("D", resource_id, well, volume, liquid, well_channels))
        # XML counted 1 LihaMix; worklist counts each A and D (one cycle = 2).
        self._mix_count_adjust += 2 * cycles * len(locs) - 1


def load_plan_object(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text or "")
    except json.JSONDecodeError as exc:
        raise CompileError(
            "mapping",
            "Input is not valid JSON.",
            "Pass a Plan IR object on stdin (schema bpl.plan_ir.lh.v0).",
        ) from exc
    if not isinstance(payload, dict):
        raise CompileError(
            "mapping",
            "Plan IR must be a JSON object.",
            "Top level needs schema, resources[], and steps[].",
        )
    schema = str(payload.get("schema") or PLAN_SCHEMA_ID).strip()
    if schema != PLAN_SCHEMA_ID:
        raise CompileError(
            "mapping",
            f"Unknown schema {schema!r}; expected {PLAN_SCHEMA_ID}.",
            f"Set \"schema\": \"{PLAN_SCHEMA_ID}\".",
        )
    return payload


def compile_text(raw_text: str) -> dict[str, Any]:
    plan = load_plan_object(raw_text)
    return FluentCompiler(plan).compile()


def main() -> int:
    try:
        result = compile_text(sys.stdin.read())
    except CompileError as exc:
        result = fail(exc.stage, exc.error, exc.hint)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        result = fail(
            "internal",
            "Compiler crashed.",
            "See stderr traceback; this is a compiler bug.",
        )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
