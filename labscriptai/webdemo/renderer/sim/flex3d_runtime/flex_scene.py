"""Flex (OT-3) scene in the official deck frame.

Cutout and well numbers come from the Opentrons JSON in ``cad/``.
``opentrons analyze`` reports positions in deck millimeters (cutout D1 at the
origin). The scene adds ``cornerOffsetFromOrigin`` to them and uses meters.

There is no official Flex robot STEP. The skeleton is slide joints: ``y``
moves the crossbar (body ``bridge``), ``x`` moves the slider (body
``carriage``), and each mounted tool has its own Z (``z`` on ``head`` is the
1000 uL tip, ``z_8``, ``z_gripper``). ``jaw_f`` and ``jaw_b`` open the
gripper along y. Labware the gripper moves hangs on ``<key>_x`` ``<key>_y``
``<key>_z`` (the demo plate is ``plate``), whose value is its front-left-bottom.
The machine's look comes from ``flex_shell.py``; this module draws the labware
(dark tip rack body with lathed tips, clear plates and reservoirs with liquid
columns, trash bins) and sets cameras and render quality.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import flex_shell
from .flex_module_assets import module_xml

# Package root is the containing Flex runtime project (``virtual-lab`` here,
# ``automation/flex3d`` when this namespace is packaged into LabScript-AI).
# FLEX3D_ROOT makes the asset location explicit for an installed/relocated
# runtime while keeping the repository checkout self-contained by default.
_ROOT_OVERRIDE = os.environ.get("FLEX3D_ROOT")
ROOT = Path(_ROOT_OVERRIDE).expanduser().resolve() if _ROOT_OVERRIDE else Path(__file__).resolve().parents[2]
DECK_PATH = ROOT / "cad" / "flex" / "deck" / "ot3_standard.json"
MODULE_DIR = ROOT / "cad" / "flex" / "modules"
# Deck-JSON cutout fixture that seats each module model and provides its addressable area.
MODULE_FIXTURES = {
    "heaterShakerModuleV1": "heaterShakerModuleV1",
    "temperatureModuleV2": "temperatureModuleV2",
    "magneticBlockV1": "magneticBlockV1",
    "thermocyclerModuleV2": "thermocyclerModuleV2Front",
    "absorbanceReaderV1": "absorbanceReaderV1",
}
# Border of module housing drawn round the labware interface, mm at most.
MODULE_MARGIN_MM = 4.0


def resolve_export() -> Path:
    """Where runs go. Default is the plugin data dir (gitignored); FLEX3D_EXPORT overrides."""

    override = os.environ.get("FLEX3D_EXPORT")
    if override:
        return Path(override)
    return Path(os.environ.get("PLUGIN_DATA", ROOT / "exports")) / "flex3d"


EXPORT = resolve_export()
ASSETS = EXPORT / "flex_assets"

# Height of the crossbar centre above the deck plane.
RAIL_Z_M = flex_shell.RAIL_Z_M
MM = 0.001
PADDLE_HALF_MM = 4.0


@dataclass(frozen=True)
class Well:
    """``radius`` is half the diameter for round wells and half the shorter side for rectangular ones."""

    x: float
    y: float
    z: float
    depth: float
    radius: float
    shape: str = "circular"
    size_x: float = 0.0
    size_y: float = 0.0
    # Inner tube profile: (radius, height from well bottom), millimeters; visual only.
    profile: tuple[tuple[float, float], ...] = ()

    def contains(self, dx: float, dy: float, slack: float = 0.0) -> bool:
        """Is (dx, dy) from the labware origin inside this well's opening?"""

        if self.shape == "rectangular":
            return abs(dx - self.x) <= self.size_x / 2 + slack and abs(dy - self.y) <= self.size_y / 2 + slack
        return (dx - self.x) ** 2 + (dy - self.y) ** 2 <= (self.radius + slack) ** 2

    def area_mm2(self) -> float:
        if self.shape == "rectangular":
            return self.size_x * self.size_y
        return float(np.pi * self.radius**2)


@dataclass(frozen=True)
class Labware:
    load_name: str
    x: float
    y: float
    z: float
    offset: tuple[float, float, float]
    wells: dict[str, Well]
    grip_z: float = 0.0
    is_tiprack: bool = False
    tip_length: float = 0.0
    quirks: tuple[str, ...] = ()
    is_adapter: bool = False
    # ``stackingOffsetWithLabware`` / ``stackingOffsetWithModule``: how far this
    # labware sinks into a parent, by parent load name or module model.
    on_labware: dict[str, tuple[float, float, float]] = field(default_factory=dict, compare=False)
    on_module: dict[str, tuple[float, float, float]] = field(default_factory=dict, compare=False)
    is_tuberack: bool = False

    @property
    def top(self) -> float:
        """Highest point above the labware bottom: the tip tops for a rack."""

        return max([self.z] + [w.z + w.depth for w in self.wells.values()])


@dataclass(frozen=True)
class Deck:
    corner: tuple[float, float, float]
    size: tuple[float, float, float]
    slots: dict[str, tuple[float, float, float]]
    slot_size: tuple[float, float]


@dataclass(frozen=True)
class Pose:
    """One sampled target for one tool. ``command`` uses LogicPass / analyze names.

    ``deck_mm`` is where ``tool``'s site goes (the tip, the 8-channel nozzle A, the
    gripper paddle bottom). The other tools sit raised at ``flex_shell.Z_PARK``.
    ``jaw`` is the half-gap between paddle inner faces, in meters; None leaves
    the jaws open. ``plate_mm`` is the plate's front-left-bottom in deck
    millimeters; None leaves it on its home slot.
    """

    command: str
    where: str
    deck_mm: tuple[float, float, float]
    tool: str = "pipette_1000"
    jaw: float | None = None
    plate_mm: tuple[float, float, float] | None = None


def load_deck(path: Path = DECK_PATH) -> Deck:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cutouts = {item["id"]: tuple(item["position"]) for item in raw["locations"]["cutouts"]}
    slots: dict[str, tuple[float, float, float]] = {}
    # Prefer the standard single-slot fixtures so each of D1–A3 maps once.
    for fixture in raw["cutoutFixtures"]:
        if fixture["id"] not in {"singleLeftSlot", "singleCenterSlot", "singleRightSlot"}:
            continue
        for cutout_id, areas in fixture["providesAddressableAreas"].items():
            for area in areas:
                slots[area] = cutouts[cutout_id]
    boxes = {
        (area["boundingBox"]["xDimension"], area["boundingBox"]["yDimension"])
        for area in raw["locations"]["addressableAreas"]
        if area["id"] in slots
    }
    if len(boxes) != 1:
        raise ValueError(f"slot sizes differ in {path.name}: {boxes}")
    return Deck(
        corner=tuple(raw["cornerOffsetFromOrigin"]),
        size=tuple(raw["dimensions"]),
        slots=slots,
        slot_size=boxes.pop(),
    )


def _tube_profile(raw: dict, geometries: dict) -> tuple[tuple[float, float], ...]:
    """Use the definition's inner profile, aligned to its authoritative well depth."""
    points = {}
    for section in geometries.get(raw.get("geometryDefinitionId"), {}).get("sections", []):
        bottom, top = section.get("bottomHeight", 0), section.get("topHeight", 0)
        if section.get("shape") == "conical":
            points[bottom] = section["bottomDiameter"] / 2
            points[top] = section["topDiameter"] / 2
        elif section.get("shape") == "spherical":
            radius = section["radiusOfCurvature"]
            for height in np.linspace(bottom, top, 5):
                points[float(height)] = float(np.sqrt(max(0, 2 * radius * height - height * height)))
    if len(points) < 2 or max(points) <= 0:
        return ()
    scale = raw["depth"] / max(points)
    return tuple((float(radius), float(height) * scale) for height, radius in sorted(points.items()))


def _well(raw: dict, geometries: dict | None = None) -> Well:
    if raw.get("shape") == "rectangular":
        sx, sy = float(raw["xDimension"]), float(raw["yDimension"])
        return Well(float(raw["x"]), float(raw["y"]), float(raw["z"]), float(raw["depth"]), min(sx, sy) / 2, "rectangular", sx, sy)
    d = float(raw.get("diameter", 6.0))
    return Well(float(raw["x"]), float(raw["y"]), float(raw["z"]), float(raw["depth"]), d / 2, "circular", d, d, _tube_profile(raw, geometries or {}))


def labware_from_definition(raw: dict) -> Labware:
    """Labware from an Opentrons definition dict (a JSON file, or ``loadLabware.result.definition``)."""

    dims = raw["dimensions"]
    corner = raw["cornerOffsetFromSlot"]
    params = raw["parameters"]

    def offsets(table: dict | None) -> dict[str, tuple[float, float, float]]:
        return {name: (float(v["x"]), float(v["y"]), float(v["z"])) for name, v in (table or {}).items()}

    return Labware(
        load_name=params["loadName"],
        x=float(dims["xDimension"]),
        y=float(dims["yDimension"]),
        z=float(dims["zDimension"]),
        offset=(float(corner["x"]), float(corner["y"]), float(corner["z"])),
        wells={name: _well(well, raw.get("innerLabwareGeometry") if raw.get("metadata", {}).get("displayCategory") == "tubeRack" else None) for name, well in raw["wells"].items()},
        grip_z=float(raw.get("gripHeightFromLabwareBottom") or 0.0),
        is_tiprack=bool(params.get("isTiprack")),
        tip_length=float(params.get("tipLength") or 0.0),
        quirks=tuple(params.get("quirks") or ()),
        is_adapter="adapter" in (raw.get("allowedRoles") or ()),
        is_tuberack=raw.get("metadata", {}).get("displayCategory") == "tubeRack",
        on_labware=offsets(raw.get("stackingOffsetWithLabware")),
        on_module=offsets(raw.get("stackingOffsetWithModule")),
    )


def load_labware(path: Path) -> Labware:
    return labware_from_definition(json.loads(path.read_text(encoding="utf-8")))


@dataclass
class Module:
    """A Flex module, placed by the deck JSON fixture that seats it.

    Flex modules sit in caddies below the deck; above it show the labware
    interface and a narrow border. ``area_mm`` is the front-left-bottom of the
    module's addressable area: where labware on the module is placed before its
    ``stackingOffsetWithModule``. ``seat_mm`` is the top of the drawn body (the
    lowest bottom of labware ever set on it); ``rim_mm`` the fixture height, the
    top of the housing round the labware; ``lid_mm`` the closed-lid top, 0 when
    the module has no lid this scene draws.
    """

    key: str
    model: str
    module_type: str
    slot: str
    area: str
    area_mm: tuple[float, float, float]
    interface: tuple[float, float]
    margin: tuple[float, float]
    rim_mm: float
    seat_mm: float
    lid_mm: float = 0.0
    label: str = ""

    @property
    def has_rim(self) -> bool:
        """A housing wall rises round the labware. The thermocycler's housing is its lid."""

        return not self.lid_mm and self.rim_mm > self.seat_mm + 1.0

    @property
    def top(self) -> float:
        """Top of the module with its lid open, deck mm."""

        return self.rim_mm if self.has_rim else self.seat_mm


def module_definition(model: str) -> dict:
    path = MODULE_DIR / f"{model}.json"
    if model not in MODULE_FIXTURES or not path.is_file():
        raise KeyError(model)
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(model: str, slot: str, key: str, label: str = "", deck_path: Path = DECK_PATH) -> Module:
    """``model`` loaded in deck ``slot`` (``loadModule.params``), from the module and deck JSON."""

    definition = module_definition(model)
    raw = json.loads(deck_path.read_text(encoding="utf-8"))
    cutouts = {c["id"]: c["position"] for c in raw["locations"]["cutouts"]}
    areas = {a["id"]: a for a in raw["locations"]["addressableAreas"]}
    fixture = next(f for f in raw["cutoutFixtures"] if f["id"] == MODULE_FIXTURES[model])
    cutout = f"cutout{slot}"
    provided = fixture["providesAddressableAreas"].get(cutout)
    if not provided:
        raise ValueError(f"{model} cannot be loaded in {slot}")
    area = areas[provided[0]]
    off = area["offsetFromCutoutFixture"]
    origin = tuple(float(cutouts[cutout][i] + off[i]) for i in range(3))
    dims = definition["dimensions"]
    ix = float(dims.get("labwareInterfaceXDimension") or area["boundingBox"]["xDimension"])
    iy = float(dims.get("labwareInterfaceYDimension") or area["boundingBox"]["yDimension"])
    margin = (
        min(MODULE_MARGIN_MM, max(0.0, (float(dims["xDimension"]) - ix) / 2)),
        min(MODULE_MARGIN_MM, max(0.0, (float(dims["yDimension"]) - iy) / 2)),
    )
    rim = float(fixture.get("height") or origin[2])
    return Module(
        key=key,
        model=model,
        module_type=definition["moduleType"],
        slot=slot,
        area=area["id"],
        area_mm=origin,
        interface=(ix, iy),
        margin=margin,
        rim_mm=rim,
        seat_mm=origin[2],
        lid_mm=rim if model == "thermocyclerModuleV2" else 0.0,
        label=label or definition.get("displayName", model),
    )


def robot_m(deck: Deck, deck_mm: tuple[float, float, float]) -> tuple[float, float, float]:
    """Deck millimeters plus ``cornerOffsetFromOrigin``, in meters."""

    return tuple((deck_mm[i] + deck.corner[i]) * MM for i in range(3))


def qpos_for_tool(tool: str, site_m: tuple[float, float, float]) -> dict[str, float]:
    """Slide-joint values that put ``tool``'s site at a robot-frame point, by joint name.

    ``y`` and ``x`` place the carriage, which is shared. Each tool has its own Z
    joint whose value is the height of that tool's site above its rest offset.
    Tools that are not in use sit at ``Z_PARK``.
    """

    spec = flex_shell.TOOL_BY_NAME[tool]
    q = {t.joint: flex_shell.Z_PARK for t in flex_shell.TOOLS}
    q["x"] = site_m[0] - spec.dx
    q["y"] = site_m[1] - spec.dy
    q[spec.joint] = site_m[2] - spec.dz
    return q


def qpos_for_tip(tip_m: tuple[float, float, float]) -> dict[str, float]:
    """The 1000 uL pipette tip at a point; joints ``x`` ``y`` ``z`` equal the point itself."""

    return qpos_for_tool("pipette_1000", tip_m)


def pose_qpos(deck: Deck, pose: Pose, plate_home_mm: tuple[float, float, float]) -> dict[str, float]:
    """Tool joints, plus jaw opening and the plate's front-left-bottom."""

    q = qpos_for_tool(pose.tool, robot_m(deck, pose.deck_mm))
    jaw = flex_shell.JAW_OPEN if pose.jaw is None else pose.jaw
    q["jaw_f"] = -jaw
    q["jaw_b"] = jaw
    origin = plate_home_mm if pose.plate_mm is None else pose.plate_mm
    q["plate_x"], q["plate_y"], q["plate_z"] = robot_m(deck, origin)
    return q


def labware_origin(deck: Deck, slot: str, labware: Labware) -> tuple[float, float, float]:
    """Front-left-bottom of a labware in deck millimeters."""

    slot_pos = deck.slots[slot]
    return (
        slot_pos[0] + labware.offset[0],
        slot_pos[1] + labware.offset[1],
        slot_pos[2] + labware.offset[2],
    )


def well_points(
    deck: Deck, slot: str, labware: Labware, well_name: str
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return (bottom, top) of a well in deck millimeters.

    In the labware JSON, ``z`` is the well bottom: top is ``z + depth``.
    """

    origin = labware_origin(deck, slot, labware)
    well = labware.wells[well_name]
    bottom = (origin[0] + well.x, origin[1] + well.y, origin[2] + well.z)
    top = (bottom[0], bottom[1], bottom[2] + well.depth)
    return bottom, top


def home_point(deck: Deck, z_mm: float) -> tuple[float, float, float]:
    """Where the 1000 uL nozzle waits at home, deck millimeters: back right, as far as the rails allow."""

    layout = flex_shell.Layout.for_deck(deck)
    y_max = layout.joint_ranges()["y"][1] / MM - deck.corner[1] - 2.0
    return (
        min(deck.size[0] / 2, layout.home_x_max / MM - deck.corner[0]),
        min(deck.size[1] - 40.0, y_max),
        z_mm,
    )


def _pose(
    command: str,
    where: str,
    deck_mm: tuple[float, float, float],
    tool: str = "pipette_1000",
    jaw: float | None = None,
    plate_mm: tuple[float, float, float] | None = None,
) -> Pose:
    return Pose(command=command, where=where, deck_mm=deck_mm, tool=tool, jaw=jaw, plate_mm=plate_mm)


def demo_poses(deck: Deck, tiprack: Labware, plate: Labware) -> list[Pose]:
    """A short Flex transfer: pick A1, aspirate plate A1, dispense B1, drop.
    Then the 8-channel visits plate column 1. The gripper then closes on that
    plate (the liquid dispensed into B1 goes with it) and carries it from D2
    to empty slot C2.

    Tip rack on front slot D1, plate on the next slot D2. There is no fixed
    trash addressable area with geometry on the Flex deck (only
    ``legacyFixtures.fixedTrash`` naming A3, and optional movableTrash
    fixtures). Drop above empty back slot A3, clear of the deck surface.
    """

    _, tip_top = well_points(deck, "D1", tiprack, "A1")
    a_bottom, a_top = well_points(deck, "D2", plate, "A1")
    b_bottom, b_top = well_points(deck, "D2", plate, "B1")
    # Empty back slot A3: drop above the deck (no trash bin geom).
    drop_slot = deck.slots["A3"]
    drop_xy = (drop_slot[0] + 64.0, drop_slot[1] + 43.0)
    deck_z = 0.0

    def above(point: tuple[float, float, float], lift: float = 40.0) -> tuple[float, float, float]:
        return (point[0], point[1], point[2] + lift)

    home = home_point(deck, tip_top[2] + 80.0)
    park_z = flex_shell.Z_PARK / MM
    travel_z = tip_top[2] + 31.0
    home_plate = labware_origin(deck, "D2", plate)
    c2_slot = deck.slots["C2"]
    c2_plate = (
        c2_slot[0] + plate.offset[0],
        c2_slot[1] + plate.offset[1],
        c2_slot[2] + plate.offset[2],
    )
    # Paddle occupies z 0..8 mm in the gripper frame; the site is its bottom.
    # The labware JSON's grip height is the contact, halfway up the paddle.
    # The jaws close on the plate's front and back faces (its y dimension).
    paddle_half = PADDLE_HALF_MM
    closed = plate.y * MM / 2
    grip_z = home_plate[2] + plate.grip_z - paddle_half
    lift = 40.0

    def visit(where: str, xy: tuple[float, float], z: float, tool: str) -> list[Pose]:
        return [
            _pose("moveToWell", where, (xy[0], xy[1], travel_z), tool),
            _pose("moveToWell", where, (xy[0], xy[1], z), tool),
            _pose("moveToWell", where, (xy[0], xy[1], travel_z), tool),
        ]

    def grip(where: str, origin: tuple[float, float, float], site_z: float, jaw: float | None, plate_z: float) -> Pose:
        center = (origin[0] + plate.x / 2, origin[1] + plate.y / 2, site_z)
        return _pose("moveLabware", where, center, "gripper", jaw=jaw, plate_mm=(origin[0], origin[1], plate_z))
    return [
        _pose("home", "start", home),
        _pose("moveToWell", "tiprack A1", above(tip_top)),
        _pose("pickUpTip", "tiprack A1", tip_top),
        _pose("moveToWell", "tiprack A1", above(tip_top)),
        # Cross at tip-rack height first, so the nozzle does not drag through the tips.
        _pose("moveToWell", "plate A1", (a_top[0], a_top[1], tip_top[2] + 40.0)),
        _pose("moveToWell", "plate A1", above(a_top)),
        _pose("aspirate", "plate A1", (a_bottom[0], a_bottom[1], a_bottom[2] + 1.5)),
        _pose("moveToWell", "plate A1", above(a_top)),
        _pose("moveToWell", "plate B1", above(b_top)),
        _pose("dispense", "plate B1", (b_bottom[0], b_bottom[1], b_bottom[2] + 1.5)),
        _pose("moveToWell", "plate B1", above(b_top)),
        _pose("moveToWell", "slot A3", (drop_xy[0], drop_xy[1], deck_z + 40.0)),
        _pose("dropTip", "slot A3", (drop_xy[0], drop_xy[1], deck_z + 15.0)),
        _pose("moveToWell", "slot A3", (drop_xy[0], drop_xy[1], deck_z + 60.0)),
        _pose("moveToWell", "slot A3", (drop_xy[0], drop_xy[1], park_z)),
        *visit("plate column 1", (a_top[0], a_top[1]), a_top[2] + 4.0, "pipette_8"),
        grip("above D2", home_plate, grip_z + lift, None, home_plate[2]),
        grip("at D2", home_plate, grip_z, None, home_plate[2]),
        grip("grip D2", home_plate, grip_z, closed, home_plate[2]),
        grip("lift D2", home_plate, grip_z + lift, closed, home_plate[2] + lift),
        grip("carry C2", c2_plate, grip_z + lift, closed, c2_plate[2] + lift),
        grip("down C2", c2_plate, grip_z, closed, c2_plate[2]),
        grip("release C2", c2_plate, grip_z, None, c2_plate[2]),
        grip("clear C2", c2_plate, grip_z + lift, None, c2_plate[2]),
        _pose("home", "end", home, plate_mm=c2_plate),
    ]


def _f(value: float) -> str:
    return f"{value:.5f}"


def _box(
    name: str,
    center_m: tuple[float, float, float],
    size_m: tuple[float, float, float],
    rgba: str,
) -> str:
    pos = " ".join(_f(v) for v in center_m)
    size = " ".join(_f(v / 2) for v in size_m)
    return f'<geom name="{name}" type="box" pos="{pos}" size="{size}" rgba="{rgba}"/>'


def _cylinder(
    name: str,
    center_m: tuple[float, float, float],
    radius_m: float,
    height_m: float,
    rgba: str,
) -> str:
    pos = " ".join(_f(v) for v in center_m)
    return (
        f'<geom name="{name}" type="cylinder" pos="{pos}" '
        f'size="{_f(radius_m)} {_f(height_m / 2)}" rgba="{rgba}"/>'
    )


def _camera(name: str, pos, target, fovy: float) -> str:
    pos = np.array(pos, dtype=float)
    z = pos - np.array(target, dtype=float)
    z /= np.linalg.norm(z)
    x = np.cross([0.0, 0.0, 1.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    axes = " ".join(_f(v) for v in (*x, *y))
    return f'<camera name="{name}" pos="{" ".join(_f(v) for v in pos)}" xyaxes="{axes}" fovy="{fovy}"/>'


def camera_axes(pos, target) -> np.ndarray:
    """Rotation matrix (columns x, y, z) of a camera at ``pos`` looking at ``target``, built as ``_camera`` does."""
    pos = np.array(pos, dtype=float)
    z = pos - np.array(target, dtype=float)
    z /= np.linalg.norm(z)
    x = np.cross([0.0, 0.0, 1.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


def deck_camera_pose(deck: Deck) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Position and look-at point, metres, of the fixed ``deck`` camera: the main view of the mp4."""
    deck_mid = robot_m(deck, (deck.slots["B2"][0] + deck.slot_size[0] / 2 + 30.0, deck.slots["C2"][1] + deck.slot_size[1] / 2 + 40.0, 0.0))
    look = (deck_mid[0], deck_mid[1], 0.05)
    far = (deck_mid[0] - 0.09, deck_mid[1] - 1.36, 1.22)
    return tuple(b + 0.72 * (a - b) for a, b in zip(far, look)), look


RACK_RGBA = "0.19 0.205 0.225 1"
TIP_RGBA = "0.93 0.94 0.95 1"
PLATE_RGBA = "0.93 0.945 0.96 1"
WELL_RGBA = "0.82 0.86 0.90 0.32"
LIQUID_RGBA = "0.08 0.44 0.90 1"
TRASH_RGBA = "0.15 0.16 0.17 1"
TRASH_LINER_RGBA = "0.32 0.33 0.35 1"
MODULE_RGBA = "0.84 0.85 0.87 1"
MODULE_TOP_RGBA = "0.56 0.58 0.61 1"
MODULE_LID_RGBA = "0.90 0.91 0.92 1"
ADAPTER_RGBA = "0.70 0.72 0.75 1"
# Height of tip collar left showing above the rack top. More than the
# tip-to-nozzle overlap (9.4-9.8 mm), so a seated nozzle stays above the rack.
TIP_SHOW_MM = 11.0
# A liquid column fills this share of the well opening, so the well wall shows round it.
LIQUID_FILL = 0.9
LIQUID_MIN_M = 0.0002


@dataclass(frozen=True)
class Placed:
    """One labware on the deck. ``key`` prefixes its geoms; ``origin_mm`` is its
    front-left-bottom in deck millimeters. ``movable`` labware hangs on slide joints."""

    key: str
    origin_mm: tuple[float, float, float]
    labware: Labware
    movable: bool = False
    label: str = ""
    # Adapters are drawn as a block up to where the labware on them sits.
    height_mm: float | None = None


@dataclass(frozen=True)
class TrashBin:
    """A trash bin fixture: the addressable area's front-left-bottom and bounding box, deck millimeters."""

    name: str
    origin_mm: tuple[float, float, float]
    size_mm: tuple[float, float, float]


@dataclass(frozen=True)
class WasteChute:
    """The waste-chute stand-in body over its cutout, deck millimeters.

    The deck JSON's chute addressable areas are drop slots with no volume (the
    single- and eight-channel slots sit at z 114.5), so the scene draws one
    open-topped box per cutout whose rim is level with those slots.
    """

    cutout: str
    origin_mm: tuple[float, float, float]
    size_mm: tuple[float, float, float]


# Chute body box relative to its cutout's corner (deck millimetres): centred on
# the drop slots (x +64, y -27..+36) with the rim at the 114.5 mm drop height.
CHUTE_BODY_OFFSET_MM = (42.0, -35.0, 0.0)
CHUTE_BODY_SIZE_MM = (45.0, 80.0, 114.5)


@dataclass(frozen=True)
class TipDims:
    """A mounted tip as the analysis reports it (``tipLength`` = ``reach_mm``) plus the rack's tip geometry."""

    reach_mm: float
    length_mm: float
    top_diameter_mm: float


@dataclass
class SceneSpec:
    placed: list[Placed]
    trash: list[TrashBin] = field(default_factory=list)
    modules: list[Module] = field(default_factory=list)
    # One waste-chute body when the protocol uses a chute area; the areas
    # themselves are drop points, not boxes to draw.
    chute: WasteChute | None = None
    # Wells that get a liquid column; initial heights in mm with an rgba string.
    liquid_wells: set[tuple[str, str]] = field(default_factory=set)
    initial_liquid: dict[tuple[str, str], tuple[float, str]] = field(default_factory=dict)
    tips: dict[str, TipDims] = field(default_factory=dict)
    title: str = "Flex Transfer Demo"
    # Pipette tools the protocol actually mounts; the scene builds one body per
    # mount in use and leaves an empty mount empty. The gripper is always built.
    tools: tuple[str, ...] = ()
    # Front-label texture per tool: (volume string, channel count string).
    faces: dict[str, tuple[str, str]] = field(default_factory=dict)


def liquid_column(well: Well, height_mm: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Local (pos, size) in meters of the liquid column geom for ``height_mm`` of liquid."""

    h = max(height_mm * MM, LIQUID_MIN_M)
    pos = (well.x * MM, well.y * MM, well.z * MM + h / 2)
    if well.shape == "rectangular":
        return pos, (well.size_x * LIQUID_FILL * MM / 2, well.size_y * LIQUID_FILL * MM / 2, h / 2)
    return pos, (well.radius * LIQUID_FILL * MM, h / 2, 0.0)


def _liquid_geom(key: str, name: str, well: Well, height_mm: float, rgba: str) -> str:
    pos, size = liquid_column(well, height_mm)
    kind = "box" if well.shape == "rectangular" else "cylinder"
    dims = size if kind == "box" else size[:2]
    return (
        f'<geom name="{key}_liquid_{name}" type="{kind}" pos="{" ".join(_f(v) for v in pos)}" '
        f'size="{" ".join(_f(v) for v in dims)}" rgba="{rgba}"/>'
    )


def _well_geom(key: str, name: str, well: Well, rgba: str) -> str:
    center = (well.x * MM, well.y * MM, (well.z + well.depth / 2) * MM)
    if well.shape == "rectangular":
        return _box(f"{key}_{name}", center, (well.size_x * MM, well.size_y * MM, well.depth * MM), rgba)
    return _cylinder(f"{key}_{name}", center, well.radius * MM, well.depth * MM, rgba)


def _tiprack_geoms(key: str, labware: Labware, tip_mesh: str) -> list[str]:
    """Rack pad, rack body (its top below the tip tops) and one lathed tip per well, local frame.

    The rack body is named ``body_<key>``, not ``<key>_...``: it is a look, not a
    well, and nothing aimed above a tip can reach it.
    """

    mid = (labware.x / 2, labware.y / 2)
    top = labware.top - TIP_SHOW_MM
    geoms = [
        _box(f"{key}_pad", (mid[0] * MM, mid[1] * MM, 1.5 * MM), (labware.x * MM, labware.y * MM, 3 * MM), RACK_RGBA),
        _box(
            f"body_{key}",
            (mid[0] * MM, mid[1] * MM, (3.0 + top) / 2 * MM),
            ((labware.x - 3.0) * MM, (labware.y - 3.0) * MM, (top - 3.0) * MM),
            RACK_RGBA,
        ),
    ]
    for name, well in labware.wells.items():
        end = well.z + well.depth - labware.tip_length
        geoms.append(
            f'<geom name="{key}_{name}" type="mesh" mesh="{tip_mesh}" '
            f'pos="{_f(well.x * MM)} {_f(well.y * MM)} {_f(end * MM)}" rgba="{TIP_RGBA}"/>'
        )
    return geoms


PE_TIPRACKS = {"pe_50a_1_ts_96_tiprack_50ul", "pe_200a_1_ts_96_tiprack_200ul"}


def _pe_tiprack_geoms(key: str, labware: Labware, book: flex_shell.AssetBook) -> list[str]:
    """PE appearance over the original clearance proxies and exact tip origins.

    JSON dimensions, well coordinates and tip length are authoritative. The
    rounded shell, insert thickness, wall and colours are schematic: no PE CAD
    was supplied. Reuse the tube insert's through-hole mesher, not a solid cap.
    """

    from PIL import Image, ImageDraw
    from .tube_rack_assets import write_insert

    mesh = book.tip_mesh(labware.tip_length, 2 * labware.wells["A1"].radius, hollow=True)
    geoms = _tiprack_geoms(key, labware, mesh)
    # A hidden proxy must retain alpha > 0 for the clearance sweep. Tip names
    # stay <key>_<well>, so rack pick-up/return visibility needs no special case.
    geoms[:2] = [g.replace('<geom ', '<geom group="3" ') for g in geoms[:2]]
    geoms[2:] = [g.replace(f'rgba="{TIP_RGBA}"', 'material="labware_pe_tip" rgba="0.52 0.59 0.62 0.90"')
                 for g in geoms[2:]]
    x, y = labware.x, labware.y
    seat = labware.top - TIP_SHOW_MM

    def rounded(name, lo, hi, material, radius=0.8):
        return flex_shell.rbox(book, f"visual_{key}_{name}", tuple(v * MM for v in lo),
                               tuple(v * MM for v in hi), material, radius * MM, group=0)

    geoms.append(rounded("base", (0, 0, 0), (x, y, 4.2), "labware_pe_rack_base", 1.3))
    # Open shell: four walls and a floor, with a narrow seam below the insert.
    geoms.append(rounded("floor", (2, 2, 3), (x - 2, y - 2, 5), "labware_pe_rack_body"))
    for name, lo, hi in (
        ("front", (1.5, 1.5, 3.4), (x - 1.5, 4.5, seat - 0.6)),
        ("back", (1.5, y - 4.5, 3.4), (x - 1.5, y - 1.5, seat - 0.6)),
        ("left", (1.5, 3.6, 3.4), (4.5, y - 3.6, seat - 0.6)),
        ("right", (x - 4.5, 3.6, 3.4), (x - 1.5, y - 3.6, seat - 0.6)),
    ):
        geoms.append(rounded(name, lo, hi, "labware_pe_rack_body", 1.1))
    outer = flex_shell.rrect(1.0 * MM, (x - 1) * MM, 1.0 * MM, (y - 1) * MM, 2 * MM, 2 * MM)
    hole = flex_shell.rrect(5.6 * MM, (x - 5.6) * MM, 5.6 * MM, (y - 5.6) * MM, 1.6 * MM, 1.6 * MM)
    rim = book.extrusion(f"pe_rim_{x:g}_{y:g}_{seat:g}", outer, hole, 2, (seat - 1) * MM, (seat + 1.4) * MM)
    geoms.append(flex_shell.mesh_geom(f"visual_{key}_rim", rim, "labware_pe_rack_rim", 0))
    inset, thickness = 5.0, 1.9
    openings = [(w.x - inset, w.y - inset, w.radius + 0.70) for w in labware.wells.values()]
    mesh_key = "pe_insert_" + hashlib.sha256(repr((x, y, openings)).encode()).hexdigest()[:12]
    insert = book._mesh(mesh_key, lambda p: write_insert(p, (x - 2 * inset) * MM, (y - 2 * inset) * MM,
                         [tuple(v * MM for v in h) for h in openings], thickness * MM))
    geoms.append(flex_shell.mesh_geom(f"visual_{key}_insert", insert, "labware_pe_rack_insert", 0,
                                     (inset * MM, inset * MM, (seat - 0.8) * MM)))
    # Readable but restrained identification; no unverified mould or latch details.
    volume = "50" if "50ul" in labware.load_name else "200"
    label_key = f"labware_pe_label_{volume}"
    if label_key not in book._materials:
        image = Image.new("RGB", (512, 120), (226, 232, 232))
        draw = ImageDraw.Draw(image)
        draw.text((20, 8), f"PE  /  {volume} uL", fill=(53, 67, 72), font=flex_shell._font(44, bold=True))
        draw.text((23, 65), f"PE-{volume}A-1-TS    96 TIPS", fill=(88, 103, 107), font=flex_shell._font(24))
        book.texture(label_key, image, specular=0.15, shininess=0.15)
    geoms.append(flex_shell.label(book, f"visual_{key}_label", (x / 2 * MM, 1.35 * MM, 27 * MM),
                                  (43 * MM, 10 * MM), label_key))
    return geoms


def _plate_geoms(key: str, labware: Labware, liquid_wells: set[str], initial: dict[str, tuple[float, str]]) -> list[str]:
    """Plate or reservoir, local frame: bottom pad, four side walls, clear wells, liquid columns.

    The side walls give the jaws a face at ``gripHeightFromLabwareBottom``. Wells
    are clear so the liquid columns show; they are children of the labware, so
    they travel with it when the gripper carries it.
    """

    margin = 5.5
    x, y, z = labware.x, labware.y, labware.z
    geoms = [
        _box(f"{key}_pad", (x / 2 * MM, y / 2 * MM, 0.0012), ((x - 2 * margin) * MM, (y - 2 * margin) * MM, 0.0024), PLATE_RGBA)
    ]
    rails = (
        ("left", (margin / 2, y / 2, z / 2), (margin, y, z)),
        ("right", (x - margin / 2, y / 2, z / 2), (margin, y, z)),
        ("front", (x / 2, margin / 2, z / 2), (x - 2 * margin, margin, z)),
        ("back", (x / 2, y - margin / 2, z / 2), (x - 2 * margin, margin, z)),
    )
    for name, center, size in rails:
        geoms.append(_box(f"{key}_side_{name}", tuple(v * MM for v in center), tuple(v * MM for v in size), PLATE_RGBA))
    for name, well in labware.wells.items():
        geoms.append(_well_geom(key, name, well, WELL_RGBA))
    for name in sorted(liquid_wells):
        height, rgba = initial.get(name, (0.0, "0 0 0 0"))
        geoms.append(_liquid_geom(key, name, labware.wells[name], height, rgba))
    return geoms


def _tuberack_geoms(key: str, labware: Labware, liquid_wells, initial, book) -> list[str]:
    from .tube_rack_assets import write_insert

    # The 4-in-1 stand's 73.6 mm base and 78.4 mm assembled height follow the
    # Opentrons tube-rack drawing. Bevels and tube wall thickness are illustrative.
    x, y = labware.x, labware.y
    if min(x, y) < 30 or labware.top < 24 or any(w.shape != "circular" for w in labware.wells.values()):
        return _plate_geoms(key, labware, liquid_wells, initial)
    top = min(78.4, labware.top - 1.2)
    frame = top - 4.8
    inset = 3.0
    holes = [(w.x - inset, w.y - inset, w.radius + (1.35 if w.radius < 6 else 1.0 if w.radius < 10 else 0.75))
             for w in labware.wells.values()]
    mesh_key = "rack_insert_" + hashlib.sha256(repr((x, y, holes)).encode()).hexdigest()[:12]
    try:
        insert = book._mesh(mesh_key, lambda path: write_insert(path, (x - 2 * inset) * MM, (y - 2 * inset) * MM,
                           [tuple(v * MM for v in h) for h in holes], 4.8 * MM))
    except ValueError:  # Custom layouts may not fit this stand; retain the generic preview.
        return _plate_geoms(key, labware, liquid_wells, initial)
    # Group 3 is hidden by both renderers but retains alpha for the clearance sweep.
    geoms = [g.replace('<geom ', '<geom group="3" ') for g in _plate_geoms(key, labware, set(), {})]

    def rounded(name, lo, hi, material, radius=1.2):
        return flex_shell.rbox(book, "visual_" + key + "_" + name, tuple(v * MM for v in lo),
                               tuple(v * MM for v in hi), material, radius * MM, group=0)

    geoms.append(rounded("base", (1, 1, 0.4), (x - 1, y - 1, 5.2), "labware_rack", 1.5))
    for side, width, axis, lo in [("front", x, 1, 0), ("back", x, 1, y - 3.2),
                                  ("left", y, 0, 0), ("right", y, 0, x - 3.2)]:
        outer = flex_shell.rrect(0, width * MM, 0, frame * MM, 3 * MM, 3 * MM)
        hole = flex_shell.rrect(8 * MM, (width - 8) * MM, 7 * MM, (frame - 7) * MM, 3 * MM, 5 * MM)
        # Tapered window gives the stand substantial corners rather than thin rods.
        hole = [(width * MM / 2 + (u - width * MM / 2) * (1 - 0.16 * v / (frame * MM)), v) for u, v in hole]
        mesh = book.extrusion(f"rack_window_{axis}_{width:g}_{frame:g}", outer, hole, axis, 0, 3.2 * MM)
        geoms.append(flex_shell.mesh_geom(f"visual_{key}_window_{side}", mesh, "labware_rack", 0,
                                           (lo * MM, 0, 0) if axis == 0 else (0, lo * MM, 0)))
    for side, xx, yy in [("fl", 0, 0), ("fr", x - 6, 0), ("bl", 0, y - 6), ("br", x - 6, y - 6)]:
        geoms.append(rounded("corner_" + side, (xx, yy, 1), (xx + 6, yy + 6, frame), "labware_rack", 1.4))
    outer = flex_shell.rrect(1 * MM, (x - 1) * MM, 1 * MM, (y - 1) * MM, 3 * MM, 3 * MM)
    inner = flex_shell.rrect(inset * MM, (x - inset) * MM, inset * MM, (y - inset) * MM, 0.5 * MM, 0.5 * MM)
    mesh = book.extrusion(f"rack_rim_{x:g}_{y:g}_{frame:g}", outer, inner, 2, frame * MM, top * MM)
    geoms.append(flex_shell.mesh_geom(f"visual_{key}_rim", mesh, "labware_rack_insert", 0))
    # One small shared texture supplies legible well names on the holder surface.
    label_key = "labware_rack_labels_" + hashlib.sha256(repr((mesh_key, tuple(labware.wells))).encode()).hexdigest()[:12]
    if label_key not in book._materials:
        scale = 8
        width, depth = x - 2 * inset, y - 2 * inset
        image = flex_shell.Image.new("RGB", (round(width * scale), round(depth * scale)), (41, 47, 51))
        draw = flex_shell.ImageDraw.Draw(image)
        font = flex_shell._font(15)
        for (name, well), (_, _, radius) in zip(labware.wells.items(), holes):
            flex_shell._text_center(draw, ((well.x - inset) * scale, (depth - (well.y - inset - radius - 2)) * scale),
                                    name, font, (152, 164, 170))
        book.texture(label_key, image, specular=0.35, shininess=0.36)
    geoms.append(flex_shell.mesh_geom(f"visual_{key}_insert", insert, label_key, 0, (inset * MM, inset * MM, frame * MM)))
    for name, well in labware.wells.items():
        if well.profile:
            # One shared hollow mesh per tube profile, with a rounded, open mouth.
            depth, r = well.depth, well.profile[-1][0]
            outer = [(0.0, 0.0)] + [(radius + 0.45, z) for radius, z in well.profile if z < depth - 1.1]
            outer += [(r + 0.45, depth - 1.1), (r + 0.8, depth - 0.85), (r + 0.8, depth - 0.2), (r + 0.35, depth)]
            profile = [(radius * MM, z * MM) for radius, z in outer + list(reversed(well.profile)) + [(0.0, 0.0)]]
            mesh_key = "tube_" + hashlib.sha256(repr(profile).encode()).hexdigest()[:12]
            mesh = book._mesh(mesh_key, lambda path, points=profile: flex_shell.write_lathe(path, points, seg=40))
            geoms.append(f'<geom name="visual_{key}_tube_{name}" type="mesh" mesh="{mesh}" pos="{_f(well.x * MM)} {_f(well.y * MM)} {_f(well.z * MM)}" material="labware_tube"/>')
        else:
            geoms.append(_well_geom("visual_" + key, "tube_" + name, well, "0.48 0.62 0.68 0.22"))
        # A separate annular rim reads clearly without turning the whole tube white.
        r, depth = well.radius, well.depth
        lip = [(r + 0.35, depth - 0.9), (r + 0.8, depth - 0.7), (r + 0.8, depth - 0.25),
               (r + 0.35, depth), (r, depth), (r, depth - 0.7), (r + 0.35, depth - 0.9)]
        lip_key = "tube_lip_" + hashlib.sha256(repr(lip).encode()).hexdigest()[:12]
        mesh = book._mesh(lip_key, lambda path, points=lip: flex_shell.write_lathe(path, [(a * MM, b * MM) for a, b in points], seg=40))
        geoms.append(f'<geom name="visual_{key}_lip_{name}" type="mesh" mesh="{mesh}" pos="{_f(well.x * MM)} {_f(well.y * MM)} {_f(well.z * MM)}" material="labware_tube_rim"/>')
    for name in sorted(liquid_wells):
        height, rgba = initial.get(name, (0.0, "0 0 0 0"))
        geoms.append(_liquid_geom(key, name, labware.wells[name], height, rgba))
    return geoms


def _trash_geoms(deck: Deck, bin_: TrashBin) -> list[str]:
    """Open-topped bin over the addressable area's bounding box, walls 3 mm."""

    x0, y0, z0 = bin_.origin_mm
    sx, sy, sz = bin_.size_mm
    t = 3.0
    name = f"trash_{bin_.name}"
    parts = (
        ("floor", (x0 + sx / 2, y0 + sy / 2, z0 + t / 2), (sx, sy, t), TRASH_LINER_RGBA),
        ("wall_front", (x0 + sx / 2, y0 + t / 2, z0 + sz / 2), (sx, t, sz), TRASH_RGBA),
        ("wall_back", (x0 + sx / 2, y0 + sy - t / 2, z0 + sz / 2), (sx, t, sz), TRASH_RGBA),
        ("wall_left", (x0 + t / 2, y0 + sy / 2, z0 + sz / 2), (t, sy - 2 * t, sz), TRASH_RGBA),
        ("wall_right", (x0 + sx - t / 2, y0 + sy / 2, z0 + sz / 2), (t, sy - 2 * t, sz), TRASH_RGBA),
    )
    return [_box(f"{name}_{part}", robot_m(deck, c), tuple(v * MM for v in size), rgba) for part, c, size, rgba in parts]


def _module_geoms(deck: Deck, mod: Module) -> list[str]:
    """Body up to the labware seat, the housing rim round it, and the closed thermocycler lid.

    Geoms are ``<key>_body``, ``<key>_top``, ``<key>_rim_*`` and ``<key>_lid``
    (hidden while the lid is open), world frame.
    """

    ax, ay, _ = mod.area_mm
    ix, iy = mod.interface
    mx, my = mod.margin
    x0, y0, sx, sy = ax - mx, ay - my, ix + 2 * mx, iy + 2 * my
    seat = mod.seat_mm
    top_t = min(1.0, seat)
    parts = [
        ("body", (x0 + sx / 2, y0 + sy / 2, (seat - top_t) / 2), (sx, sy, seat - top_t), MODULE_RGBA),
        ("top", (ax + ix / 2, ay + iy / 2, seat - top_t / 2), (ix, iy, top_t), MODULE_TOP_RGBA),
    ]
    if mod.has_rim:
        h, zc = mod.rim_mm - seat, (mod.rim_mm + seat) / 2
        parts += [
            ("rim_front", (x0 + sx / 2, y0 + my / 2, zc), (sx, my, h), MODULE_RGBA),
            ("rim_back", (x0 + sx / 2, y0 + sy - my / 2, zc), (sx, my, h), MODULE_RGBA),
            ("rim_left", (x0 + mx / 2, y0 + sy / 2, zc), (mx, sy - 2 * my, h), MODULE_RGBA),
            ("rim_right", (x0 + sx - mx / 2, y0 + sy / 2, zc), (mx, sy - 2 * my, h), MODULE_RGBA),
        ]
    if mod.lid_mm:
        h = mod.lid_mm - seat
        parts.append(("lid", (x0 + sx / 2, y0 + sy / 2, seat + h / 2), (sx, sy, h), MODULE_LID_RGBA))
    return [
        _box(f"{mod.key}_{part}", robot_m(deck, c), tuple(max(v, 0.2) * MM for v in size), rgba)
        for part, c, size, rgba in parts
        if min(size) > 0
    ]

def _chute_geoms(deck: Deck, chute: WasteChute) -> list[str]:
    """Open-topped chute body over the cutout, walls 3 mm, rim at the drop slots."""

    x0, y0, z0 = chute.origin_mm
    sx, sy, sz = chute.size_mm
    t = 3.0
    parts = (
        ("floor", (x0 + sx / 2, y0 + sy / 2, z0 + t / 2), (sx, sy, t), TRASH_LINER_RGBA),
        ("wall_front", (x0 + sx / 2, y0 + t / 2, z0 + sz / 2), (sx, t, sz), TRASH_RGBA),
        ("wall_back", (x0 + sx / 2, y0 + sy - t / 2, z0 + sz / 2), (sx, t, sz), TRASH_RGBA),
        ("wall_left", (x0 + t / 2, y0 + sy / 2, z0 + sz / 2), (t, sy - 2 * t, sz), TRASH_RGBA),
        ("wall_right", (x0 + sx - t / 2, y0 + sy / 2, z0 + sz / 2), (t, sy - 2 * t, sz), TRASH_RGBA),
    )
    return [_box(f"waste_chute_{part}", robot_m(deck, c), tuple(v * MM for v in size), rgba) for part, c, size, rgba in parts]


def labware_xml(deck: Deck, item: Placed, spec: SceneSpec, book: flex_shell.AssetBook, ranges) -> str:
    lw = item.labware
    if lw.is_adapter and not lw.wells:
        h = item.height_mm if item.height_mm is not None else lw.z
        geoms = [_box(f"{item.key}_block", (lw.x / 2 * MM, lw.y / 2 * MM, h / 2 * MM), (lw.x * MM, lw.y * MM, max(h, 0.2) * MM), ADAPTER_RGBA)]
    elif lw.is_tiprack:
        geoms = (_pe_tiprack_geoms(item.key, lw, book) if lw.load_name in PE_TIPRACKS else
                 _tiprack_geoms(item.key, lw, book.tip_mesh(lw.tip_length, 2 * lw.wells["A1"].radius)))
    else:
        wells = {w for k, w in spec.liquid_wells if k == item.key}
        initial = {w: v for (k, w), v in spec.initial_liquid.items() if k == item.key}
        geoms = _tuberack_geoms(item.key, lw, wells, initial, book) if lw.is_tuberack else _plate_geoms(item.key, lw, wells, initial)
    body = "\n      ".join(geoms)
    origin = robot_m(deck, item.origin_mm)
    if not item.movable:
        return f'<body name="{item.key}_lw" pos="{" ".join(_f(v) for v in origin)}">\n      {body}\n    </body>'

    def rng(axis: str) -> str:
        lo, hi = ranges[f"labware_{axis}"]
        return f"{_f(lo)} {_f(hi)}"

    joints = "\n      ".join(
        f'<joint name="{item.key}_{axis}" type="slide" axis="{vec}" range="{rng(axis)}"/>'
        for axis, vec in (("x", "1 0 0"), ("y", "0 1 0"), ("z", "0 0 1"))
    )
    return f'<body name="{item.key}_carrier" pos="0 0 0">\n      {joints}\n      {body}\n    </body>'


def build_xml(deck: Deck, spec: SceneSpec, assets: Path = ASSETS) -> str:
    layout = flex_shell.Layout.for_deck(deck)
    book = flex_shell.AssetBook(assets)
    flex_shell.make_textures(book, layout, deck, spec.title, len(spec.placed))
    ranges = layout.joint_ranges()
    pe_tips = {(lw.labware.tip_length, 2 * lw.labware.wells["A1"].radius)
               for lw in spec.placed if lw.labware.load_name in PE_TIPRACKS}
    tips = {
        tool: flex_shell.TipSpec(book.tip_mesh(d.length_mm, d.top_diameter_mm,
                                hollow=(d.length_mm, d.top_diameter_mm) in pe_tips), d.reach_mm, d.length_mm)
        for tool, d in spec.tips.items()
    }
    faces = {
        tool: flex_shell.pipette_face_material(book, tool, volume, channels)
        for tool, (volume, channels) in spec.faces.items()
    }

    labware = [labware_xml(deck, item, spec, book, ranges) for item in spec.placed]
    trash = [g for bin_ in spec.trash for g in _trash_geoms(deck, bin_)]
    modules = []
    for mod in spec.modules:
        detail = module_xml(deck, mod, book, robot_m)
        proxies = _module_geoms(deck, mod)
        # Detailed visuals and coarse collision proxies have separate roles.
        modules.extend(g.replace('<geom ', '<geom group="5" ') if detail else g for g in proxies
                       if not (detail and f'name="{mod.key}_lid"' in g))
        if detail:
            modules.append(detail)
    if spec.chute is not None:
        trash += _chute_geoms(deck, spec.chute)

    def rng(name: str) -> str:
        lo, hi = ranges[name]
        return f"{_f(lo)} {_f(hi)}"

    # One pipette body per mount in use; the right single's body carries the shared ``z`` joint.
    if "pipette_1000" in spec.tools:
        head = (
            '<body name="head" pos="0 0 0">\n'
            f'          <joint name="z" type="slide" axis="0 0 1" range="{rng("z")}"/>\n'
            f'          {flex_shell.pipette_1000_body(book, tips.get("pipette_1000"), faces.get("pipette_1000"))}\n'
            "        </body>"
        )
    else:
        head = ""
    mounted = []
    if "pipette_8" in spec.tools:
        mounted.append(flex_shell.pipette_8_body(book, rng("z_8"), tips.get("pipette_8"), faces.get("pipette_8")))
    if "pipette_1000_left" in spec.tools:
        mounted.append(flex_shell.pipette_1000_left_body(book, rng("z_left"), tips.get("pipette_1000_left"), faces.get("pipette_1000_left")))
    if "pipette_8_right" in spec.tools:
        mounted.append(flex_shell.pipette_8_right_body(book, rng("z_8_right"), tips.get("pipette_8_right"), faces.get("pipette_8_right")))

    gantry = f"""
    <body name="bridge" pos="0 0 0">
      <joint name="y" type="slide" axis="0 1 0" range="{rng("y")}"/>
        {flex_shell.bridge_geoms(book, layout)}
      <body name="carriage" pos="0 0 0">
        <joint name="x" type="slide" axis="1 0 0" range="{rng("x")}"/>
          {flex_shell.carriage_geoms(book, spec.tools)}
        <body name="head_focus" pos="0.03 -0.02 0.22"><geom type="sphere" size="0.001" contype="0" conaffinity="0" group="4" mass="0.001"/></body>
        <camera name="head_track" mode="targetbody" target="head_focus" pos="0.03 -0.62 0.30" fovy="40"/>
        {head}
        {chr(10).join(mounted)}
        {flex_shell.gripper_body(book, rng("z_gripper"), rng("jaw_f"), rng("jaw_b"))}
      </body>
    </body>
    """

    chassis = flex_shell.chassis_xml(book, layout, deck)
    target = layout.view_target
    deck_pos, deck_look_at = deck_camera_pose(deck)
    cams = "\n    ".join(
        [
            _camera("overview", (target[0] + 0.95, target[1] - 1.30, 0.98), target, 40),
            _camera("hero", (target[0] + 1.05, target[1] - 1.60, 0.62), (target[0], target[1], 0.27), 36),
            _camera("front", (target[0], target[1] - 1.75, 0.30), target, 38),
            _camera("side_right", (target[0] + 1.75, target[1], 0.30), target, 38),
            _camera("top_down", (target[0], target[1] - 0.25, 1.9), (target[0], target[1], 0.0), 40),
            # Front and above, looking down through the door window, left of the touchscreen.
            _camera("deck", deck_pos, deck_look_at, 25),
        ]
    )
    return f"""<mujoco model="flex">
  <compiler angle="radian" meshdir="{assets.name}" texturedir="{assets.name}"/>
  <option gravity="0 0 0"/>
  <visual>
    <global azimuth="128" elevation="-18" offwidth="1920" offheight="1200"/>
    <quality shadowsize="8192" offsamples="8"/>
    <headlight ambient="0.28 0.28 0.28" diffuse="0.10 0.10 0.10" specular="0.04 0.04 0.04"/>
    <map znear="0.01" zfar="20" haze="0.25"/>
    <rgba haze="0.96 0.965 0.975 1"/>
  </visual>
  <default>
    <geom contype="0" conaffinity="0"/>
  </default>
  <asset>
    {flex_shell.materials_xml()}
    {book.asset_xml()}
  </asset>
  <worldbody>
    {flex_shell.scene_lighting(layout)}
    {cams}
    {chassis}
    {chr(10).join(trash)}
    {chr(10).join(modules)}
    {chr(10).join(labware)}
    {gantry}
  </worldbody>
</mujoco>
"""


def write_model(deck: Deck, spec: SceneSpec, folder: Path = EXPORT) -> Path:
    """Write ``flex.xml`` and its ``flex_assets/`` into ``folder``."""

    folder.mkdir(parents=True, exist_ok=True)
    xml_path = folder / "flex.xml"
    xml_path.write_text(build_xml(deck, spec, folder / "flex_assets"), encoding="utf-8")
    return xml_path


def load_model(xml_path: Path):
    """``mujoco.MjModel`` for a ``write_model`` folder, read through Python.

    MuJoCo on Windows cannot open paths with non-ASCII characters (a Chinese
    protocol name or user folder), so the XML and its assets go in as bytes.
    """

    import mujoco

    xml_path = Path(xml_path)
    assets = {item.name: item.read_bytes() for item in (xml_path.parent / "flex_assets").glob("*") if item.is_file()}
    return mujoco.MjModel.from_xml_string(xml_path.read_text(encoding="utf-8"), assets)
