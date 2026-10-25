"""Turn an ``opentrons analyze`` result into keyframes for the Flex MuJoCo scene.

The analysis JSON is the only input. ``loadLabware`` gives each labware's slot
and full definition, ``loadPipette`` the mounts, ``loadLiquid`` the starting
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

from sim import flex_shell
from sim.flex_scene import (
    DECK_PATH,
    MM,
    PADDLE_HALF_MM,
    Deck,
    Labware,
    Placed,
    SceneSpec,
    TipDims,
    TrashBin,
    home_point,
    labware_from_definition,
    labware_origin,
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

JOINTS_BASE = ("x", "y", "z", "z_8", "z_left", "z_8_right", "z_gripper", "jaw_f", "jaw_b")
NO_MOTION = {
    "loadLabware",
    "loadPipette",
    "loadLiquid",
    "loadModule",
    "loadLiquidClass",
    "configureForVolume",
    "configureNozzleLayout",
    "prepareToAspirate",
    "setRailLights",
    "setStatusBar",
}


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

    def by_key(self, key: str) -> LabwareRun:
        return next(lw for lw in self.labware.values() if lw.key == key)


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


def _slot_of(location: dict) -> str:
    for key in ("slotName", "addressableAreaName"):
        if key in location:
            return location[key]
    raise ProtocolError(f"labware location {location} is not a deck slot (modules, adapters and off-deck are not modelled)")


def load_analysis(path: Path, deck: Deck) -> ProtocolRun:
    raw = json.loads(path.read_text())
    if raw.get("errors"):
        first = raw["errors"][0]
        raise ProtocolError(f"analysis has errors: {first.get('errorType')}: {first.get('detail')}")
    if raw.get("robotType") not in (None, "OT-3 Standard"):
        raise ProtocolError(f"robotType is {raw.get('robotType')}, not a Flex")
    deck_raw = json.loads(DECK_PATH.read_text())
    bins = _trash_bins(deck_raw)

    labware: dict[str, LabwareRun] = {}
    pipettes: dict[str, PipetteRun] = {}
    liquids = {
        item["id"]: LiquidRun(item["id"], item.get("displayName", item["id"]), _hex_rgb(item.get("displayColor", "#3C78D8")))
        for item in raw.get("liquids", [])
    }
    trash: dict[str, TrashBin] = {}
    moved: list[str] = []
    for cmd in raw["commands"]:
        kind, params, result = cmd["commandType"], cmd["params"], cmd.get("result") or {}
        if kind == "loadLabware":
            definition = result["definition"]
            lw = labware_from_definition(definition)
            slot = _slot_of(params["location"])
            if slot not in deck.slots:
                raise ProtocolError(f"slot {slot} is not one of the twelve deck slots")
            run = LabwareRun(
                id=result["labwareId"],
                key=f"lw{len(labware) + 1}",
                load_name=params["loadName"],
                name=params.get("displayName") or definition["metadata"]["displayName"],
                slot=slot,
                labware=lw,
                definition=definition,
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
            elif "Trash" in name or "trash" in name:
                raise ProtocolError(f"{name} is not a trash bin this scene draws")
        elif kind == "moveLabware":
            if params.get("strategy") == "usingGripper" and params["labwareId"] not in moved:
                moved.append(params["labwareId"])
    title = raw.get("metadata", {}).get("protocolName") or path.stem
    return ProtocolRun(path, title, labware, pipettes, liquids, raw["commands"], trash, moved, deck)


# ---------------------------------------------------------------- state


@dataclass
class State:
    """What the scene shows at one keyframe. Volumes in uL, positions in deck mm."""

    wells: dict[tuple[str, str], dict[str, float]] = field(default_factory=dict)
    rack: dict[str, set[str]] = field(default_factory=dict)
    mounted: dict[str, list[bool]] = field(default_factory=dict)
    tip_liquid: dict[str, list[dict[str, float]]] = field(default_factory=dict)
    falling: dict[str, float] = field(default_factory=dict)
    origin: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    held: str | None = None

    def copy(self) -> "State":
        return copy.deepcopy(self)


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
    out.falling = {tool: (1 - u) * a.falling.get(tool, 0.0) + u * b.falling.get(tool, 0.0) for tool in a.falling}
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
        moved_keys = [run.labware[i].key for i in run.moved]
        self.joints = JOINTS_BASE + tuple(f"{k}_{a}" for k in moved_keys for a in "xyz")
        self.moved_keys = set(moved_keys)
        self.keys: list[Key] = []
        self.arrivals: list[Arrival] = []
        self.steps: list[Step] = []
        self.warnings: list[str] = []
        self.liquid_wells: set[tuple[str, str]] = set()
        self.context: dict[str, str | None] = {
            "pipette_1000": None,
            "pipette_8": None,
            "pipette_1000_left": None,
            "pipette_8_right": None,
            "gripper": None,
        }
        self.cmd = -1

        state = State()
        for lw in run.labware.values():
            state.origin[lw.key] = labware_origin(self.deck, lw.slot, lw.labware)
            if lw.labware.is_tiprack:
                state.rack[lw.key] = set(lw.labware.wells)
        for tool, n in CHANNELS.items():
            state.mounted[tool] = [False] * n
            state.tip_liquid[tool] = [{} for _ in range(n)]
            state.falling[tool] = 0.0
        q = {name: 0.0 for name in self.joints}
        home = home_point(self.deck, Z_PARK_MM)
        q.update(self._tool_q(q, "pipette_1000", home))
        for t in flex_shell.TOOLS:
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
        lw = self.run.by_key(key).labware
        return state.origin[key][2] + lw.top

    def _deck_top(self, state: State) -> float:
        tops = [self._top(lw.key, state) for lw in self.run.labware.values() if lw.key != state.held]
        tops += [b.origin_mm[2] + b.size_mm[2] for b in self.run.trash.values()]
        return max(tops + [0.0])

    def nozzles_mm(self, tool: str, site_mm) -> list[tuple[float, float]]:
        n = CHANNELS.get(tool, 1)
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
        prev = self.q
        if duration is None:
            dxy = math.hypot(q["x"] - prev["x"], q["y"] - prev["y"])
            dz = max(abs(q[j] - prev[j]) for j in ("z", "z_8", "z_left", "z_8_right", "z_gripper"))
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
            origin = (site_mm[0] - lw.x / 2, site_mm[1] - lw.y / 2, site_mm[2] - (lw.grip_z - PADDLE_HALF_MM))
            q.update(self._labware_q(st.held, origin))
        return self._push(q, st, phase)

    def _activate(self, tool: str) -> None:
        """Retract every other tool to the top of its stroke before ``tool`` moves."""

        q = dict(self.q)
        changed = False
        for t in flex_shell.TOOLS:
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

    def _liquid_step(self, tool: str, volume: float, sign: int, phase: str, duration: float) -> None:
        state = self.state.copy()
        site = self._site_mm(self.q, tool)
        wells = self.wells_under(tool, site, state)
        for k, well in enumerate(wells):
            if not state.mounted[tool][k]:
                continue
            tip = state.tip_liquid[tool][k]
            if sign < 0:
                if well is None:
                    self.warnings.append(f"command {self.cmd + 1}: nozzle {k + 1} aspirates over no well")
                    continue
                mix = state.wells.setdefault(well, {})
                if _vol(mix) + 1e-6 < volume:
                    self.warnings.append(
                        f"command {self.cmd + 1}: {well[0]} {well[1]} holds {_vol(mix):.1f} uL, asked for {volume:g} uL"
                    )
                _add(tip, _take(mix, volume))
            else:
                part = _take(tip, volume if volume is not None else _vol(tip))
                if well is not None:
                    _add(state.wells.setdefault(well, {}), part)
                    self.liquid_wells.add(well)
        self._push(dict(self.q), state, phase, duration)

    def _pick_up(self, index: int, params, result) -> None:
        tool, _ = self._arrive_at_well(index, params, result, with_tip=False)
        pip = self._pipette_cmd(params)
        overlap = pip.tip.length_mm - pip.tip.reach_mm
        site = self._site_mm(self.q, tool)
        state = self.state.copy()
        for k, well in enumerate(self.wells_under(tool, site, state)):
            if well is None or well[1] not in state.rack.get(well[0], set()):
                self.warnings.append(f"command {index + 1}: nozzle {k + 1} finds no tip at {well}")
                continue
            state.rack[well[0]].discard(well[1])
            state.mounted[tool][k] = True
        self._move_site(tool, (site[0], site[1], site[2] - overlap), "press")
        self._push(dict(self.q), state, "seat", 0.18)
        self._move_site(tool, site, "lift")

    def _drop(self, tool: str, return_to: tuple[str, ...] | None = None) -> None:
        state = self.state.copy()
        state.falling[tool] = 1.0
        for mix in state.tip_liquid[tool]:
            mix.clear()
        self._push(dict(self.q), state, "eject", 0.55)
        after = state.copy()
        after.falling[tool] = 0.0
        after.mounted[tool] = [False] * CHANNELS[tool]
        if return_to:
            for well in return_to:
                after.rack[well[0]].add(well[1])
        self._push(dict(self.q), after, "ejected", 0.01)

    def _move_labware(self, params) -> None:
        lw = self.run.labware[params["labwareId"]]
        strategy = params.get("strategy")
        dest = _slot_of(params["newLocation"]) if isinstance(params["newLocation"], dict) else params["newLocation"]
        if dest not in self.deck.slots:
            raise ProtocolError(f"moveLabware to {params['newLocation']} is not a deck slot")
        new_origin = labware_origin(self.deck, dest, lw.labware)
        if strategy != "usingGripper":
            state = self.state.copy()
            state.origin[lw.key] = new_origin
            self._push(dict(self.q), state, "manual move", 1.2)
            return
        offsets = (lw.definition.get("gripperOffsets") or {}).get("default") or {}
        pick_off = offsets.get("pickUpOffset") or {"x": 0, "y": 0, "z": 0}
        drop_off = offsets.get("dropOffset") or {"x": 0, "y": 0, "z": 0}
        L = lw.labware
        lift = L.grip_z - PADDLE_HALF_MM

        def grip_site(origin, off) -> tuple[float, float, float]:
            return (origin[0] + L.x / 2 + off["x"], origin[1] + L.y / 2 + off["y"], origin[2] + lift + off["z"])

        old = self.state.origin[lw.key]
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
        self._push(q, state, "grip")
        self._move_site("gripper", (src[0], src[1], Z_PARK_MM), "lift")
        self._move_site("gripper", (dst[0], dst[1], Z_PARK_MM), "carry")
        self._move_site("gripper", dst, "set down")
        q = dict(self.q)
        q["jaw_f"], q["jaw_b"] = -flex_shell.JAW_OPEN, flex_shell.JAW_OPEN
        state = self.state.copy()
        state.held = None
        state.origin[lw.key] = new_origin
        q.update(self._labware_q(lw.key, new_origin))
        self._push(q, state, "release")
        self._move_site("gripper", (dst[0], dst[1], Z_PARK_MM), "clear")
        self.context["gripper"] = None

    def _home(self) -> None:
        q = dict(self.q)
        for t in flex_shell.TOOLS:
            q[t.joint] = flex_shell.Z_PARK
        self._push(q, self.state, "z home")
        q = dict(self.q)
        q.update(self._tool_q(q, "pipette_1000", home_point(self.deck, Z_PARK_MM)))
        q["z"] = flex_shell.Z_PARK
        self._push(q, self.state, "xy home", None if len(self.keys) > 2 else 0.6)
        for tool in self.context:
            self.context[tool] = None

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
                    state.wells[(lw.key, well)] = {params["liquidId"]: float(volume)}
                    self.liquid_wells.add((lw.key, well))
                self._push(dict(self.q), state, "load liquid", 0.01)
            elif kind in NO_MOTION:
                pass
            elif kind == "home":
                self._home()
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
            elif kind in ("moveToAddressableArea", "moveToAddressableAreaForDropTip"):
                self._area(index, params, result)
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
            elif kind in ("waitForDuration", "waitForResume", "comment", "delay"):
                self._push(dict(self.q), self.state, "pause", 0.8)
            else:
                self.warnings.append(f"command {index + 1}: {kind} is shown as text only")
                self._push(dict(self.q), self.state, kind, 0.4)
            if len(self.keys) > start:
                self._record_step(index, kind, params, result, self.keys[start - 1].t, self.keys[-1].t)
        self.cmd = -1
        self._push(dict(self.q), self.state, "done", 1.6)

    # -- captions

    def _well_text(self, tool: str | None, lw: LabwareRun, well: str) -> str:
        if tool == "pipette_8" and not lw.labware.is_tiprack and "centerMultichannelOnWells" in lw.labware.quirks:
            return f"{lw.name} {well} 槽 (8 通道同槽)"
        if tool == "pipette_8":
            return f"{lw.name} 第 {well[1:]} 列 ({well[0]}{well[1:]}-H{well[1:]})"
        return f"{lw.name} {well}"

    def _record_step(self, index: int, kind: str, params, result, t0: float, t1: float) -> None:
        pip = self.run.pipettes.get(params.get("pipetteId", ""))
        tool = pip.tool if pip else None
        lw = self.run.labware.get(params.get("labwareId", ""))
        slots: tuple[str, ...] = ()
        if lw is not None:
            slots = (self._slot_now(lw.key, t0),)
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
            text = f"{'混匀·吸' if mixing else '吸液'} {_fmt_ul(vol)} μL  ←  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "dispense":
            text = f"{'混匀·打' if mixing else '分液'} {_fmt_ul(vol)} μL  →  {self._well_text(tool, lw, params['wellName'])}"
        elif kind == "moveToAddressableAreaForDropTip":
            area = params["addressableAreaName"]
            text = f"移到垃圾桶 {area.replace('movableTrash', '')}"
            slots = (area.replace("movableTrash", ""),)
        elif kind == "moveToAddressableArea":
            text = f"移到 {params['addressableAreaName']}"
        elif kind == "dropTipInPlace":
            text = "弃枪头"
        elif kind == "dropTip":
            text = f"弃枪头 → {lw.name if lw else ''}"
        elif kind == "moveLabware":
            src = self._slot_now(lw.key, t0)
            dst = _slot_of(params["newLocation"])
            how = "夹爪搬运" if params.get("strategy") == "usingGripper" else "手动移动"
            text = f"{how} {lw.name}: {src} → {dst}"
            slots = (src, dst)
        elif kind == "loadLiquid":
            liquid = self.run.liquids.get(params["liquidId"])
            wells = list(params["volumeByWell"])
            vols = sorted({v for v in params["volumeByWell"].values()})
            span = wells[0] if len(wells) == 1 else f"{wells[0]}…{wells[-1]} ({len(wells)} 孔)"
            text = f"加载液体 {liquid.name if liquid else ''}: {lw.name} {span} 各 {'/'.join(_fmt_ul(v) for v in vols)} μL"
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
        origin = self.state_at_time(t).origin[key]
        lw = self.run.by_key(key).labware
        for slot in self.deck.slots:
            if all(abs(a - b) < 1e-6 for a, b in zip(labware_origin(self.deck, slot, lw), origin)):
                return slot
        return "?"

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
        Placed(lw.key, start.origin[lw.key], lw.labware, movable=lw.id in run.moved, label=lw.name)
        for lw in run.labware.values()
    ]
    tips = {p.tool: p.tip for p in run.pipettes.values() if p.tip is not None}
    return SceneSpec(
        placed=placed,
        trash=list(run.trash.values()),
        liquid_wells=set(plan_.liquid_wells),
        tips=tips,
        title=run.title,
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
