"""Turn an ``opentrons analyze`` result into keyframes for the Flex MuJoCo scene.

The analysis JSON is the only input. ``loadModule`` gives each module's model
and slot (its shape comes from the module JSON in ``cad/``), ``loadLabware``
each labware's full definition and what it sits on (a slot, a module or the
labware below), ``loadPipette`` the mounts, ``loadLiquid`` the starting
volumes, ``pickUpTip.result.tipLength`` how far a mounted tip reaches below the
nozzle, and every positional command carries ``result.position``: the
pipette's critical point in deck millimeters. Motion is built around those
points the way the protocol engine moves:

* between different labware the lowest point of the tool (tip end, nozzle, or
  the bottom of a held plate) rises above the tallest thing on the deck, then
  travels, then descends; within one labware it clears that labware only;
* the critical point is nozzle A, except for an 8-channel over a labware with
  the ``centerMultichannelOnWells`` quirk or over a trash bin, where it is the
  centre of the eight nozzles;
* ``moveLabware`` with the gripper: pipettes retract, jaws open over the
  labware, close on its front and back faces at ``gripHeightFromLabwareBottom``,
  lift to the top of the gripper stroke, travel, set down, release.

Tips and liquid are tracked per nozzle. A pick-up takes the rack tip under
each nozzle, an aspirate takes volume out of the well under each nozzle in
proportion to what it holds, and so on, so every colour on screen is the
consequence of commands in the JSON.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from . import flex_shell
from .flex_scene import (
    CHUTE_BODY_OFFSET_MM,
    CHUTE_BODY_SIZE_MM,
    DECK_PATH,
    MM,
    MODULE_FIXTURES,
    PADDLE_HALF_MM,
    Deck,
    Labware,
    Module,
    Placed,
    SceneSpec,
    TipDims,
    TrashBin,
    WasteChute,
    home_point,
    labware_from_definition,
    load_module,
    robot_m,
)

PIPETTE_TOOLS = {
    ("p1000_single_flex", "right"): "pipette_1000",
    ("p50_single_flex", "right"): "pipette_1000",
    ("p1000_single_flex", "left"): "pipette_1000_left",
    ("p50_single_flex", "left"): "pipette_1000_left",
    ("p1000_multi_flex", "left"): "pipette_8",
    ("p50_multi_flex", "left"): "pipette_8",
    ("p1000_multi_flex", "right"): "pipette_8_right",
    ("p50_multi_flex", "right"): "pipette_8_right",
}
CHANNELS = {"pipette_1000": 1, "pipette_8": 8, "pipette_1000_left": 1, "pipette_8_right": 8}
EIGHT_TOOLS = frozenset(name for name, count in CHANNELS.items() if count == 8)
PITCH_MM = flex_shell.NOZZLE_PITCH / MM
# Nozzle A to the centre of eight nozzles, along -y.
CENTER_OFFSET_MM = 3.5 * PITCH_MM
Z_PARK_MM = flex_shell.Z_PARK / MM

# Playback speeds (m/s). Faster than a real Flex Z axis so the clip stays short.
V_XY = 0.30
V_Z = 0.15
V_JAW = 0.06
MIN_MOVE_S = 0.16
# Clearance above the tallest obstacle when crossing between labware, and above
# the current labware when moving inside it.
CROSS_CLEAR_MM = 15.0
WITHIN_CLEAR_MM = 10.0
# An ejected tip drops this far: from the bin rim (40 mm) to just above its floor.
TRASH_FALL_M = 0.034

JOINTS_BASE = ("x", "y", "z_gripper", "jaw_f", "jaw_b")
NO_MOTION = {
    "loadLabware",
    "loadPipette",
    "loadLiquid",
    "loadModule",
    "loadLiquidClass",
    "configureForVolume",
    "prepareToAspirate",
    "setRailLights",
    "setStatusBar",
}


MODULE_NAMES = {
    "heaterShakerModuleType": "加热振荡模块",
    "temperatureModuleType": "温控模块",
    "magneticBlockType": "磁力架",
    "thermocyclerModuleType": "PCR 仪",
    "absorbanceReaderType": "酶标仪",
}
MODULE_ACTIONS = {
    "setTargetTemperature": "设定温度",
    "waitForTemperature": "等待温度",
    "setAndWaitForShakeSpeed": "振荡",
    "deactivateShaker": "停止振荡",
    "deactivateHeater": "停止加热",
    "openLabwareLatch": "打开夹扣",
    "closeLabwareLatch": "合上夹扣",
    "deactivate": "关闭",
    "openLid": "开盖",
    "closeLid": "合盖",
    "setTargetBlockTemperature": "设定模块温度",
    "waitForBlockTemperature": "等待模块温度",
    "setTargetLidTemperature": "设定热盖温度",
    "waitForLidTemperature": "等待热盖温度",
    "deactivateBlock": "关闭模块温控",
    "deactivateLid": "关闭热盖",
    "runProfile": "运行温度程序",
    "runExtendedProfile": "运行温度程序",
    "initialize": "初始化",
    "read": "读板",
}
MODULE_PREFIXES = ("heaterShaker/", "temperatureModule/", "thermocycler/", "magneticModule/", "absorbanceReader/")
# These are the module actions for which this digital replay has an explicit
# visual/state contract.  A command in a known module family is not accepted
# merely because its prefix happens to match: silently turning a new action
# into a generic 0.6 s beat makes liquid/motion timelines lie.
SUPPORTED_MODULE_COMMANDS = frozenset(
    {
        "magneticModule/engage",
        "magneticModule/disengage",
        "heaterShaker/setTargetTemperature",
        "heaterShaker/waitForTemperature",
        "heaterShaker/setAndWaitForShakeSpeed",
        "heaterShaker/deactivateShaker",
        "heaterShaker/deactivateHeater",
        "heaterShaker/openLabwareLatch",
        "heaterShaker/closeLabwareLatch",
        "temperatureModule/setTargetTemperature",
        "temperatureModule/waitForTemperature",
        "temperatureModule/deactivate",
        "thermocycler/openLid",
        "thermocycler/closeLid",
        "thermocycler/setTargetLidTemperature",
        "thermocycler/setTargetBlockTemperature",
        "thermocycler/waitForLidTemperature",
        "thermocycler/waitForBlockTemperature",
        "thermocycler/deactivateLid",
        "thermocycler/deactivateBlock",
        "thermocycler/runProfile",
        "thermocycler/runExtendedProfile",
        "thermocycler/awaitProfileComplete",
        "absorbanceReader/initialize",
        "absorbanceReader/openLid",
        "absorbanceReader/closeLid",
        "absorbanceReader/read",
    }
)
HOME_AXES = frozenset(
    {
        "x",
        "y",
        "leftZ",
        "rightZ",
        "extensionZ",
        "extensionJaw",
        # These axes are real Flex command-engine axes, but the web model has
        # no independent plunger/cam geometry.  Homing them is therefore a
        # validated no-op rather than an invented joint motion.
        "leftPlunger",
        "rightPlunger",
        "axis96ChannelCam",
    }
)

# Where a labware sits: ("slot", "D1"), ("module", module key) or ("labware", labware key).
Parent = tuple[str, str]


class ProtocolError(RuntimeError):
    pass


@dataclass
class LabwareRun:
    id: str
    key: str
    load_name: str
    name: str
    slot: str
    labware: Labware
    definition: dict
    parent: Parent = ("slot", "")
    # Height drawn above the origin: an adapter stops where the labware on it sits.
    height: float = 0.0


@dataclass
class PipetteRun:
    id: str
    name: str
    mount: str
    tool: str
    tip: TipDims | None = None

    @property
    def channels(self) -> int:
        return CHANNELS[self.tool]


@dataclass
class LiquidRun:
    id: str
    name: str
    rgb: tuple[float, float, float]


@dataclass
class ProtocolRun:
    path: Path
    title: str
    labware: dict[str, LabwareRun]
    pipettes: dict[str, PipetteRun]
    liquids: dict[str, LiquidRun]
    commands: list[dict]
    trash: dict[str, TrashBin]
    moved: list[str]
    deck: Deck
    modules: dict[str, Module] = field(default_factory=dict)
    # Labware that changes place during the run (moved, or riding on moved labware): it hangs on slide joints.
    carried: list[str] = field(default_factory=list)
    # Chute drop-slot areas by name (zero-volume boxes; the drop point is their
    # origin, or the centre of the eight-channel span) and the one drawn body.
    chutes: dict[str, TrashBin] = field(default_factory=dict)
    chute: WasteChute | None = None

    def by_key(self, key: str) -> LabwareRun:
        return next(lw for lw in self.labware.values() if lw.key == key)

    def module_by_key(self, key: str) -> Module:
        return next(m for m in self.modules.values() if m.key == key)

    def placement(self, key: str, parent: Parent, origin: dict[str, tuple[float, float, float]]) -> tuple[float, float, float]:
        """Front-left-bottom of labware ``key`` set on ``parent``, deck mm.

        The protocol engine's schema-2 stacking: the parent's placement point
        (slot, module addressable area less ``stackingOffsetWithModule``, or the
        labware below at its ``zDimension`` less ``stackingOffsetWithLabware``)
        plus this labware's ``cornerOffsetFromSlot``. A labware below counts
        from its own placement point, without its corner offset.
        """

        run = self.by_key(key)
        lw = run.labware
        kind, ref = parent
        if kind == "slot":
            base = self.deck.slots[ref]
        elif kind == "module":
            mod = self.module_by_key(ref)
            ov = lw.on_module.get(mod.model, (0.0, 0.0, 0.0))
            base = tuple(mod.area_mm[i] - ov[i] for i in range(3))
        else:
            below = self.by_key(ref)
            ov = lw.on_labware.get(below.load_name) or lw.on_labware.get("default")
            if ov is None:
                raise ProtocolError(f"{run.name} has no stackingOffsetWithLabware for {below.load_name}")
            o, c = origin[ref], below.labware.offset
            base = (o[0] - c[0] + ov[0], o[1] - c[1] + ov[1], o[2] - c[2] + below.labware.z - ov[2])
        return tuple(base[i] + lw.offset[i] for i in range(3))

    def where_text(self, parent: Parent) -> str:
        kind, ref = parent
        if kind == "slot":
            return ref
        if kind == "module":
            mod = self.module_by_key(ref)
            return f"{mod.label}({mod.slot})"
        return f"{self.by_key(ref).name} 上"


def _hex_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _trash_bins(deck_raw: dict) -> dict[str, TrashBin]:
    """Every trash-bin addressable area the deck JSON defines, by area name."""

    cutouts = {c["id"]: c["position"] for c in deck_raw["locations"]["cutouts"]}
    areas = {a["id"]: a for a in deck_raw["locations"]["addressableAreas"]}
    bins: dict[str, TrashBin] = {}
    for fixture in deck_raw["cutoutFixtures"]:
        if fixture["id"] != "trashBinAdapter":
            continue
        for cutout, names in fixture["providesAddressableAreas"].items():
            for name in names:
                area = areas[name]
                off = area["offsetFromCutoutFixture"]
                box = area["boundingBox"]
                origin = tuple(cutouts[cutout][i] + off[i] for i in range(3))
                bins[name] = TrashBin(name, origin, (box["xDimension"], box["yDimension"], box["zDimension"]))
    return bins


def _location(location, what: str) -> Parent:
    """``("slot" | "module" | "labware", id)`` for a labware location from the analysis."""

    if isinstance(location, dict):
        for field_name, kind in (("slotName", "slot"), ("addressableAreaName", "slot"), ("moduleId", "module"), ("labwareId", "labware")):
            if field_name in location:
                return kind, location[field_name]
    raise ProtocolError(f"{what}: location {location} is not modelled (off-deck and the waste chute are not drawn)")


def _waste_chutes(deck_raw: dict) -> tuple[dict[str, TrashBin], dict[str, WasteChute]]:
    """Waste-chute addressable areas by name, plus one stand-in body per cutout.

    The areas are drop slots: their bounding boxes are flat or a line, so they
    work as exact drop points (``expected_position`` centres them) but are not
    drawn. One ``WasteChute`` body per cutout covers every slot on it.
    """

    cutouts = {c["id"]: c["position"] for c in deck_raw["locations"]["cutouts"]}
    areas = {a["id"]: a for a in deck_raw["locations"]["addressableAreas"]}
    slots: dict[str, TrashBin] = {}
    bodies: dict[str, WasteChute] = {}
    for fixture in deck_raw["cutoutFixtures"]:
        if not fixture["id"].startswith("wasteChute"):
            continue
        for cutout, names in fixture["providesAddressableAreas"].items():
            for name in names:
                area = areas[name]
                if area.get("areaType") != "wasteChute":
                    continue  # combined fixtures also provide staging slots
                off = area["offsetFromCutoutFixture"]
                box = area["boundingBox"]
                origin = tuple(cutouts[cutout][i] + off[i] for i in range(3))
                slots[name] = TrashBin(name, origin, (box["xDimension"], box["yDimension"], box["zDimension"]))
                bodies[cutout] = WasteChute(
                    cutout,
                    tuple(cutouts[cutout][i] + CHUTE_BODY_OFFSET_MM[i] for i in range(3)),
                    CHUTE_BODY_SIZE_MM,
                )
    return slots, bodies


def load_analysis(path: Path, deck: Deck) -> ProtocolRun:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("errors"):
        first = raw["errors"][0]
        raise ProtocolError(f"analysis has errors: {first.get('errorType')}: {first.get('detail')}")
    if raw.get("robotType") not in (None, "OT-3 Standard"):
        raise ProtocolError(f"robotType is {raw.get('robotType')}, not a Flex")
    deck_raw = json.loads(DECK_PATH.read_text(encoding="utf-8"))
    bins = _trash_bins(deck_raw)
    chute_slots, chute_bodies = _waste_chutes(deck_raw)

    labware: dict[str, LabwareRun] = {}
    pipettes: dict[str, PipetteRun] = {}
    liquids = {
        item["id"]: LiquidRun(item["id"], item.get("displayName", item["id"]), _hex_rgb(item.get("displayColor", "#3C78D8")))
        for item in raw.get("liquids", [])
    }
    trash: dict[str, TrashBin] = {}
    chutes: dict[str, TrashBin] = {}
    moved: list[str] = []
    modules: dict[str, Module] = {}

    def parent_key(location, what: str) -> tuple[Parent, str]:
        """The parent by scene key, and the deck slot under it."""

        kind, ref = _location(location, what)
        if kind == "slot":
            if ref not in deck.slots:
                raise ProtocolError(f"{what}: slot {ref} is not one of the twelve deck slots")
            return (kind, ref), ref
        if kind == "module":
            mod = modules[ref]
            return (kind, mod.key), mod.slot
        below = labware[ref]
        return (kind, below.key), below.slot

    for cmd in raw["commands"]:
        kind, params, result = cmd["commandType"], cmd["params"], cmd.get("result") or {}
        if kind == "loadModule":
            model = result.get("model") or params["model"]
            slot = _location(params["location"], model)[1]
            try:
                mod = load_module(model, slot, f"mod{len(modules) + 1}")
            except KeyError:
                raise ProtocolError(f"{model} is not drawn in this scene. Supported modules: {', '.join(MODULE_FIXTURES)}") from None
            except ValueError as exc:
                raise ProtocolError(str(exc)) from None
            mod.label = MODULE_NAMES.get(mod.module_type, mod.label)
            modules[result["moduleId"]] = mod
        elif kind == "loadLabware":
            definition = result["definition"]
            if definition.get("schemaVersion", 2) != 2:
                raise ProtocolError(f"{params['loadName']}: labware schema {definition.get('schemaVersion')} is not modelled (schema 2 only)")
            lw = labware_from_definition(definition)
            parent, slot = parent_key(params["location"], params["loadName"])
            run = LabwareRun(
                id=result["labwareId"],
                key=f"lw{len(labware) + 1}",
                load_name=params["loadName"],
                name=params.get("displayName") or definition["metadata"]["displayName"],
                slot=slot,
                labware=lw,
                definition=definition,
                parent=parent,
                height=lw.top,
            )
            labware[run.id] = run
        elif kind == "loadPipette":
            tool = PIPETTE_TOOLS.get((params["pipetteName"], params["mount"]))
            if tool is None:
                raise ProtocolError(
                    f"{params['pipetteName']} on the {params['mount']} mount is not in this scene. "
                    "Supported: flex_1channel_50 and flex_1channel_1000 on either mount, "
                    "and flex_8channel_50 and flex_8channel_1000 on either mount."
                )
            pipettes[result["pipetteId"]] = PipetteRun(result["pipetteId"], params["pipetteName"], params["mount"], tool)
        elif kind == "pickUpTip":
            pip = pipettes[params["pipetteId"]]
            rack = labware[params["labwareId"]].labware
            dims = TipDims(float(result["tipLength"]), rack.tip_length, float(result.get("tipDiameter") or 2 * rack.wells["A1"].radius))
            if pip.tip is not None and abs(pip.tip.reach_mm - dims.reach_mm) > 1e-6:
                raise ProtocolError(f"{pip.name} uses tips of two lengths; the scene mounts one")
            pip.tip = dims
        elif kind in ("moveToAddressableArea", "moveToAddressableAreaForDropTip"):
            name = params["addressableAreaName"]
            if name in bins:
                trash[name] = bins[name]
            elif name in chute_slots:
                chutes[name] = chute_slots[name]
            else:
                # Loud, not silent: an area the scene cannot place used to be
                # skipped here and blow up later as a KeyError at play time.
                raise ProtocolError(
                    f"addressable area {name} is not one this scene draws "
                    f"(trash bins: {sorted(bins)}, waste chutes: {sorted(chute_slots)})"
                )
        elif kind == "moveLabware":
            if params.get("strategy") == "usingGripper" and params["labwareId"] not in moved:
                moved.append(params["labwareId"])
    title = raw.get("metadata", {}).get("protocolName") or path.stem
    # The deck definition lists possible fixtures, not installed ones. Drawing
    # its optional chute unconditionally overlaps a trash bin or labware in D3.
    chute = next(iter(chute_bodies.values()), None) if chutes else None
    run = ProtocolRun(path, title, labware, pipettes, liquids, raw["commands"], trash, moved, deck, modules=modules, chutes=chutes, chute=chute)
    _settle(run)
    return run


def _settle(run: ProtocolRun) -> None:
    """Walk the moves once: what rides on moved labware, and where every module and adapter seat is.

    A module body and an adapter block are drawn up to the lowest bottom of any
    labware set on them, so a plate sinking into its seat does not read as a
    collision.
    """

    by_key = {lw.key: lw for lw in run.labware.values()}
    parent = {lw.key: lw.parent for lw in run.labware.values()}
    carried: set[str] = set()
    placed: list[tuple[str, Parent]] = list(parent.items())

    def riders(key: str) -> list[str]:
        out = [k for k, p in parent.items() if p == ("labware", key)]
        return out + [r for k in out for r in riders(k)]

    for cmd in run.commands:
        if cmd["commandType"] != "moveLabware":
            continue
        params = cmd["params"]
        lw = run.labware[params["labwareId"]]
        kind, ref = _location(params["newLocation"], f"moveLabware {lw.name}")
        if kind == "slot" and ref not in run.deck.slots:
            raise ProtocolError(f"moveLabware {lw.name}: slot {ref} is not one of the twelve deck slots")
        dest = (kind, ref if kind == "slot" else (run.modules[ref].key if kind == "module" else run.labware[ref].key))
        carried.update([lw.key, *riders(lw.key)])
        parent[lw.key] = dest
        placed.append((lw.key, dest))

    for key, (kind, ref) in placed:
        lw = by_key[key].labware
        if kind == "module":
            mod = run.module_by_key(ref)
            ov = lw.on_module.get(mod.model, (0.0, 0.0, 0.0))
            mod.seat_mm = min(mod.seat_mm, mod.area_mm[2] - ov[2] + lw.offset[2])
        elif kind == "labware":
            below = by_key[ref]
            if below.labware.is_adapter:
                ov = lw.on_labware.get(below.load_name) or lw.on_labware.get("default") or (0.0, 0.0, 0.0)
                seat = below.labware.z - ov[2] - below.labware.offset[2] + lw.offset[2]
                below.height = max(0.0, min(below.height, seat))
    run.carried = [lw.id for lw in run.labware.values() if lw.key in carried]


# ---------------------------------------------------------------- state


@dataclass
class State:
    """What the scene shows at one keyframe. Volumes in uL, positions in deck mm."""

    wells: dict[tuple[str, str], dict[str, float]] = field(default_factory=dict)
    rack: dict[str, set[str]] = field(default_factory=dict)
    mounted: dict[str, list[bool]] = field(default_factory=dict)
    tip_liquid: dict[str, list[dict[str, float]]] = field(default_factory=dict)
    # Segments retain aspirate order.  The last segment is nearest the nozzle
    # outlet, so dispensing consumes it first (air gaps stay air, and liquid
    # never gets re-ordered into a single proportional mixture).
    tip_segments: dict[str, list[list["TipSegment"]]] = field(default_factory=dict)
    tip_air: dict[str, list[float]] = field(default_factory=dict)
    tip_front_air: dict[str, list[float]] = field(default_factory=dict)
    tip_capacity: dict[str, float] = field(default_factory=dict)
    # Liquid intentionally dispensed outside a well: trash/chute or an
    # unmodelled coordinate.  This is part of the replay ledger, not discarded
    # state hidden behind a warning.
    waste: dict[str, dict[str, float]] = field(default_factory=dict)
    # loadLiquid is authoritative inventory.  Empty wells that were never
    # annotated may be treated as unknown legacy inventory once, but an
    # annotated source underflow is a hard protocol error.
    known_inventory: set[tuple[str, str]] = field(default_factory=set)
    assumed_inventory: set[tuple[str, str]] = field(default_factory=set)
    falling: dict[str, float] = field(default_factory=dict)
    origin: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    parent: dict[str, Parent] = field(default_factory=dict)
    # Thermocycler lids that are closed, by module key.
    lid_closed: set[str] = field(default_factory=set)
    # Continuous visual progress, independent of protocol geometry/thermal logic.
    module_lid: dict[str, float] = field(default_factory=dict)
    module_latch: dict[str, float] = field(default_factory=dict)
    held: str | None = None
    # Labware stacked on the held labware (it travels along), and keys the
    # carried stack may touch while it leaves or enters its seat.
    riders: tuple[str, ...] = ()
    seated: tuple[str, ...] = ()
    # Gripper ``pickUpOffset`` of the held labware: jaw centre minus labware centre at grip height.
    grip_off: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def copy(self) -> "State":
        return copy.deepcopy(self)


@dataclass
class TipSegment:
    """One aspirated gas/liquid segment in a Flex tip."""

    liquid: dict[str, float] = field(default_factory=dict)
    air: float = 0.0

    @property
    def volume(self) -> float:
        return self.air + _vol(self.liquid)


def _vol(mix: dict[str, float]) -> float:
    return sum(mix.values())


def _take(mix: dict[str, float], volume: float) -> dict[str, float]:
    """Remove ``volume`` from ``mix`` in proportion; return what was removed."""

    total = _vol(mix)
    if total <= 1e-9:
        return {}
    share = min(1.0, volume / total)
    out = {k: v * share for k, v in mix.items()}
    for k in list(mix):
        mix[k] -= out[k]
        if mix[k] < 1e-9:
            del mix[k]
    return out


def _add(mix: dict[str, float], part: dict[str, float]) -> None:
    for k, v in part.items():
        mix[k] = mix.get(k, 0.0) + v


def _sync_tip(state: State, tool: str, channel: int) -> None:
    """Synchronize display summaries from ordered tip segments."""

    segments = state.tip_segments[tool][channel]
    mix: dict[str, float] = {}
    for segment in segments:
        _add(mix, segment.liquid)
    state.tip_liquid[tool][channel] = mix
    state.tip_air[tool][channel] = sum(segment.air for segment in segments)
    front_air = 0.0
    for segment in reversed(segments):
        if segment.liquid:
            break
        front_air += segment.air
    state.tip_front_air[tool][channel] = front_air


def blend(a: State, b: State, u: float) -> State:
    """Volumes and fall progress move linearly from ``a`` to ``b``; everything else is ``a``'s."""

    if u >= 1.0:
        return b
    out = copy.copy(a)
    wells = {}
    for key in set(a.wells) | set(b.wells):
        ma, mb = a.wells.get(key, {}), b.wells.get(key, {})
        wells[key] = {k: (1 - u) * ma.get(k, 0.0) + u * mb.get(k, 0.0) for k in set(ma) | set(mb)}
    out.wells = wells
    out.tip_liquid = {
        tool: [
            {k: (1 - u) * ma.get(k, 0.0) + u * mb.get(k, 0.0) for k in set(ma) | set(mb)}
            for ma, mb in zip(a.tip_liquid[tool], b.tip_liquid[tool])
        ]
        for tool in a.tip_liquid
    }
    out.tip_air = {
        tool: [(1 - u) * x + u * y for x, y in zip(a.tip_air[tool], b.tip_air[tool])]
        for tool in a.tip_air
    }
    out.tip_front_air = {
        tool: [(1 - u) * x + u * y for x, y in zip(a.tip_front_air[tool], b.tip_front_air[tool])]
        for tool in a.tip_front_air
    }
    out.waste = {
        where: {
            liquid: (1 - u) * a.waste.get(where, {}).get(liquid, 0.0) + u * b.waste.get(where, {}).get(liquid, 0.0)
            for liquid in set(a.waste.get(where, {})) | set(b.waste.get(where, {}))
        }
        for where in set(a.waste) | set(b.waste)
    }
    out.falling = {tool: (1 - u) * a.falling.get(tool, 0.0) + u * b.falling.get(tool, 0.0) for tool in a.falling}
    for field_name in ('module_lid', 'module_latch'):
        va, vb = getattr(a, field_name), getattr(b, field_name)
        setattr(out, field_name, {k: (1-u)*va.get(k, 1.)+u*vb.get(k, 1.) for k in va.keys() | vb.keys()})
    return out


# ---------------------------------------------------------------- plan


@dataclass
class Key:
    """Arrive at ``q`` with ``state`` at time ``t``. ``cmd`` indexes the analysis commands."""

    t: float
    q: dict[str, float]
    state: State
    cmd: int
    phase: str


@dataclass
class Arrival:
    """The keyframe where a positional command's critical point reaches ``result.position``."""

    cmd: int
    key: int
    tool: str
    position_mm: tuple[float, float, float]
    centered: bool
    target: tuple[str, str] | None


@dataclass
class Step:
    """One analysis command on the timeline."""

    cmd: int
    kind: str
    t0: float
    t1: float
    text: str
    detail: str
    slots: tuple[str, ...]
    tool: str | None


@dataclass
class Plan:
    run: ProtocolRun
    joints: tuple[str, ...]
    keys: list[Key]
    arrivals: list[Arrival]
    steps: list[Step]
    warnings: list[str]
    liquid_wells: set[tuple[str, str]]

    @property
    def duration(self) -> float:
        return self.keys[-1].t


def _fmt_ul(volume: float) -> str:
    return f"{volume:g}"


class Planner:
    def __init__(self, run: ProtocolRun) -> None:
        self.run = run
        self.deck = run.deck
        moved_keys = [run.labware[i].key for i in run.carried]
        # Joints that exist in the model: the shared slides, the gripper's, and
        # one Z per mounted pipette. The scene builds only those bodies.
        self.home_tool = next(iter(run.pipettes.values())).tool if run.pipettes else "gripper"
        tool_joints = [t.joint for t in flex_shell.TOOLS if t.body == "gripper" or t.body in {p.tool for p in run.pipettes.values()}]
        self.joints = tuple(dict.fromkeys([*JOINTS_BASE[:2], *tool_joints, *JOINTS_BASE[2:]])) + tuple(
            f"{k}_{a}" for k in moved_keys for a in "xyz"
        )
        self.moved_keys = set(moved_keys)
        self.keys: list[Key] = []
        self.arrivals: list[Arrival] = []
        self.steps: list[Step] = []
        self.warnings: list[str] = []
        self.liquid_wells: set[tuple[str, str]] = set()
        self.module_holds: dict[str, float] = {}
        self.context: dict[str, str | None] = {
            "pipette_1000": None,
            "pipette_8": None,
            "pipette_1000_left": None,
            "pipette_8_right": None,
            "gripper": None,
        }
        self.cmd = -1

        state = State()
        for mod in run.modules.values():
            if mod.model == 'thermocyclerModuleV2':
                state.module_lid[mod.key] = 0.
            elif mod.model == 'absorbanceReaderV1':
                state.module_lid[mod.key] = 1.
            elif mod.model == 'heaterShakerModuleV1':
                state.module_latch[mod.key] = 1.
        for lw in run.labware.values():
            state.parent[lw.key] = lw.parent
            state.origin[lw.key] = run.placement(lw.key, lw.parent, state.origin)
            if lw.labware.is_tiprack:
                state.rack[lw.key] = set(lw.labware.wells)
        for tool, n in CHANNELS.items():
            state.mounted[tool] = [False] * n
            state.tip_liquid[tool] = [{} for _ in range(n)]
            state.tip_segments[tool] = [[] for _ in range(n)]
            state.tip_air[tool] = [0.0] * n
            state.tip_front_air[tool] = [0.0] * n
            state.tip_capacity[tool] = 0.0
            state.falling[tool] = 0.0
        q = {name: 0.0 for name in self.joints}
        home = home_point(self.deck, Z_PARK_MM)
        q.update(self._tool_q(q, self.home_tool, home))
        for t in flex_shell.TOOLS:
            if t.joint in q:
                q[t.joint] = flex_shell.Z_PARK
        q["jaw_f"], q["jaw_b"] = -flex_shell.JAW_OPEN, flex_shell.JAW_OPEN
        for key in moved_keys:
            q.update(self._labware_q(key, state.origin[key]))
        self.keys.append(Key(0.0, q, state, -1, "start"))

    # -- geometry

    @property
    def q(self) -> dict[str, float]:
        return self.keys[-1].q

    @property
    def state(self) -> State:
        return self.keys[-1].state

    def _labware_q(self, key: str, origin_mm) -> dict[str, float]:
        m = robot_m(self.deck, origin_mm)
        return {f"{key}_x": m[0], f"{key}_y": m[1], f"{key}_z": m[2]}

    def _tool_q(self, q: dict[str, float], tool: str, site_mm) -> dict[str, float]:
        spec = flex_shell.TOOL_BY_NAME[tool]
        m = robot_m(self.deck, site_mm)
        return {"x": m[0] - spec.dx, "y": m[1] - spec.dy, spec.joint: m[2] - spec.dz}

    def _site_mm(self, q: dict[str, float], tool: str) -> tuple[float, float, float]:
        spec = flex_shell.TOOL_BY_NAME[tool]
        m = (q["x"] + spec.dx, q["y"] + spec.dy, q[spec.joint] + spec.dz)
        return tuple(m[i] / MM - self.deck.corner[i] for i in range(3))

    def _reach(self, tool: str, state: State) -> float:
        """How far the tool's lowest point hangs below its site, mm."""

        if tool == "gripper":
            if state.held is None:
                return 0.0
            lw = self.run.by_key(state.held).labware
            return lw.grip_z - PADDLE_HALF_MM
        if any(state.mounted[tool]):
            return self._pipette(tool).tip.reach_mm
        return 0.0

    def _pipette(self, tool: str) -> PipetteRun:
        return next(p for p in self.run.pipettes.values() if p.tool == tool)

    def _top(self, key: str, state: State) -> float:
        return state.origin[key][2] + self.run.by_key(key).height

    def _deck_top(self, state: State) -> float:
        aboard = {state.held, *state.riders}
        tops = [self._top(lw.key, state) for lw in self.run.labware.values() if lw.key not in aboard]
        tops += [b.origin_mm[2] + b.size_mm[2] for b in self.run.trash.values()]
        tops += [m.lid_mm if m.key in state.lid_closed else m.top for m in self.run.modules.values()]
        # Chute drop slots sit at 114.5 mm, so the drawn body is just as tall.
        tops += [b.origin_mm[2] + b.size_mm[2] for b in self.run.chutes.values()]
        return max(tops + [0.0])

    def _riders(self, key: str, state: State) -> list[str]:
        """Labware stacked on ``key``, all the way up."""

        out = [k for k, p in state.parent.items() if p == ("labware", key)]
        return out + [r for k in out for r in self._riders(k, state)]

    def _stack_below(self, parent: Parent, state: State) -> list[str]:
        """Labware and module keys under a placement, top down."""

        kind, ref = parent
        if kind == "module":
            return [ref]
        if kind == "labware":
            return [ref, *self._stack_below(state.parent[ref], state)]
        return []

    def base_slot(self, key: str, state: State) -> str:
        kind, ref = state.parent[key]
        if kind == "slot":
            return ref
        if kind == "module":
            return self.run.module_by_key(ref).slot
        return self.base_slot(ref, state)

    def nozzles_mm(self, tool: str, site_mm) -> list[tuple[float, float]]:
        n = CHANNELS.get(tool, 1)
        return [(site_mm[0], site_mm[1] - k * PITCH_MM) for k in range(n)]

    def wells_under(self, tool: str, site_mm, state: State) -> list[tuple[str, str] | None]:
        """For each nozzle, the (labware key, well) whose opening it is over."""

        out: list[tuple[str, str] | None] = []
        stack = sorted(self.run.labware.values(), key=lambda lw: -self._top(lw.key, state))
        for x, y in self.nozzles_mm(tool, site_mm):
            hit = None
            for lw in stack:
                o = state.origin[lw.key]
                for name, well in lw.labware.wells.items():
                    if well.contains(x - o[0], y - o[1], 0.05):
                        hit = (lw.key, name)
                        break
                if hit:
                    break
            out.append(hit)
        return out

    # -- keyframes

    def _push(self, q: dict[str, float], state: State, phase: str, duration: float | None = None) -> int:
        prev = self.q
        if duration is None:
            dxy = math.hypot(q["x"] - prev["x"], q["y"] - prev["y"])
            dz = max((abs(q[j] - prev[j]) for j in ("z", "z_8", "z_left", "z_8_right", "z_gripper") if j in q), default=0.0)
            djaw = max(abs(q["jaw_f"] - prev["jaw_f"]), abs(q["jaw_b"] - prev["jaw_b"]))
            duration = max(MIN_MOVE_S, dxy / V_XY + dz / V_Z + djaw / V_JAW)
        self.keys.append(Key(self.keys[-1].t + duration, dict(q), state, self.cmd, phase))
        return len(self.keys) - 1

    def _move_site(self, tool: str, site_mm, phase: str, state: State | None = None) -> int:
        q = dict(self.q)
        q.update(self._tool_q(q, tool, site_mm))
        st = state if state is not None else self.state
        if st.held is not None and tool == "gripper":
            lw = self.run.by_key(st.held).labware
            off = st.grip_off
            origin = (
                site_mm[0] - lw.x / 2 - off[0],
                site_mm[1] - lw.y / 2 - off[1],
                site_mm[2] - (lw.grip_z - PADDLE_HALF_MM) - off[2],
            )
            q.update(self._labware_q(st.held, origin))
            home = st.origin[st.held]
            for key in st.riders:
                q.update(self._labware_q(key, tuple(origin[i] + st.origin[key][i] - home[i] for i in range(3))))
        return self._push(q, st, phase)

    def _activate(self, tool: str) -> None:
        """Retract every other mounted tool to the top of its stroke before ``tool`` moves."""

        q = dict(self.q)
        changed = False
        for t in flex_shell.TOOLS:
            if t.joint not in q:
                continue
            if t.body != tool and abs(q[t.joint] - flex_shell.Z_PARK) > 1e-9:
                q[t.joint] = flex_shell.Z_PARK
                changed = True
        if changed:
            for other in self.context:
                if other != tool:
                    self.context[other] = None
            self._push(q, self.state, "retract")

    def _travel(self, tool: str, site_mm, dest: str | None) -> int:
        """Up, across, down so the lowest point clears what lies between. Returns the arrival key."""

        self._activate(tool)
        state = self.state
        here = self._site_mm(self.q, tool)
        reach = self._reach(tool, state)
        same = dest is not None and dest == self.context.get(tool)
        if same and dest in {lw.key for lw in self.run.labware.values()}:
            clear = self._top(dest, state) + WITHIN_CLEAR_MM
        else:
            clear = self._deck_top(state) + CROSS_CLEAR_MM
        travel_z = min(max(clear + reach, site_mm[2], here[2]), Z_PARK_MM)
        moved_xy = math.hypot(site_mm[0] - here[0], site_mm[1] - here[1]) > 1e-6
        if moved_xy:
            if here[2] < travel_z - 1e-6:
                self._move_site(tool, (here[0], here[1], travel_z), "rise")
            self._move_site(tool, (site_mm[0], site_mm[1], travel_z), "travel")
        index = self._move_site(tool, site_mm, "descend")
        self.context[tool] = dest
        return index

    def _critical_to_site(self, tool: str, position_mm, centered: bool, with_tip: bool) -> tuple[float, float, float]:
        """Nozzle-A site for a critical point: undo the tip reach and the 8-channel centring."""

        x, y, z = position_mm
        if tool in EIGHT_TOOLS and centered:
            y += CENTER_OFFSET_MM
        if with_tip:
            z += self._pipette(tool).tip.reach_mm
        return (x, y, z)

    # -- commands

    def _pipette_cmd(self, params) -> PipetteRun:
        return self.run.pipettes[params["pipetteId"]]

    def _centered(self, tool: str, labware_id: str | None) -> bool:
        if tool not in EIGHT_TOOLS:
            return False
        if labware_id is None:
            return True
        return "centerMultichannelOnWells" in self.run.labware[labware_id].labware.quirks

    def _arrive_at_well(self, index: int, params, result, with_tip: bool) -> tuple[str, int]:
        pip = self._pipette_cmd(params)
        lw = self.run.labware[params["labwareId"]]
        pos = tuple(float(result["position"][a]) for a in "xyz")
        centered = self._centered(pip.tool, lw.id)
        site = self._critical_to_site(pip.tool, pos, centered, with_tip)
        key = self._travel(pip.tool, site, lw.key)
        self.arrivals.append(Arrival(index, key, pip.tool, pos, centered, (lw.key, params["wellName"])))
        return pip.tool, key

    def _liquid_destination(self, tool: str) -> str:
        location = self.context.get(tool)
        if location in self.run.trash:
            return f"trash:{location}"
        if location in self.run.chutes:
            return f"chute:{location}"
        return "outside_wells"

    def _liquid_step(self, tool: str, volume: float | None, sign: int, phase: str, duration: float) -> None:
        if volume is not None and (not math.isfinite(volume) or volume < 0):
            raise ProtocolError(f"command {self.cmd + 1}: invalid volume {volume}")
        state = self.state.copy()
        site = self._site_mm(self.q, tool)
        wells = self.wells_under(tool, site, state)
        air_channels = 0
        liquid_channels = 0
        for k, well in enumerate(wells):
            if not state.mounted[tool][k]:
                continue
            segments = state.tip_segments[tool][k]
            if sign < 0:
                amount = float(volume or 0.0)
                if sum(segment.volume for segment in segments) + amount > state.tip_capacity[tool] + 1e-6:
                    raise ProtocolError(f"command {self.cmd + 1}: tip {k + 1} capacity exceeded on {tool}")
                tip_end_z = site[2] - self._reach(tool, state)
                above_opening = False
                if well is not None:
                    opening = self.run.by_key(well[0]).labware.wells[well[1]]
                    opening_z = state.origin[well[0]][2] + opening.z + opening.depth
                    above_opening = tip_end_z > opening_z + 1e-6
                if well is None or above_opening or phase in ("airGap", "airGapInPlace"):
                    segments.append(TipSegment(air=amount))
                    air_channels += 1
                    _sync_tip(state, tool, k)
                    continue
                mix = state.wells.setdefault(well, {})
                available = _vol(mix)
                if available + 1e-6 < amount:
                    if well in state.known_inventory:
                        raise ProtocolError(
                            f"command {self.cmd + 1}: {self.run.by_key(well[0]).name} {well[1]} "
                            f"contains {available:g} uL, cannot aspirate {amount:g} uL"
                        )
                    if well not in state.assumed_inventory:
                        state.assumed_inventory.add(well)
                        self.warnings.append(
                            f"command {self.cmd + 1}: {well[0]} {well[1]} holds {available:.1f} uL, asked for {amount:g} uL"
                        )
                    _add(mix, {"__unknown__": max(0.0, amount - available)})
                    self.liquid_wells.add(well)
                segments.append(TipSegment(liquid=_take(mix, amount)))
                liquid_channels += 1
            else:
                remaining = float(volume) if volume is not None else sum(segment.volume for segment in segments)
                part: dict[str, float] = {}
                while remaining > 1e-9 and segments:
                    front = segments[-1]
                    take = min(remaining, front.volume)
                    if front.air > 0:
                        front.air -= take
                    else:
                        _add(part, _take(front.liquid, take))
                    remaining -= take
                    if front.volume < 1e-9:
                        segments.pop()
                if well is not None:
                    lw = self.run.by_key(well[0])
                    capacity = float(lw.definition["wells"][well[1]]["totalLiquidVolume"])
                    if _vol(state.wells.get(well, {})) + _vol(part) > capacity + 1e-6:
                        raise ProtocolError(
                            f"command {self.cmd + 1}: {lw.name} {well[1]} capacity {capacity:g} uL exceeded"
                        )
                    _add(state.wells.setdefault(well, {}), part)
                    self.liquid_wells.add(well)
                elif part:
                    _add(state.waste.setdefault(self._liquid_destination(tool), {}), part)
            _sync_tip(state, tool, k)
        if sign < 0 and air_channels and not liquid_channels:
            phase = "aspirate air"
        self._push(dict(self.q), state, phase, duration)

    def _pick_up(self, index: int, params, result) -> None:
        tool, _ = self._arrive_at_well(index, params, result, with_tip=False)
        pip = self._pipette_cmd(params)
        overlap = pip.tip.length_mm - pip.tip.reach_mm
        site = self._site_mm(self.q, tool)
        state = self.state.copy()
        tip_volume = float(result.get("tipVolume") or pip.name.split("_", 1)[0][1:])
        state.tip_capacity[tool] = min(tip_volume, float(pip.name.split("_", 1)[0][1:]))
        for k, well in enumerate(self.wells_under(tool, site, state)):
            if well is None or well[1] not in state.rack.get(well[0], set()):
                self.warnings.append(f"command {index + 1}: nozzle {k + 1} finds no tip at {well}")
                continue
            state.rack[well[0]].discard(well[1])
            state.mounted[tool][k] = True
            state.tip_segments[tool][k].clear()
            _sync_tip(state, tool, k)
        self._move_site(tool, (site[0], site[1], site[2] - overlap), "press")
        self._push(dict(self.q), state, "seat", 0.18)
        self._move_site(tool, site, "lift")

    def _drop(self, tool: str, return_to: tuple[tuple[str, str], ...] | None = None) -> None:
        state = self.state.copy()
        # Returning to a rack seats the tip at its definition's original pose.
        # Only waste drops use the free-fall/fade animation through empty space.
        state.falling[tool] = 0.0 if return_to else 1.0
        destination = "returned_tip" if return_to else self._liquid_destination(tool)
        for k in range(CHANNELS[tool]):
            _add(state.waste.setdefault(destination, {}), state.tip_liquid[tool][k])
            state.tip_segments[tool][k].clear()
            _sync_tip(state, tool, k)
        self._push(dict(self.q), state, "eject", 0.55)
        after = state.copy()
        after.falling[tool] = 0.0
        after.mounted[tool] = [False] * CHANNELS[tool]
        if return_to:
            for well in return_to:
                after.rack[well[0]].add(well[1])
        self._push(dict(self.q), after, "ejected", 0.01)

    def _dest(self, location, what: str) -> Parent:
        kind, ref = _location(location, what)
        if kind == "module":
            return kind, self.run.modules[ref].key
        if kind == "labware":
            return kind, self.run.labware[ref].key
        return kind, ref

    def _move_labware(self, params) -> None:
        lw = self.run.labware[params["labwareId"]]
        strategy = params.get("strategy")
        dest = self._dest(params["newLocation"], f"moveLabware {lw.name}")
        before = self.state
        riders = tuple(self._riders(lw.key, before))
        new_origin = self.run.placement(lw.key, dest, before.origin)
        old = before.origin[lw.key]
        shift = tuple(new_origin[i] - old[i] for i in range(3))

        def landed(state: State) -> State:
            state.parent[lw.key] = dest
            for key in (lw.key, *riders):
                o = before.origin[key]
                state.origin[key] = tuple(o[i] + shift[i] for i in range(3))
            return state

        if strategy != "usingGripper":
            state = landed(self.state.copy())
            q = dict(self.q)
            for key in (lw.key, *riders):
                q.update(self._labware_q(key, state.origin[key]))
            self._push(q, state, "manual move", 1.2)
            return
        offsets = (lw.definition.get("gripperOffsets") or {}).get("default") or {}
        pick_off = offsets.get("pickUpOffset") or {"x": 0, "y": 0, "z": 0}
        drop_off = offsets.get("dropOffset") or {"x": 0, "y": 0, "z": 0}
        L = lw.labware
        lift = L.grip_z - PADDLE_HALF_MM

        def grip_site(origin, off) -> tuple[float, float, float]:
            return (origin[0] + L.x / 2 + off["x"], origin[1] + L.y / 2 + off["y"], origin[2] + lift + off["z"])

        src = grip_site(old, pick_off)
        dst = grip_site(new_origin, drop_off)
        self._activate("gripper")
        here = self._site_mm(self.q, "gripper")
        if here[2] < Z_PARK_MM - 1e-6:
            self._move_site("gripper", (here[0], here[1], Z_PARK_MM), "rise")
        q = dict(self.q)
        q["jaw_f"], q["jaw_b"] = -flex_shell.JAW_OPEN, flex_shell.JAW_OPEN
        q.update(self._tool_q(q, "gripper", (src[0], src[1], Z_PARK_MM)))
        self._push(q, self.state, "over labware")
        self._move_site("gripper", src, "descend")
        q = dict(self.q)
        q["jaw_f"], q["jaw_b"] = -L.y * MM / 2, L.y * MM / 2
        state = self.state.copy()
        state.held = lw.key
        state.riders = riders
        state.grip_off = (pick_off["x"], pick_off["y"], pick_off["z"])
        state.seated = tuple(self._stack_below(before.parent[lw.key], before) + self._stack_below(dest, before))
        self._push(q, state, "grip")
        self._move_site("gripper", (src[0], src[1], Z_PARK_MM), "lift")
        self._move_site("gripper", (dst[0], dst[1], Z_PARK_MM), "carry")
        self._move_site("gripper", dst, "set down")
        q = dict(self.q)
        q["jaw_f"], q["jaw_b"] = -flex_shell.JAW_OPEN, flex_shell.JAW_OPEN
        state = landed(self.state.copy())
        state.held, state.riders, state.seated, state.grip_off = None, (), (), (0.0, 0.0, 0.0)
        for key in (lw.key, *riders):
            q.update(self._labware_q(key, state.origin[key]))
        self._push(q, state, "release")
        self._move_site("gripper", (dst[0], dst[1], Z_PARK_MM), "clear")
        self.context["gripper"] = None

    def _home(self, axes: list[str] | None = None) -> None:
        if axes is not None:
            if not isinstance(axes, list) or any(not isinstance(axis, str) for axis in axes):
                raise ProtocolError(f"command {self.cmd + 1}: home axes must be a list of axis names")
            unknown = set(axes) - HOME_AXES
            if unknown:
                raise ProtocolError(f"command {self.cmd + 1}: unsupported Flex home axes: {sorted(unknown)}")
            q = dict(self.q)
            selected = set(axes)
            if "x" in selected or "y" in selected:
                home = home_point(self.deck, Z_PARK_MM)
                home_q = self._tool_q(q, self.home_tool, home)
                for axis in ("x", "y"):
                    if axis in selected:
                        q[axis] = home_q[axis]
                for tool in self.context:
                    self.context[tool] = None
            if "leftZ" in selected:
                for tool in ("pipette_8", "pipette_1000_left"):
                    spec = flex_shell.TOOL_BY_NAME[tool]
                    if spec.joint in q:
                        q[spec.joint] = flex_shell.Z_PARK
                        self.context[tool] = None
            if "rightZ" in selected:
                for tool in ("pipette_1000", "pipette_8_right"):
                    spec = flex_shell.TOOL_BY_NAME[tool]
                    if spec.joint in q:
                        q[spec.joint] = flex_shell.Z_PARK
                        self.context[tool] = None
            if "extensionZ" in selected:
                q["z_gripper"] = flex_shell.Z_PARK
                self.context["gripper"] = None
            if "extensionJaw" in selected:
                q["jaw_f"], q["jaw_b"] = -flex_shell.JAW_OPEN, flex_shell.JAW_OPEN
            phase = "axis home" if selected & {"x", "y", "leftZ", "rightZ", "extensionZ", "extensionJaw"} else "plunger home"
            self._push(q, self.state, phase, 0.6)
            return
        q = dict(self.q)
        for t in flex_shell.TOOLS:
            if t.joint in q:
                q[t.joint] = flex_shell.Z_PARK
        self._push(q, self.state, "z home")
        q = dict(self.q)
        q.update(self._tool_q(q, self.home_tool, home_point(self.deck, Z_PARK_MM)))
        self._push(q, self.state, "xy home", None if len(self.keys) > 2 else 0.6)
        for tool in self.context:
            self.context[tool] = None

    def _module_command(self, index: int, kind: str, params) -> None:
        """Apply a supported module action and preserve explicit hold times.

        Temperature ramps remain a visual beat because no thermal calibration is
        part of this offline scene, but command-provided hold/profile seconds
        are real timeline durations and are never replaced by a fixed beat.
        """

        if kind not in SUPPORTED_MODULE_COMMANDS:
            raise ProtocolError(f"command {index + 1}: unsupported Flex module action {kind}")
        mod = self.run.modules.get(params.get("moduleId", ""))
        if mod is None:
            raise ProtocolError(f"command {index + 1}: module {params.get('moduleId')} is not loaded")
        state = self.state
        if kind in ("thermocycler/openLid", "thermocycler/closeLid"):
            state = state.copy()
            (state.lid_closed.add if kind.endswith("closeLid") else state.lid_closed.discard)(mod.key)
            state.module_lid[mod.key] = float(kind.endswith("closeLid"))
        elif kind in ("heaterShaker/openLabwareLatch", "heaterShaker/closeLabwareLatch"):
            state = state.copy()
            state.module_latch[mod.key] = float(kind.endswith("closeLabwareLatch"))
        elif kind in ("absorbanceReader/openLid", "absorbanceReader/closeLid"):
            state = state.copy()
            state.module_lid[mod.key] = float(kind.endswith("closeLid"))

        self._push(dict(self.q), state, "module", 0.6)
        if kind == "thermocycler/setTargetBlockTemperature":
            hold = float(params.get("holdTimeSeconds") or 0.0)
            if not math.isfinite(hold) or hold < 0:
                raise ProtocolError(f"command {index + 1}: invalid temperature hold {hold}")
            self.module_holds[params["moduleId"]] = hold
        elif kind == "thermocycler/waitForBlockTemperature":
            hold = self.module_holds.pop(params["moduleId"], 0.0)
            if hold:
                self._push(dict(self.q), self.state, "thermocycler/holdBlock", hold)
        elif kind in ("thermocycler/runProfile", "thermocycler/runExtendedProfile"):
            for profile_index, profile_step in enumerate(params.get("profile", []), start=1):
                hold = float(profile_step.get("holdSeconds") or 0.0)
                if not math.isfinite(hold) or hold < 0:
                    raise ProtocolError(f"command {index + 1}: invalid profile hold {hold}")
                self._push(dict(self.q), self.state, f"thermocycler/profile/{profile_index}", 0.6)
                if hold:
                    self._push(dict(self.q), self.state, f"thermocycler/holdProfile/{profile_index}", hold)

    def _area(self, index: int, params, result) -> None:
        pip = self._pipette_cmd(params)
        name = params["addressableAreaName"]
        pos = tuple(float(result["position"][a]) for a in "xyz")
        centered = pip.tool in EIGHT_TOOLS
        site = self._critical_to_site(pip.tool, pos, centered, any(self.state.mounted[pip.tool]))
        key = self._travel(pip.tool, site, name)
        self.arrivals.append(Arrival(index, key, pip.tool, pos, centered, None))

    def run_commands(self) -> None:
        for index, cmd in enumerate(self.run.commands):
            self.cmd = index
            kind, params, result = cmd["commandType"], cmd["params"], cmd.get("result") or {}
            start = len(self.keys)
            if kind == "loadLiquid":
                state = self.state.copy()
                lw = self.run.labware[params["labwareId"]]
                for well, volume in params["volumeByWell"].items():
                    if well not in lw.labware.wells:
                        raise ProtocolError(f"command {index + 1}: {lw.name} has no well {well}")
                    capacity = float(lw.definition["wells"][well]["totalLiquidVolume"])
                    volume = float(volume)
                    if not math.isfinite(volume) or volume < 0 or volume > capacity + 1e-6:
                        raise ProtocolError(f"command {index + 1}: invalid initial volume {volume:g} in {lw.name} {well}")
                    if params["liquidId"] not in self.run.liquids:
                        raise ProtocolError(f"command {index + 1}: unknown liquid {params['liquidId']}")
                    state.wells[(lw.key, well)] = {params["liquidId"]: volume}
                    state.known_inventory.add((lw.key, well))
                    self.liquid_wells.add((lw.key, well))
                self._push(dict(self.q), state, "load liquid", 0.01)
            elif kind == "configureNozzleLayout":
                style = params.get("configurationParams", {}).get("style")
                if style != "ALL":
                    raise ProtocolError(f"command {index + 1}: partial nozzle layout {style!r} is not supported by the Flex replay")
            elif kind in NO_MOTION:
                pass
            elif kind == "home":
                self._home(params.get("axes"))
            elif kind == "pickUpTip":
                self._pick_up(index, params, result)
            elif kind in ("aspirate", "dispense", "blowout"):
                pip = self._pipette_cmd(params)
                tool, _ = self._arrive_at_well(index, params, result, with_tip=True)
                volume = params.get("volume")
                dwell = max(0.42, (volume or 0) / max(params.get("flowRate") or 1, 1))
                if kind == "aspirate":
                    self._liquid_step(tool, float(volume), -1, "aspirate", dwell)
                else:
                    self._liquid_step(tool, float(volume) if volume is not None else None, 1, kind, dwell)
            elif kind in ("aspirateInPlace", "dispenseInPlace", "blowOutInPlace"):
                pip = self._pipette_cmd(params)
                volume = params.get("volume")
                sign = -1 if kind == "aspirateInPlace" else 1
                self._liquid_step(pip.tool, float(volume) if volume is not None else None, sign, kind, 0.42)
            elif kind == "moveToWell":
                pip = self._pipette_cmd(params)
                self._arrive_at_well(index, params, result, with_tip=any(self.state.mounted[pip.tool]))
            elif kind == "moveToCoordinates":
                pip = self._pipette_cmd(params)
                raw_position = result.get("position") or params.get("coordinates")
                if not isinstance(raw_position, dict) or any(axis not in raw_position for axis in "xyz"):
                    raise ProtocolError(f"command {index + 1}: moveToCoordinates has no xyz position")
                pos = tuple(float(raw_position[axis]) for axis in "xyz")
                if not all(math.isfinite(value) for value in pos):
                    raise ProtocolError(f"command {index + 1}: moveToCoordinates has non-finite coordinates")
                minimum_z = params.get("minimumZHeight")
                if minimum_z is not None and (not math.isfinite(float(minimum_z)) or float(minimum_z) < 0):
                    raise ProtocolError(f"command {index + 1}: invalid minimumZHeight {minimum_z}")
                site = self._critical_to_site(pip.tool, pos, False, any(self.state.mounted[pip.tool]))
                if params.get("forceDirect"):
                    self._activate(pip.tool)
                    key = self._move_site(pip.tool, site, "direct move")
                    self.context[pip.tool] = None
                else:
                    key = self._travel(pip.tool, site, None)
                self.arrivals.append(Arrival(index, key, pip.tool, pos, False, None))
            elif kind in ("moveToAddressableArea", "moveToAddressableAreaForDropTip"):
                self._area(index, params, result)
            elif kind in ("airGap", "airGapInPlace"):
                pip = self._pipette_cmd(params)
                if "labwareId" in params:
                    self._arrive_at_well(index, params, result, with_tip=True)
                self._liquid_step(pip.tool, float(params["volume"]), -1, kind, 0.3)
            elif kind == "dropTipInPlace":
                self._drop(self._pipette_cmd(params).tool)
            elif kind == "dropTip":
                pip = self._pipette_cmd(params)
                lw = self.run.labware[params["labwareId"]]
                self._arrive_at_well(index, params, result, with_tip=True)
                back = None
                if lw.labware.is_tiprack:
                    site = self._site_mm(self.q, pip.tool)
                    back = tuple(w for w in self.wells_under(pip.tool, site, self.state) if w is not None)
                self._drop(pip.tool, back)
            elif kind == "moveLabware":
                self._move_labware(params)
            elif kind == "waitForDuration":
                seconds = float(params.get("seconds", 0.0))
                if not math.isfinite(seconds) or seconds < 0:
                    raise ProtocolError(f"command {index + 1}: invalid wait duration {seconds}")
                self._push(dict(self.q), self.state, kind, seconds)
            elif kind in ("waitForResume", "comment", "delay"):
                if kind == "waitForResume":
                    self.warnings.append(f"command {index + 1}: manual resume is represented by a pause marker")
                duration = float(params.get("seconds", 0.8)) if kind == "delay" else 0.8
                if not math.isfinite(duration) or duration < 0:
                    raise ProtocolError(f"command {index + 1}: invalid {kind} duration {duration}")
                self._push(dict(self.q), self.state, "pause", duration)
            elif kind == "touchTip":
                # The Flex web scene does not yet model the contact waypoints,
                # but this is a known command with an explicit text-only
                # contract.  It must not fall through the unknown-action error.
                self.warnings.append(f"command {index + 1}: touchTip is shown as text only")
                self._push(dict(self.q), self.state, kind, 0.4)
            elif kind.startswith(MODULE_PREFIXES):
                self._module_command(index, kind, params)
            else:
                raise ProtocolError(f"command {index + 1}: unsupported Flex replay action {kind}")
            if len(self.keys) > start:
                self._record_step(index, kind, params, result, self.keys[start - 1].t, self.keys[-1].t)
        self.cmd = -1
        self._push(dict(self.q), self.state, "done", 1.6)

    # -- captions

    def _well_text(self, tool: str | None, lw: LabwareRun, well: str) -> str:
        if tool == "pipette_8" and not lw.labware.is_tiprack and "centerMultichannelOnWells" in lw.labware.quirks:
            return f"{lw.name} {well} trough (8 channels share it)"
        if tool == "pipette_8":
            return f"{lw.name} column {well[1:]} ({well[0]}{well[1:]}-H{well[1:]})"
        return f"{lw.name} {well}"

    def _record_step(self, index: int, kind: str, params, result, t0: float, t1: float) -> None:
        pip = self.run.pipettes.get(params.get("pipetteId", ""))
        tool = pip.tool if pip else None
        lw = self.run.labware.get(params.get("labwareId", ""))
        mod = self.run.modules.get(params.get("moduleId", ""))
        slots: tuple[str, ...] = ()
        if lw is not None:
            slots = (self._slot_now(lw.key, t0),)
        elif mod is not None:
            slots = (mod.slot,)
        vol = params.get("volume")
        prev = self.run.commands[index - 1] if index > 0 else None
        nxt = self.run.commands[index + 1] if index + 1 < len(self.run.commands) else None

        def same_well(other) -> bool:
            if other is None:
                return False
            p = other["params"]
            return p.get("labwareId") == params.get("labwareId") and p.get("wellName") == params.get("wellName") and p.get("volume") == vol

        mixing = (kind == "aspirate" and nxt is not None and nxt["commandType"] == "dispense" and same_well(nxt)) or (
            kind == "dispense" and prev is not None and prev["commandType"] == "aspirate" and same_well(prev)
        )
        if kind == "home":
            text = "Home"
        elif kind == "pickUpTip":
            text = f"Pick up tip  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "aspirate":
            text = f"{'Mix asp' if mixing else 'Aspirate'} {_fmt_ul(vol)} μL  ←  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "dispense":
            text = f"{'Mix dis' if mixing else 'Dispense'} {_fmt_ul(vol)} μL  →  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "moveToAddressableAreaForDropTip":
            area = params["addressableAreaName"]
            if area in self.run.chutes:
                text = "Move to waste chute"
                slots = ()
            else:
                text = f"Move to trash bin {area.replace('movableTrash', '')}"
                slots = (area.replace("movableTrash", ""),)
        elif kind == "moveToAddressableArea":
            text = f"Move to {params['addressableAreaName']}"
        elif kind == "dropTipInPlace":
            text = "Drop tip"
        elif kind == "dropTip":
            text = f"Return tip to {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "moveLabware":
            src = self.run.where_text(self.state_at_time(t0).parent[lw.key])
            dst = self.run.where_text(self._dest(params["newLocation"], lw.name))
            how = "Gripper carry" if params.get("strategy") == "usingGripper" else "Manual move"
            text = f"{how} {lw.name}: {src} → {dst}"
            slots = (self._slot_now(lw.key, t0), self._slot_now(lw.key, t1))
        elif mod is not None and kind.startswith(MODULE_PREFIXES):
            action = kind.split("/", 1)[1]
            text = f"{mod.label} {mod.slot}: {MODULE_ACTIONS.get(action, action)}"
            if params.get("celsius") is not None:
                text += f" {params['celsius']:g} °C"
            if params.get("rpm") is not None:
                text += f" {params['rpm']:g} rpm"
        elif kind == "loadLiquid":
            liquid = self.run.liquids.get(params["liquidId"])
            wells = list(params["volumeByWell"])
            vols = sorted({v for v in params["volumeByWell"].values()})
            span = wells[0] if len(wells) == 1 else f"{wells[0]}…{wells[-1]} ({len(wells)} wells)"
            text = f"Load liquid {liquid.name if liquid else ''}: {lw.name} {span} {'/'.join(_fmt_ul(v) for v in vols)} μL each"
        else:
            text = kind
        detail = kind
        if pip is not None:
            detail += f" · {pip.name} ({pip.mount})"
        if "position" in result:
            p = result["position"]
            detail += f" · position ({p['x']:.2f}, {p['y']:.2f}, {p['z']:.2f}) mm"
        self.steps.append(Step(index, kind, t0, t1, text, detail, slots, tool))

    def _slot_now(self, key: str, t: float) -> str:
        return self.base_slot(key, self.state_at_time(t))

    def state_at_time(self, t: float) -> State:
        for key in reversed(self.keys):
            if key.t <= t + 1e-9:
                return key.state
        return self.keys[0].state


def plan(run: ProtocolRun) -> Plan:
    planner = Planner(run)
    planner.run_commands()
    return Plan(run, planner.joints, planner.keys, planner.arrivals, planner.steps, planner.warnings, planner.liquid_wells)


def scene_spec(plan_: Plan) -> SceneSpec:
    run = plan_.run
    start = plan_.keys[0].state
    placed = [
        Placed(lw.key, start.origin[lw.key], lw.labware, movable=lw.id in run.carried, label=lw.name, height_mm=lw.height)
        for lw in run.labware.values()
    ]
    tips = {p.tool: p.tip for p in run.pipettes.values() if p.tip is not None}
    tools = tuple(dict.fromkeys(p.tool for p in run.pipettes.values()))
    # Front label from the pipette name: p50 → "50", p1000 → "1000", plus its channel count.
    faces = {p.tool: (p.name.split("_")[0][1:], str(CHANNELS[p.tool])) for p in run.pipettes.values()}
    return SceneSpec(
        placed=placed,
        # Only the bins are boxes to draw; chute areas are drop points covered
        # by the one chute body.
        trash=[b for n, b in run.trash.items() if n not in run.chutes],
        chute=run.chute,
        modules=list(run.modules.values()),
        liquid_wells=set(plan_.liquid_wells),
        tips=tips,
        title=run.title,
        tools=tools,
        faces=faces,
    )


# ---------------------------------------------------------------- sampling


def smooth(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3.0 - 2.0 * u)


def sample(plan_: Plan, t: float) -> tuple[dict[str, float], State, int]:
    """Joint values, scene state and keyframe index (of the segment's end) at time ``t``."""

    keys = plan_.keys
    if t <= 0.0:
        return keys[0].q, keys[0].state, 0
    if t >= keys[-1].t:
        return keys[-1].q, keys[-1].state, len(keys) - 1
    lo, hi = 0, len(keys) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if keys[mid].t < t:
            lo = mid
        else:
            hi = mid
    a, b = keys[hi - 1], keys[hi]
    span = b.t - a.t
    u = smooth((t - a.t) / span) if span > 1e-9 else 1.0
    q = {name: a.q[name] + u * (b.q[name] - a.q[name]) for name in a.q}
    return q, blend(a.state, b.state, u), hi


def step_at(plan_: Plan, t: float) -> Step | None:
    current = None
    for step in plan_.steps:
        if step.kind == "loadLiquid":
            continue
        if step.t0 <= t + 1e-9:
            current = step
    return current
