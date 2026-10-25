"""Turn an OT-2 ``opentrons analyze`` result into keyframes for the OT-2 MuJoCo scene.

The analysis JSON is the only input, same schema the Flex planner reads. On the
OT-2 every positional command also carries ``result.position``: the moving
pipette's critical point in deck millimeters. For a single-channel that is the
nozzle; for an 8-channel it is the back nozzle (row A) over a normal plate, or
the centre of the nozzle column when the labware has the
``centerMultichannelOnWells`` quirk (trough reservoirs), matching how the
engine reports positions.

The two mounts share one gantry: ``x`` and ``y`` place it, and each mounted
pipette has its own Z. The left mount's critical point sits 34 mm left of the
right's (``DEFAULT_MOUNT_OFFSET`` in ``opentrons/config/defaults_ot2.py``);
per-pipette nozzle x offsets of a few mm are ignored, so the parked pipette
may sit that far from its true spot — the active pipette is always exact
because its critical point is anchored on the reported position.

Tips are dropped into the fixed trash (slot 12) with an ``alternateDropLocation``
x the engine rotates through the bin, or returned to their rack. OT-2 apiLevel
analyses can include ``loadLiquid``. Explicit inventories are tracked, including
empty wells. Older protocols without inventory use a clearly warned unknown
source; a known, depleted well is never silently replenished. Aspiration above
the well opening is air, kept separate from liquid in the tip.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from sim.flex_protocol import (
    Arrival,
    Key,
    Plan,
    ProtocolError,
    State as BaseState,
    Step,
    _add,
    _take,
    _vol,
    blend as _base_blend,
    sample as _base_sample,
    smooth,
    step_at,
)
from sim.flex_scene import MM, Deck, Labware, TipDims, labware_from_definition, labware_origin, robot_m
from sim.ot2_scene import DECK_PATH, HEAD_Z_RANGE_M, load_deck, load_module_def, module_top_mm

# Playback speeds (m/s). Faster than a real OT-2 axis so the clip stays short.
V_XY = 0.30
V_Z = 0.15
MIN_MOVE_S = 0.16
# Clearance above the tallest obstacle when crossing between labware, and above
# the current labware when moving inside it.
CROSS_CLEAR_MM = 15.0
WITHIN_CLEAR_MM = 10.0
# Where both tools park: above everything an OT-2 deck holds.
Z_PARK_MM = 150.0
# The left mount's critical point, left of the right mount's, in deck mm.
LEFT_MOUNT_DX_MM = -34.0
# Nozzle pitch of an 8-channel along -y from the back nozzle.
PITCH_MM = 9.0
CENTER_OFFSET_MM = 3.5 * PITCH_MM
NOZZLE_ROWS = tuple("ABCDEFGH")
# An ejected tip drops this far, from the bin rim to just above its floor.
TRASH_FALL_M = 0.034

NO_MOTION = {
    "loadLabware",
    "loadPipette",
    "loadLiquid",
    "configureForVolume",
    "prepareToAspirate",
    "setStatusBar",
}

# Module commands and how long they hold on screen; the ones that move
# hardware (magnets, lid) are animated by the player over that window.
MODULE_BEAT_S = {
    "magneticModule/engage": 0.9,
    "magneticModule/disengage": 0.7,
    "thermocycler/openLid": 1.5,
    "thermocycler/closeLid": 1.4,
    "thermocycler/awaitProfileComplete": 1.2,
}

OT2_PIPETTES = (
    "p10_single", "p50_single", "p300_single", "p1000_single",
    "p10_multi", "p50_multi", "p300_multi",
    "p20_single_gen2", "p300_single_gen2", "p1000_single_gen2",
    "p20_multi_gen2", "p300_multi_gen2",
)

# Opentrons shared-data 8.8.2 default_return_tip_height, all supported tip
# volumes for these models. Most use half a tip; these two are exceptions.
# This reconstructs the engine's default rack return, not a visual guess.
RETURN_TIP_SCALE = {name: (.4 if name == "p300_multi_gen2" else .83 if name == "p1000_single_gen2" else .5)
                    for name in OT2_PIPETTES}


@dataclass
class ToolSpec:
    """One mounted pipette. ``dx`` is the critical point's x off the gantry."""

    tool: str
    mount: str
    joint: str
    dx: float
    channels: int
    model: str = ""  # OT2_PIPETTES name, for the look geoms

    @property
    def is_multi(self) -> bool:
        return self.channels > 1


@dataclass
class LabwareRun:
    id: str
    key: str
    load_name: str
    name: str
    slot: str
    labware: Labware
    definition: dict
    module_id: str | None = None


@dataclass
class ModuleRun:
    """One loaded module. ``child``/``pins`` are module-local mm, set when the
    labware on it loads: the plate footprint (x0, y0, x1, y1, top z) the
    drawing animates around, and the magnet pin positions."""

    id: str
    model: str
    slot: str
    definition: dict
    child: tuple | None = None
    pins: tuple = ()


@dataclass
class PipetteRun:
    id: str
    name: str
    mount: str
    tool: str
    tip: TipDims | None = None

    @property
    def channels(self) -> int:
        return 8 if "multi" in self.name else 1


@dataclass
class LiquidRun:
    id: str
    name: str
    rgb: tuple[float, float, float]


@dataclass
class TrashRun:
    """The fixed trash the deck JSON draws, in the shape Flex trash bins use."""

    name: str
    origin_mm: tuple[float, float, float]
    size_mm: tuple[float, float, float]


@dataclass
class ProtocolRun:
    path: Path
    title: str
    labware: dict[str, LabwareRun]
    pipettes: dict[str, PipetteRun]
    liquids: dict[str, LiquidRun]
    commands: list[dict]
    trash: dict[str, TrashRun]
    deck: Deck
    modules: dict[str, ModuleRun] = field(default_factory=dict)
    layout_warnings: list[str] = field(default_factory=list)

    def by_key(self, key: str) -> LabwareRun:
        return next(lw for lw in self.labware.values() if lw.key == key)


@dataclass
class TipSegment:
    """Aspirated order; the last segment is nearest the nozzle outlet."""

    liquid: dict[str, float] = field(default_factory=dict)
    air: float = 0.0

    @property
    def volume(self) -> float:
        return self.air + _vol(self.liquid)


@dataclass
class State(BaseState):
    """OT-2 gas/liquid and tip-release display state, without changing Flex."""

    tip_segments: dict[str, list[list[TipSegment]]] = field(default_factory=dict)
    tip_air: dict[str, list[float]] = field(default_factory=dict)
    tip_front_air: dict[str, list[float]] = field(default_factory=dict)
    release_mm: dict[str, float] = field(default_factory=dict)
    tip_capacity: dict[str, float] = field(default_factory=dict)
    waste: dict[str, dict[str, float]] = field(default_factory=dict)


def blend(a: State, b: State, u: float) -> State:
    out = _base_blend(a, b, u)
    if u >= 1.0:
        return out
    for attr in ("tip_air", "tip_front_air"):
        aa, bb = getattr(a, attr, {}), getattr(b, attr, {})
        setattr(out, attr, {tool: [(1-u)*x+u*y for x,y in zip(aa[tool],bb[tool])] for tool in aa})
    # A release uses its own destination distance from its first frame. Rack
    # returns must not inherit the waste-bin fall distance.
    out.release_mm = dict(b.release_mm)
    out.waste = {where: {liquid: (1-u)*a.waste.get(where, {}).get(liquid, 0.) + u*b.waste.get(where, {}).get(liquid, 0.)
                         for liquid in set(a.waste.get(where, {})) | set(b.waste.get(where, {}))}
                 for where in set(a.waste) | set(b.waste)}
    return out


def sample(plan_: Plan, t: float) -> tuple[dict[str, float], State, int]:
    q, state, index = _base_sample(plan_, t)
    if 0 < t < plan_.duration:
        a, b = plan_.keys[index-1], plan_.keys[index]
        span = b.t-a.t
        state = blend(a.state, b.state, smooth((t-a.t)/span) if span > 1e-9 else 1.0)
    return q, state, index


def _hex_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _slot_of(location: dict) -> str:
    for key in ("slotName", "addressableAreaName"):
        if key in location:
            return location[key]
    raise ProtocolError(f"labware location {location} is not a deck slot")


def _area_offset(mod: ModuleRun) -> tuple[float, float, float]:
    """The module's labware-area origin in module-local mm: ``labwareOffset``
    pushed through ``slotTransforms["ot2_standard"][slot]`` when the model has
    one (magnetic/temperature V2 in the left column of slots)."""

    d = mod.definition
    off = d["labwareOffset"]
    v = [float(off["x"]), float(off["y"]), float(off["z"])]
    xform = ((d.get("slotTransforms") or {}).get("ot2_standard") or {}).get(mod.slot, {}).get("labwareOffset")
    if xform:
        v = [sum(float(xform[i][j]) * v[j] for j in range(3)) + float(xform[i][3]) for i in range(3)]
    return (v[0], v[1], v[2])


def module_labware_origin(deck: Deck, mod: ModuleRun, labware: Labware) -> tuple[float, float, float]:
    """Front-left-bottom of a labware on a module, deck millimetres.

    Matches the engine's stackup math (protocol_engine
    ``labware_origin_math/stackup_origin_to_labware_origin.py``): slot origin +
    the transformed labwareOffset + the labware's own corner offset. A
    thermocycler on the OT-2 additionally drops the legacy
    ``_OFFSET_ON_TC_OT2`` = Point(0, 0, 10.7).
    """

    o = _area_offset(mod)
    slot = deck.slots[mod.slot]
    out = [slot[i] + o[i] + labware.offset[i] for i in range(3)]
    if mod.model.startswith("thermocycler"):
        out[2] -= 10.7
    return (out[0], out[1], out[2])


def module_body_origin(deck: Deck, mod: ModuleRun) -> tuple[float, float, float]:
    """Deck-mm coordinates of the module body's local (0, 0, 0) origin."""

    corner = mod.definition["cornerOffsetFromSlot"]
    slot = deck.slots[mod.slot]
    return (slot[0] + float(corner["x"]), slot[1] + float(corner["y"]), slot[2] + float(corner["z"]))


def load_analysis(path: Path, deck: Deck) -> ProtocolRun:
    raw = json.loads(path.read_text())
    if raw.get("errors"):
        first = raw["errors"][0]
        raise ProtocolError(f"analysis has errors: {first.get('errorType')}: {first.get('detail')}")
    if raw.get("robotType") not in (None, "OT-2 Standard"):
        raise ProtocolError(f"robotType is {raw.get('robotType')}, not an OT-2")
    trash_box = deck.trash
    trash = {"fixedTrash": TrashRun("fixedTrash", trash_box.origin, trash_box.size)}

    labware: dict[str, LabwareRun] = {}
    pipettes: dict[str, PipetteRun] = {}
    modules: dict[str, ModuleRun] = {}
    liquids = {
        item["id"]: LiquidRun(item["id"], item.get("displayName", item["id"]), _hex_rgb(item.get("displayColor", "#3C78D8")))
        for item in raw.get("liquids", [])
    }
    # Older analyses may omit liquid loading; unknown sources have a separate
    # colour and warning instead of being confused with explicit inventories.
    liquids["assumed"] = LiquidRun("assumed", "未知源", (0.5, 0.5, 0.5))
    for cmd in raw["commands"]:
        kind, params, result = cmd["commandType"], cmd["params"], cmd.get("result") or {}
        if kind == "loadModule":
            model, slot = params["model"], params["location"]["slotName"]
            if slot not in deck.slots:
                raise ProtocolError(f"slot {slot} is not one of the deck slots")
            try:
                definition = load_module_def(model)
            except FileNotFoundError:
                raise ProtocolError(f"{model} is not a module this scene knows (magnetic V1/V2, temperature V1/V2, thermocycler V1)")
            modules[result["moduleId"]] = ModuleRun(result["moduleId"], model, slot, definition)
        elif kind == "loadLabware":
            definition = result["definition"]
            lw = labware_from_definition(definition)
            module_id = params["location"].get("moduleId")
            if module_id is not None:
                if module_id not in modules:
                    raise ProtocolError(f"labware on unknown module {module_id}")
                slot = modules[module_id].slot
            else:
                slot = _slot_of(params["location"])
            if slot not in deck.slots:
                raise ProtocolError(f"slot {slot} is not one of the deck slots")
            run = LabwareRun(
                id=result["labwareId"],
                key=f"lw{len(labware) + 1}",
                load_name=params["loadName"],
                # The bundled font has no micro sign; the Greek mu it does have
                # reads the same.
                name=(params.get("displayName") or definition["metadata"]["displayName"]).replace("µ", "μ"),
                slot=slot,
                labware=lw,
                definition=definition,
                module_id=module_id,
            )
            labware[run.id] = run
            if module_id is not None:
                mod = modules[module_id]
                area = _area_offset(mod)
                # labwareOffset is relative to the deck slot, whereas the
                # visible module body starts at cornerOffsetFromSlot. Store
                # drawing/pin coordinates in that body's local frame. The
                # authoritative labware origin/command targets stay unchanged.
                corner = mod.definition["cornerOffsetFromSlot"]
                child_origin = tuple(area[i] + lw.offset[i] - float(corner[axis]) for i, axis in enumerate(("x", "y", "z")))
                mod.child = (
                    child_origin[0], child_origin[1],
                    child_origin[0] + lw.x, child_origin[1] + lw.y,
                    child_origin[2] - (10.7 if mod.model.startswith("thermocycler") else 0.0) + lw.z,
                )
                if mod.model.startswith("magnetic") and lw.wells:
                    # One pin per plate column, centred between the outer rows;
                    # the definitions carry no pin layout.
                    xs = sorted({round(w.x, 3) for w in lw.wells.values()})
                    ys = [w.y for w in lw.wells.values()]
                    ymid = (min(ys) + max(ys)) / 2
                    mod.pins = tuple((child_origin[0] + x, child_origin[1] + ymid) for x in xs)
        elif kind == "loadPipette":
            name, mount = params["pipetteName"], params["mount"]
            if name not in OT2_PIPETTES:
                raise ProtocolError(
                    f"{name} on the {mount} mount is not an OT-2 pipette this scene knows. "
                    f"Supported: {', '.join(OT2_PIPETTES)}."
                )
            if mount not in ("left", "right"):
                raise ProtocolError(f"mount {mount} is not left or right")
            pipettes[result["pipetteId"]] = PipetteRun(result["pipetteId"], name, mount, f"pipette_{mount}")
        elif kind == "pickUpTip":
            pip = pipettes[params["pipetteId"]]
            rack = labware[params["labwareId"]].labware
            dims = TipDims(float(result["tipLength"]), rack.tip_length, float(result.get("tipDiameter") or 2 * rack.wells["A1"].radius))
            if pip.tip is not None and abs(pip.tip.reach_mm - dims.reach_mm) > 1e-6:
                raise ProtocolError(f"{pip.name} uses tips of two lengths; the scene mounts one")
            pip.tip = dims
    title = raw.get("metadata", {}).get("protocolName") or path.stem
    run = ProtocolRun(path, title, labware, pipettes, liquids, raw["commands"], trash, deck, modules)
    run.layout_warnings = _check_static_layout(run)
    return run


def _check_static_layout(run: ProtocolRun) -> list[str]:
    """Report overlapping definition envelopes; a module may support its child.

    This checks the supplied definition boxes, not detailed surface clearance
    or an open lid's swept volume. It also catches invalid hand-edited analyses
    that bypass the official analyzer's deck-conflict checks. These coarse
    boxes can include empty space, so overlap is a review warning rather than
    proof of surface collision.
    """
    bodies = []
    for mod in run.modules.values():
        lo = module_body_origin(run.deck, mod)
        dims = mod.definition["dimensions"]
        size = (dims["xDimension"], dims["yDimension"], dims["bareOverallHeight"])
        bodies.append((f"{mod.model} in slot {mod.slot}", mod.id, lo, tuple(lo[i] + size[i] for i in range(3))))
    for lw in run.labware.values():
        origin = (module_labware_origin(run.deck, run.modules[lw.module_id], lw.labware)
                  if lw.module_id else labware_origin(run.deck, lw.slot, lw.labware))
        size = (lw.labware.x, lw.labware.y, lw.labware.top)
        bodies.append((f"{lw.name} in slot {lw.slot}", lw.module_id or lw.id, origin,
                       tuple(origin[i] + size[i] for i in range(3))))
    warnings = []
    for i, (name, parent, lo, hi) in enumerate(bodies):
        for other, other_parent, other_lo, other_hi in bodies[i + 1:]:
            overlap = tuple(min(hi[a], other_hi[a]) - max(lo[a], other_lo[a]) for a in range(3))
            if parent != other_parent and min(overlap) > 1.0:
                warnings.append(f"Layout review required: definition envelopes of {name} and {other} overlap ({' x '.join(f'{v:g}' for v in overlap)} mm); detailed static fit is not verified")
    return warnings


# ---------------------------------------------------------------- plan


@dataclass
class Placed:
    key: str
    origin: tuple[float, float, float]
    labware: Labware
    label: str


@dataclass
class ModulePlaced:
    """One module for the scene builder. ``origin`` is module-local (0, 0, 0)
    in deck millimetres; geoms are named ``{prefix}_<part>`` so the clearance
    sweep can pick every module part up as an obstacle."""

    prefix: str
    model: str
    slot: str
    origin: tuple[float, float, float]
    definition: dict
    child: tuple | None = None
    pins: tuple = ()


@dataclass
class SceneSpec:
    placed: list[Placed]
    trash: list[TrashRun]
    liquid_wells: set[tuple[str, str]]
    tips: dict[str, TipDims]
    mounts: list[ToolSpec]
    title: str
    modules: list[ModulePlaced] = field(default_factory=list)


def _fmt_ul(volume: float) -> str:
    return f"{volume:g}"


class Planner:
    def __init__(self, run: ProtocolRun) -> None:
        self.run = run
        self.deck = run.deck
        self.tools = {
            spec.tool: spec
            for spec in (
                ToolSpec(
                    tool=pip.tool,
                    mount=pip.mount,
                    joint=f"z_{pip.mount}",
                    dx=0.0 if pip.mount == "right" else LEFT_MOUNT_DX_MM,
                    channels=pip.channels,
                    model=pip.name,
                )
                for pip in run.pipettes.values()
            )
        }
        self.joints = ("x", "y") + tuple(spec.joint for spec in sorted(self.tools.values(), key=lambda s: s.mount))
        self.keys: list[Key] = []
        self.arrivals: list[Arrival] = []
        self.steps: list[Step] = []
        self.warnings: list[str] = list(run.layout_warnings)
        self.liquid_wells: set[tuple[str, str]] = set()
        self.assumed: set[tuple[str, str]] = set()
        self.known_inventory: set[tuple[str, str]] = set()
        self.context: dict[str, str | None] = {tool: None for tool in self.tools}
        self.module_holds: dict[str, float] = {}
        self.cmd = -1
        # Park above fixed/closed module bodies. An upright thermocycler lid
        # is taller than the Z stroke, so clear its XY sweep before lid motion.
        max_reach = max((p.tip.reach_mm for p in run.pipettes.values() if p.tip), default=0.)
        labware_top = max((
            (module_labware_origin(self.deck, run.modules[lw.module_id], lw.labware)
             if lw.module_id else labware_origin(self.deck, lw.slot, lw.labware))[2] + lw.labware.top
            for lw in run.labware.values()
        ), default=0.)
        self.z_park = max(
            Z_PARK_MM,
            labware_top + max_reach + CROSS_CLEAR_MM,
            max((module_top_mm(m.definition) for m in run.modules.values()), default=0.0)
            + max(80., max_reach + CROSS_CLEAR_MM),
        )
        park_z_m = robot_m(self.deck, (0.0, 0.0, self.z_park))[2]
        if not HEAD_Z_RANGE_M[0] <= park_z_m <= HEAD_Z_RANGE_M[1]:
            raise ProtocolError(
                f"module clearance requires nozzle park Z {park_z_m * 1000:.1f} mm; "
                f"OT-2 model Z range is {HEAD_Z_RANGE_M[0] * 1000:.1f}..{HEAD_Z_RANGE_M[1] * 1000:.1f} mm"
            )

        state = State()
        for lw in run.labware.values():
            if lw.module_id is not None:
                state.origin[lw.key] = module_labware_origin(self.deck, run.modules[lw.module_id], lw.labware)
            else:
                state.origin[lw.key] = labware_origin(self.deck, lw.slot, lw.labware)
            if lw.labware.is_tiprack:
                state.rack[lw.key] = set(lw.labware.wells)
        for tool in self.tools:
            n = self.tools[tool].channels
            state.mounted[tool] = [False] * n
            state.tip_liquid[tool] = [{} for _ in range(n)]
            state.tip_segments[tool] = [[] for _ in range(n)]
            state.tip_air[tool] = [0.0] * n
            state.tip_front_air[tool] = [0.0] * n
            state.release_mm[tool] = TRASH_FALL_M * 1000
            state.falling[tool] = 0.0
        q = {name: 0.0 for name in self.joints}
        home = self._home_point()
        if self.tools:
            q.update(self._tool_q(q, next(iter(self.tools)), home))
        else:
            point = robot_m(self.deck, home)
            q.update(x=point[0], y=point[1])
        for spec in self.tools.values():
            q[spec.joint] = robot_m(self.deck, (0.0, 0.0, self.z_park))[2]
        self.keys.append(Key(0.0, q, state, -1, "start"))

    # -- geometry

    @property
    def q(self) -> dict[str, float]:
        return self.keys[-1].q

    @property
    def state(self) -> State:
        return self.keys[-1].state

    def _home_point(self) -> tuple[float, float, float]:
        # Deck.dimensions is the whole robot footprint, not the reachable
        # slot grid. The previous use of that depth parked the head beyond
        # the rear wall once the official CAD axes were corrected.
        last_row = max(p[1] for name, p in self.deck.slots.items() if name.isdigit())
        return (self.deck.size[0] / 2, last_row + self.deck.slot_size[1] + WITHIN_CLEAR_MM, self.z_park)

    def _tool_q(self, q: dict[str, float], tool: str, site_mm) -> dict[str, float]:
        spec = self.tools[tool]
        m = robot_m(self.deck, site_mm)
        return {"x": m[0] - spec.dx * MM, "y": m[1], spec.joint: m[2]}

    def _site_mm(self, q: dict[str, float], tool: str) -> tuple[float, float, float]:
        spec = self.tools[tool]
        m = (q["x"] + spec.dx * MM, q["y"], q[spec.joint])
        return tuple(m[i] / MM - self.deck.corner[i] for i in range(3))

    def _reach(self, tool: str, state: State) -> float:
        """How far the tool's lowest point hangs below its nozzle, mm."""

        if any(state.mounted[tool]):
            return self._pipette(tool).tip.reach_mm
        return 0.0

    def _pipette(self, tool: str) -> PipetteRun:
        return next(p for p in self.run.pipettes.values() if p.tool == tool)

    def _top(self, key: str, state: State) -> float:
        lw = self.run.by_key(key).labware
        return state.origin[key][2] + lw.top

    def _deck_top(self, state: State) -> float:
        tops = [self._top(lw.key, state) for lw in self.run.labware.values()]
        tops += [b.origin_mm[2] + b.size_mm[2] for b in self.run.trash.values()]
        tops += [module_top_mm(m.definition) for m in self.run.modules.values()]
        return max(tops + [0.0])

    def nozzles_mm(self, tool: str, site_mm) -> list[tuple[float, float]]:
        n = self.tools[tool].channels
        return [(site_mm[0], site_mm[1] - k * PITCH_MM) for k in range(n)]

    def wells_under(self, tool: str, site_mm, state: State) -> list[tuple[str, str] | None]:
        """For each nozzle, the (labware key, well) whose opening it is over."""

        out: list[tuple[str, str] | None] = []
        for x, y in self.nozzles_mm(tool, site_mm):
            hit = None
            for lw in self.run.labware.values():
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
        for name, value in q.items():
            if not math.isfinite(value):
                raise ProtocolError(f"command {self.cmd + 1}: non-finite {name} position")
            if name.startswith("z_") and not HEAD_Z_RANGE_M[0] <= value <= HEAD_Z_RANGE_M[1]:
                raise ProtocolError(f"command {self.cmd + 1}: {name} {value * 1000:g} mm is outside the OT-2 model travel")
        prev = self.q
        if duration is None:
            dxy = math.hypot(q["x"] - prev["x"], q["y"] - prev["y"])
            dz = max((abs(q[j] - prev[j]) for j in self.joints if j.startswith("z_")), default=0.)
            duration = max(MIN_MOVE_S, dxy / V_XY + dz / V_Z)
        self.keys.append(Key(self.keys[-1].t + duration, dict(q), state, self.cmd, phase))
        return len(self.keys) - 1

    def _move_site(self, tool: str, site_mm, phase: str, state: State | None = None) -> int:
        q = dict(self.q)
        q.update(self._tool_q(q, tool, site_mm))
        return self._push(q, state if state is not None else self.state, phase)

    def _activate(self, tool: str) -> None:
        """Park every other tool at the top of its stroke before ``tool`` moves."""

        q = dict(self.q)
        changed = False
        park = robot_m(self.deck, (0.0, 0.0, self.z_park))[2]
        for other, spec in self.tools.items():
            if other != tool and abs(q[spec.joint] - park) > 1e-9:
                q[spec.joint] = park
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
        travel_z = min(max(clear + reach, site_mm[2], here[2]), self.z_park)
        moved_xy = math.hypot(site_mm[0] - here[0], site_mm[1] - here[1]) > 1e-6
        if moved_xy:
            if here[2] < travel_z - 1e-6:
                self._move_site(tool, (here[0], here[1], travel_z), "rise")
            self._move_site(tool, (site_mm[0], site_mm[1], travel_z), "travel")
        index = self._move_site(tool, site_mm, "descend")
        self.context[tool] = dest
        return index

    def _critical_to_site(self, tool: str, position_mm, centered: bool, with_tip: bool) -> tuple[float, float, float]:
        """Back-nozzle site for a critical point: undo the tip reach and the column centring."""

        x, y, z = position_mm
        if self.tools[tool].is_multi and centered:
            y += CENTER_OFFSET_MM
        if with_tip:
            z += self._pipette(tool).tip.reach_mm
        return (x, y, z)

    # -- commands

    def _pipette_cmd(self, params) -> PipetteRun:
        return self.run.pipettes[params["pipetteId"]]

    def _centered(self, tool: str, labware_id: str | None) -> bool:
        if not self.tools[tool].is_multi:
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

    def _arrive_at_trash(self, index: int, params, result) -> tuple[str, int]:
        """Reach the fixed-trash drop point. The engine rotates ``alternateDropLocation``
        through the bin, so the JSON position is taken as-is and the definition
        check is skipped (``Arrival.target`` None marks the trash)."""

        pip = self._pipette_cmd(params)
        pos = tuple(float(result["position"][a]) for a in "xyz")
        centered = self._centered(pip.tool, None)
        site = self._critical_to_site(pip.tool, pos, centered, any(self.state.mounted[pip.tool]))
        key = self._travel(pip.tool, site, "fixedTrash")
        self.arrivals.append(Arrival(index, key, pip.tool, pos, centered, None))
        return pip.tool, key

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
                amount = float(volume or 0.)
                if sum(x.volume for x in segments) + amount > state.tip_capacity[tool] + 1e-6:
                    raise ProtocolError(f"command {self.cmd + 1}: tip {k + 1} capacity exceeded on {tool}")
                z = site[2] - self._reach(tool, state)
                if well is not None:
                    opening = self.run.by_key(well[0]).labware.wells[well[1]]
                    opening_z = state.origin[well[0]][2] + opening.z + opening.depth
                    above_opening = z > opening_z + 1e-6
                else:
                    above_opening = False
                if well is None or above_opening or phase in ("airGap", "airGapInPlace"):
                    segments.append(TipSegment(air=amount))
                    air_channels += 1
                    self._sync_tip(state, tool, k)
                    continue
                mix = state.wells.setdefault(well, {})
                if _vol(mix) + 1e-6 < volume:
                    where = well
                    if where in self.known_inventory:
                        raise ProtocolError(
                            f"command {self.cmd + 1}: {self.run.by_key(well[0]).name} {well[1]} "
                            f"contains {_vol(mix):g} uL, cannot aspirate {volume:g} uL"
                        )
                    if where not in self.assumed:
                        self.assumed.add(where)
                        self.warnings.append(
                            f"command {self.cmd + 1}: {self.run.by_key(well[0]).name} {well[1]} content unknown "
                            f"(no initial inventory supplied); treating it as an unknown source"
                        )
                    _add(mix, {"assumed": max(0., volume - _vol(mix))})
                    self.liquid_wells.add(well)
                segments.append(TipSegment(liquid=_take(mix, amount)))
                liquid_channels += 1
            else:
                remaining = float(volume) if volume is not None else sum(x.volume for x in segments)
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
                    capacity = float(lw.definition['wells'][well[1]]['totalLiquidVolume'])
                    if _vol(state.wells.get(well, {})) + _vol(part) > capacity + 1e-6:
                        raise ProtocolError(f"command {self.cmd + 1}: {lw.name} {well[1]} capacity {capacity:g} uL exceeded")
                    _add(state.wells.setdefault(well, {}), part)
                    self.liquid_wells.add(well)
                    # A deposit does not establish how much buffer was in a
                    # previously unannotated well. Only loadLiquid makes its
                    # initial inventory authoritative (legacy protocols often
                    # start with prefilled wells but omit that annotation).
                elif part:
                    destination = "fixedTrash" if self.context.get(tool) == "fixedTrash" else "outside_wells"
                    _add(state.waste.setdefault(destination, {}), part)
            self._sync_tip(state, tool, k)
        if sign < 0 and air_channels and not liquid_channels:
            phase = "aspirate air"
        self._push(dict(self.q), state, phase, duration)

    @staticmethod
    def _sync_tip(state: State, tool: str, k: int) -> None:
        segments = state.tip_segments[tool][k]
        mix: dict[str, float] = {}
        for segment in segments:
            _add(mix, segment.liquid)
        state.tip_liquid[tool][k] = mix
        state.tip_air[tool][k] = sum(x.air for x in segments)
        front_air = 0.
        for segment in reversed(segments):
            if segment.liquid:
                break
            front_air += segment.air
        state.tip_front_air[tool][k] = front_air

    def _pick_up(self, index: int, params, result) -> None:
        tool, _ = self._arrive_at_well(index, params, result, with_tip=False)
        pip = self._pipette_cmd(params)
        overlap = pip.tip.length_mm - pip.tip.reach_mm
        site = self._site_mm(self.q, tool)
        state = self.state.copy()
        state.tip_capacity[tool] = min(float(result["tipVolume"]), float(pip.name.split('_', 1)[0][1:]))
        for k, well in enumerate(self.wells_under(tool, site, state)):
            if well is None or well[1] not in state.rack.get(well[0], set()):
                self.warnings.append(f"command {index + 1}: nozzle {k + 1} finds no tip at {well}")
                continue
            state.rack[well[0]].discard(well[1])
            state.mounted[tool][k] = True
        self._move_site(tool, (site[0], site[1], site[2] - overlap), "press")
        self._push(dict(self.q), state, "seat", 0.18)
        self._move_site(tool, site, "lift")

    def _drop(self, tool: str, return_to: tuple[tuple[str, str], ...] | None = None) -> None:
        state = self.state.copy()
        state.release_mm[tool] = TRASH_FALL_M * 1000
        if return_to:
            key, name = return_to[0]
            lw = self.run.by_key(key).labware
            w = lw.wells[name]
            rack_end = state.origin[key][2] + w.z + w.depth - lw.tip_length
            held_end = self._site_mm(self.q, tool)[2] - self._reach(tool, state)
            state.release_mm[tool] = max(0., held_end-rack_end)
        state.falling[tool] = 1.0
        for k in range(self.tools[tool].channels):
            destination = (f"returned_tip:{return_to[k][0]}/{return_to[k][1]}" if return_to and k < len(return_to)
                           else "discarded_tip")
            _add(state.waste.setdefault(destination, {}), state.tip_liquid[tool][k])
            state.tip_segments[tool][k].clear()
            self._sync_tip(state, tool, k)
        self._push(dict(self.q), state, "return tip" if return_to else "eject", 0.55)
        after = state.copy()
        after.falling[tool] = 0.0
        after.mounted[tool] = [False] * self.tools[tool].channels
        if return_to:
            for well in return_to:
                after.rack[well[0]].add(well[1])
        self._push(dict(self.q), after, "ejected", 0.01)

    def _touch_tip(self, index: int, params, result) -> None:
        """Engine 8.8 edge waypoints, not an invented circular orbit."""
        pip = self._pipette_cmd(params)
        lw = self.run.labware[params["labwareId"]]
        if lw.labware.is_tiprack or "touchTipDisabled" in lw.labware.quirks:
            raise ProtocolError(f"command {index + 1}: touchTip is disabled for {lw.name}")
        radius = float(params.get("radius", 1.))
        inset = params.get("mmFromEdge")
        if radius != 1. and inset is not None:
            raise ProtocolError(f"command {index + 1}: touchTip radius and mmFromEdge are incompatible")
        inset = float(inset or 0.)
        speed = float(params.get("speed", 60.))
        if not all(math.isfinite(x) for x in (radius, inset, speed)) or speed <= 0:
            raise ProtocolError(f"command {index + 1}: invalid touchTip parameters")
        tool, _ = self._arrive_at_well(index, params, result, with_tip=True)
        center = self._site_mm(self.q, tool)
        well = lw.labware.wells[params["wellName"]]
        rx = (well.size_x/2 if well.shape == "rectangular" else well.radius)*radius-inset
        ry = (well.size_y/2 if well.shape == "rectangular" else well.radius)*radius-inset
        points = {"right": (rx, 0.), "left": (-rx, 0.), "center": (0., 0.),
                  "forward": (0., ry), "back": (0., -ry)}
        slot = int(lw.slot)
        col = (slot-1) % 3
        neighbor = slot-1 if pip.mount == 'right' and col > 0 else slot+1 if pip.mount == 'left' and col < 2 else None
        adjacent_module = any(int(m.slot) == neighbor for m in self.run.modules.values())
        ordering = lw.definition['ordering']
        if pip.mount == 'right' and params['wellName'] in ordering[0] and (adjacent_module or col == 2):
            path = ('left', 'center', 'forward', 'back', 'center')
        elif pip.mount == 'left' and params['wellName'] in ordering[-1] and adjacent_module:
            path = ('right', 'center', 'forward', 'back', 'center')
        else:
            path = ('right', 'left', 'center', 'forward', 'back', 'center')
        for edge in path:
            dx, dy = points[edge]
            target = (center[0]+dx, center[1]+dy, center[2])
            here = self._site_mm(self.q, tool)
            duration = max(.01, math.dist(here, target)/speed)
            q = dict(self.q)
            q.update(self._tool_q(q, tool, target))
            self._push(q, self.state, f"touch {edge}", duration)

    def _module_cmd(self, kind: str, params) -> None:
        """A module command. The lid sweeps across the deck and the magnets
        rise into the plate, so the tools park first; the beat that follows is
        the window the player animates the module over."""

        if kind not in {
            "magneticModule/engage", "magneticModule/disengage",
            "temperatureModule/setTargetTemperature", "temperatureModule/waitForTemperature", "temperatureModule/deactivate",
            "thermocycler/openLid", "thermocycler/closeLid", "thermocycler/setTargetLidTemperature",
            "thermocycler/setTargetBlockTemperature", "thermocycler/waitForLidTemperature", "thermocycler/waitForBlockTemperature",
            "thermocycler/deactivateLid", "thermocycler/deactivateBlock", "thermocycler/runProfile", "thermocycler/awaitProfileComplete",
        }:
            raise ProtocolError(f"command {self.cmd + 1}: {kind} is not supported by the OT-2 replay")
        if kind in ("thermocycler/openLid", "thermocycler/closeLid", "magneticModule/engage"):
            q = dict(self.q)
            park = robot_m(self.deck, (0.0, 0.0, self.z_park))[2]
            if any(abs(q[s.joint] - park) > 1e-9 for s in self.tools.values()):
                for s in self.tools.values():
                    q[s.joint] = park
                self._push(q, self.state, "retract")
            if kind.startswith("thermocycler/") and self.tools:
                q = dict(self.q)
                home = self._tool_q(q, next(iter(self.tools)), self._home_point())
                q.update(x=home["x"], y=home["y"])
                if any(abs(q[axis] - self.q[axis]) > 1e-9 for axis in ("x", "y")):
                    self._push(q, self.state, "clear thermocycler")
                for tool in self.context:
                    self.context[tool] = None
        module_id = params.get("moduleId")
        if kind == "thermocycler/setTargetBlockTemperature":
            hold = float(params.get("holdTimeSeconds") or 0.)
            if not math.isfinite(hold) or hold < 0:
                raise ProtocolError(f"command {self.cmd + 1}: invalid temperature hold {hold}")
            self.module_holds[module_id] = hold
        self._push(dict(self.q), self.state, kind, MODULE_BEAT_S.get(kind, 0.6))
        if kind == "thermocycler/waitForBlockTemperature":
            hold = self.module_holds.pop(module_id, 0.)
            if hold:
                self._push(dict(self.q), self.state, "thermocycler/holdBlock", hold)
        elif kind == "thermocycler/runProfile":
            # The engine analysis expands repetitions into this ordered
            # profile. Preserve every explicit hold; heat/cool ramp times
            # are not measured by offline analysis and remain a visual beat.
            for i, step in enumerate(params.get("profile", [])):
                hold = float(step.get("holdSeconds") or 0.)
                if not math.isfinite(hold) or hold < 0:
                    raise ProtocolError(f"command {self.cmd + 1}: invalid profile hold {hold}")
                self._push(dict(self.q), self.state, f"thermocycler/profile/{i + 1}/{step['celsius']:g}C", .6)
                if hold:
                    self._push(dict(self.q), self.state, f"thermocycler/holdProfile/{i + 1}", hold)

    def _home(self, axes: list[str] | None = None) -> None:
        q = dict(self.q)
        park = robot_m(self.deck, (0.0, 0.0, self.z_park))[2]
        if axes is not None:
            unknown = set(axes) - {"x", "y", "leftZ", "rightZ", "leftPlunger", "rightPlunger"}
            if unknown:
                raise ProtocolError(f"unsupported OT-2 home axes: {sorted(unknown)}")
            for tool, spec in self.tools.items():
                if f"{spec.mount}Z" in axes:
                    q[spec.joint] = park
                    self.context[tool] = None
            if "x" in axes or "y" in axes:
                home = self._tool_q(q, next(iter(self.tools)), self._home_point()) if self.tools else dict(zip(("x", "y"), robot_m(self.deck, self._home_point())[:2]))
                for axis in ("x", "y"):
                    if axis in axes:
                        q[axis] = home[axis]
                for tool in self.context:
                    self.context[tool] = None
            phase = "axis home" if any(axis in axes for axis in ("x", "y", "leftZ", "rightZ")) else "plunger home"
            self._push(q, self.state, phase, .6)
            return
        for spec in self.tools.values():
            q[spec.joint] = park
        self._push(q, self.state, "z home")
        q = dict(self.q)
        if self.tools:
            q.update(self._tool_q(q, next(iter(self.tools)), self._home_point()))
        else:
            point = robot_m(self.deck, self._home_point())
            q.update(x=point[0], y=point[1])
        self._push(q, self.state, "xy home", None if len(self.keys) > 2 else 0.6)
        for tool in self.context:
            self.context[tool] = None

    def run_commands(self) -> None:
        for index, cmd in enumerate(self.run.commands):
            self.cmd = index
            kind, params, result = cmd["commandType"], cmd["params"], cmd.get("result") or {}
            start = len(self.keys)
            if kind == "loadLiquid":
                state = self.state.copy()
                lw = self.run.labware[params["labwareId"]]
                for well, volume in params["volumeByWell"].items():
                    capacity = float(lw.definition['wells'][well]['totalLiquidVolume'])
                    if not math.isfinite(volume) or volume < 0 or volume > capacity + 1e-6:
                        raise ProtocolError(f"command {index + 1}: invalid initial volume {volume} in {lw.name} {well}")
                    state.wells[(lw.key, well)] = {params["liquidId"]: float(volume)}
                    self.liquid_wells.add((lw.key, well))
                    self.known_inventory.add((lw.key, well))
                self._push(dict(self.q), state, "load liquid", 0.01)
            elif kind == "loadModule":
                self._push(dict(self.q), self.state, "load module", 0.5)
            elif kind == "setTipState":
                lw = self.run.labware[params["labwareId"]]
                names = set(params["wellNames"])
                status = params["tipWellState"]
                if not lw.labware.is_tiprack or not names <= set(lw.labware.wells) or status not in ("clean", "used", "empty"):
                    raise ProtocolError(f"command {index + 1}: unsupported tip rack state update")
                state = self.state.copy()
                if status == "empty":
                    state.rack[lw.key].difference_update(names)
                else:
                    state.rack[lw.key].update(names)
                if status == "clean":
                    self.warnings.append(f"command {index + 1}: tip rack reset assumes the indicated tips were supplied manually")
                self._push(dict(self.q), state, "tip rack update", .6)
            elif kind.startswith(("magneticModule/", "temperatureModule/", "thermocycler/")):
                self._module_cmd(kind, params)
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
                pos = tuple(float(result["position"][axis]) for axis in "xyz")
                site = self._critical_to_site(pip.tool, pos, False, any(self.state.mounted[pip.tool]))
                if params.get("forceDirect"):
                    self._activate(pip.tool)
                    key = self._move_site(pip.tool, site, "direct move")
                    self.context[pip.tool] = None
                else:
                    key = self._travel(pip.tool, site, None)
                self.arrivals.append(Arrival(index, key, pip.tool, pos, False, None))
            elif kind in ("moveToAddressableArea", "moveToAddressableAreaForDropTip"):
                if params.get("addressableAreaName") != "fixedTrash":
                    raise ProtocolError(f"command {index + 1}: unsupported addressable area {params.get('addressableAreaName')}")
                self._arrive_at_trash(index, params, result)
            elif kind == "dropTipInPlace":
                self._drop(self._pipette_cmd(params).tool)
            elif kind == "dropTip":
                pip = self._pipette_cmd(params)
                lw = self.run.labware.get(params["labwareId"])
                if lw is None:
                    self._arrive_at_trash(index, params, result)
                else:
                    self._arrive_at_well(index, params, result, with_tip=True)
                back = None
                if lw is not None and lw.labware.is_tiprack:
                    site = self._site_mm(self.q, pip.tool)
                    back = tuple(w for w in self.wells_under(pip.tool, site, self.state) if w is not None)
                self._drop(pip.tool, back)
            elif kind == "touchTip":
                self._touch_tip(index, params, result)
            elif kind in ("airGap", "airGapInPlace"):
                pip = self._pipette_cmd(params)
                if "labwareId" in params:
                    self._arrive_at_well(index, params, result, with_tip=True)
                self._liquid_step(pip.tool, float(params["volume"]), -1, kind, .3)
            elif kind == "waitForDuration":
                seconds = float(params.get("seconds", 0.))
                if not math.isfinite(seconds) or seconds < 0:
                    raise ProtocolError(f"command {index + 1}: invalid wait duration {seconds}")
                self._push(dict(self.q), self.state, kind, seconds)
            elif kind in ("waitForResume", "comment", "delay", "pause"):
                if kind in ("waitForResume", "pause"):
                    self.warnings.append(f"command {index + 1}: manual resume is represented by a pause marker")
                self._push(dict(self.q), self.state, "pause", 0.8)
            else:
                raise ProtocolError(f"command {index + 1}: {kind} is not supported by the OT-2 replay")
            if len(self.keys) > start:
                self._record_step(index, kind, params, result, self.keys[start - 1].t, self.keys[-1].t)
        self.cmd = -1
        self._push(dict(self.q), self.state, "done", 1.6)

    # -- captions

    def _well_text(self, tool: str | None, lw: LabwareRun, well: str) -> str:
        if tool is not None and self.tools[tool].is_multi and not lw.labware.is_tiprack and "centerMultichannelOnWells" in lw.labware.quirks:
            return f"{lw.name} {well} 槽 (8 通道整槽)"
        if tool is not None and self.tools[tool].is_multi:
            return f"{lw.name} 第 {well[1:]} 列 ({well[0]}{well[1:]}-H{well[1:]})"
        return f"{lw.name} {well}"

    # -- captions

    ZH_MODULE = {"magnetic": "磁力模块", "temperature": "温控模块", "thermocycler": "热循环仪"}

    def _module_text(self, mod: ModuleRun) -> str:
        family = mod.model.split("Module")[0]
        return f"{self.ZH_MODULE.get(family, mod.model)}·{mod.model[-2:]} ({mod.slot} 槽)"

    def _module_caption(self, kind: str, mod: ModuleRun, params) -> str:
        name = self._module_text(mod)
        c = params.get("celsius")
        temp = f"{c:g}°C" if c is not None else "目标温度"
        plain = {
            "magneticModule/disengage": "降下磁芯",
            "temperatureModule/setTargetTemperature": f"设定 {temp}",
            "temperatureModule/waitForTemperature": f"等待达到 {temp}",
            "temperatureModule/deactivate": "停止控温",
            "thermocycler/openLid": "打开热盖",
            "thermocycler/closeLid": "关上热盖",
            "thermocycler/setTargetLidTemperature": f"热盖 → {temp}",
            "thermocycler/setTargetBlockTemperature": f"模块 → {temp}",
            "thermocycler/waitForLidTemperature": "等待热盖到位",
            "thermocycler/waitForBlockTemperature": f"等待达到 {temp}",
            "thermocycler/deactivateLid": "热盖停止加热",
            "thermocycler/deactivateBlock": "模块停止控温",
            "thermocycler/runProfile": "运行温度程序",
            "thermocycler/awaitProfileComplete": "等待程序完成",
        }
        text = plain.get(kind, kind.split("/", 1)[1])
        if kind == "magneticModule/engage":
            text = f"升起磁芯 {params.get('height', 0):g} mm"
        return f"{name} {text}"

    def _record_step(self, index: int, kind: str, params, result, t0: float, t1: float) -> None:
        pip = self.run.pipettes.get(params.get("pipetteId", ""))
        tool = pip.tool if pip else None
        lw = self.run.labware.get(params.get("labwareId", ""))
        mod = self.run.modules.get(params.get("moduleId") or result.get("moduleId") or "")
        slots: tuple[str, ...] = ()
        if lw is not None:
            slots = (lw.slot,)
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
            text = "回原点 (home)"
        elif kind == "pickUpTip":
            text = f"取枪头  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "aspirate":
            action = "吸入空气" if self.keys[-1].phase == "aspirate air" else '混匀·吸' if mixing else '吸液'
            text = f"{action} {_fmt_ul(vol)} μL  ←  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "dispense":
            text = f"{'混匀·打' if mixing else '分液'} {_fmt_ul(vol)} μL  →  {self._well_text(tool, lw, params['wellName'])}"
        elif kind in ("airGap", "airGapInPlace"):
            text = f"吸入空气 {_fmt_ul(vol)} μL"
        elif kind in ("aspirateInPlace", "dispenseInPlace", "blowOutInPlace"):
            action = "吸入空气" if self.keys[-1].phase == "aspirate air" else {"aspirateInPlace": "原位吸液", "dispenseInPlace": "原位分液", "blowOutInPlace": "原位吹出"}[kind]
            text = action + (f" {_fmt_ul(vol)} μL" if vol is not None else "")
        elif kind == "moveToCoordinates":
            text = "移动到指定坐标"
        elif kind == "dropTipInPlace":
            text = "弃枪头"
        elif kind == "dropTip":
            trash = lw is None or lw.id == "fixedTrash"
            action = "返回枪头" if lw is not None and lw.labware.is_tiprack else "弃枪头"
            text = f"{action} → {'垃圾桶' if trash else lw.name}"
            slots = ("12",) if trash else (lw.slot,)
        elif kind == "loadLiquid":
            liquid = self.run.liquids.get(params["liquidId"])
            wells = list(params["volumeByWell"])
            vols = sorted({v for v in params["volumeByWell"].values()})
            span = wells[0] if len(wells) == 1 else f"{wells[0]}…{wells[-1]} ({len(wells)} 孔)"
            text = f"加载液体 {liquid.name if liquid else ''}: {lw.name} {span} 各 {'/'.join(_fmt_ul(v) for v in vols)} μL"
        elif kind == "setTipState":
            text = "更新枪头架状态"
        elif mod is not None and kind == "loadModule":
            text = f"装载模块 {self._module_text(mod)}"
        elif mod is not None:
            text = self._module_caption(kind, mod, params)
        else:
            text = kind
        detail = kind
        if pip is not None:
            detail += f" · {pip.name} ({pip.mount})"
        if mod is not None:
            detail += f" · {mod.model}"
        if "position" in result:
            p = result["position"]
            detail += f" · position ({p['x']:.2f}, {p['y']:.2f}, {p['z']:.2f}) mm"
        self.steps.append(Step(index, kind, t0, t1, text, detail, slots, tool))

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
        Placed(lw.key, start.origin[lw.key], lw.labware, lw.name)
        for lw in run.labware.values()
    ]
    tools = {}
    for pip in run.pipettes.values():
        channels = 8 if "multi" in pip.name else 1
        tools[pip.tool] = ToolSpec(
            tool=pip.tool,
            mount=pip.mount,
            joint=f"z_{pip.mount}",
            dx=0.0 if pip.mount == "right" else LEFT_MOUNT_DX_MM,
            channels=channels,
            model=pip.name,
        )
    tips = {p.tool: p.tip for p in run.pipettes.values() if p.tip is not None}
    modules = [
        ModulePlaced(
            prefix=f"mod_{mod.slot}_{mod.model}",
            model=mod.model,
            slot=mod.slot,
            origin=module_body_origin(run.deck, mod),
            definition=mod.definition,
            child=mod.child,
            pins=mod.pins,
        )
        for mod in run.modules.values()
    ]
    return SceneSpec(
        placed=placed,
        trash=list(run.trash.values()),
        liquid_wells=set(plan_.liquid_wells),
        tips=tips,
        mounts=sorted(tools.values(), key=lambda s: s.mount),
        title=run.title,
        modules=modules,
    )
