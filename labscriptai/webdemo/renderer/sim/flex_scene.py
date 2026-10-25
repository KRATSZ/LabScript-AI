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

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from sim import flex_shell

ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "cad" / "flex" / "deck" / "ot3_standard.json"
_EXPORT_OVERRIDE = os.environ.get("LABSCRIPTAI_RENDERER_EXPORT")
EXPORT = Path(_EXPORT_OVERRIDE).expanduser().resolve() if _EXPORT_OVERRIDE else ROOT / "exports" / "mujoco"
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
    raw = json.loads(path.read_text())
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


def _well(raw: dict) -> Well:
    if raw.get("shape") == "rectangular":
        sx, sy = float(raw["xDimension"]), float(raw["yDimension"])
        return Well(float(raw["x"]), float(raw["y"]), float(raw["z"]), float(raw["depth"]), min(sx, sy) / 2, "rectangular", sx, sy)
    d = float(raw.get("diameter", 6.0))
    return Well(float(raw["x"]), float(raw["y"]), float(raw["z"]), float(raw["depth"]), d / 2, "circular", d, d)


def labware_from_definition(raw: dict) -> Labware:
    """Labware from an Opentrons definition dict (a JSON file, or ``loadLabware.result.definition``)."""

    dims = raw["dimensions"]
    corner = raw["cornerOffsetFromSlot"]
    params = raw["parameters"]
    return Labware(
        load_name=params["loadName"],
        x=float(dims["xDimension"]),
        y=float(dims["yDimension"]),
        z=float(dims["zDimension"]),
        offset=(float(corner["x"]), float(corner["y"]), float(corner["z"])),
        wells={name: _well(well) for name, well in raw["wells"].items()},
        grip_z=float(raw.get("gripHeightFromLabwareBottom") or 0.0),
        is_tiprack=bool(params.get("isTiprack")),
        tip_length=float(params.get("tipLength") or 0.0),
        quirks=tuple(params.get("quirks") or ()),
    )


def load_labware(path: Path) -> Labware:
    return labware_from_definition(json.loads(path.read_text()))


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
    return (deck_mid[0] - 0.09, deck_mid[1] - 1.36, 1.22), (deck_mid[0] + 0.0, deck_mid[1] + 0.0, 0.07)


RACK_RGBA = "0.19 0.205 0.225 1"
TIP_RGBA = "0.93 0.94 0.95 1"
PLATE_RGBA = "0.93 0.945 0.96 1"
WELL_RGBA = "0.82 0.86 0.90 0.32"
LIQUID_RGBA = "0.08 0.44 0.90 1"
TRASH_RGBA = "0.15 0.16 0.17 1"
TRASH_LINER_RGBA = "0.32 0.33 0.35 1"
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


@dataclass(frozen=True)
class TrashBin:
    """A trash bin fixture: the addressable area's front-left-bottom and bounding box, deck millimeters."""

    name: str
    origin_mm: tuple[float, float, float]
    size_mm: tuple[float, float, float]


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
    # Wells that get a liquid column; initial heights in mm with an rgba string.
    liquid_wells: set[tuple[str, str]] = field(default_factory=set)
    initial_liquid: dict[tuple[str, str], tuple[float, str]] = field(default_factory=dict)
    tips: dict[str, TipDims] = field(default_factory=dict)
    title: str = "Flex Transfer Demo"


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


def labware_xml(deck: Deck, item: Placed, spec: SceneSpec, book: flex_shell.AssetBook, ranges) -> str:
    lw = item.labware
    if lw.is_tiprack:
        geoms = _tiprack_geoms(item.key, lw, book.tip_mesh(lw.tip_length, 2 * lw.wells["A1"].radius))
    else:
        wells = {w for k, w in spec.liquid_wells if k == item.key}
        initial = {w: v for (k, w), v in spec.initial_liquid.items() if k == item.key}
        geoms = _plate_geoms(item.key, lw, wells, initial)
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
    tips = {
        tool: flex_shell.TipSpec(book.tip_mesh(d.length_mm, d.top_diameter_mm), d.reach_mm, d.length_mm)
        for tool, d in spec.tips.items()
    }

    labware = [labware_xml(deck, item, spec, book, ranges) for item in spec.placed]
    trash = [g for bin_ in spec.trash for g in _trash_geoms(deck, bin_)]

    def rng(name: str) -> str:
        lo, hi = ranges[name]
        return f"{_f(lo)} {_f(hi)}"

    gantry = f"""
    <body name="bridge" pos="0 0 0">
      <joint name="y" type="slide" axis="0 1 0" range="{rng("y")}"/>
        {flex_shell.bridge_geoms(book, layout)}
      <body name="carriage" pos="0 0 0">
        <joint name="x" type="slide" axis="1 0 0" range="{rng("x")}"/>
          {flex_shell.carriage_geoms(book)}
        <body name="head_focus" pos="0.03 -0.02 0.22"><geom type="sphere" size="0.001" contype="0" conaffinity="0" group="4" mass="0.001"/></body>
        <camera name="head_track" mode="targetbody" target="head_focus" pos="0.03 -0.62 0.30" fovy="40"/>
        <body name="head" pos="0 0 0">
          <joint name="z" type="slide" axis="0 0 1" range="{rng("z")}"/>
        {flex_shell.pipette_1000_body(book, tips.get("pipette_1000"))}
        </body>
        {flex_shell.pipette_8_body(book, rng("z_8"), tips.get("pipette_8"))}
        {flex_shell.pipette_1000_left_body(book, rng("z_left"), tips.get("pipette_1000_left"))}
        {flex_shell.pipette_8_right_body(book, rng("z_8_right"), tips.get("pipette_8_right"))}
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
    <headlight ambient="0.34 0.34 0.36" diffuse="0.22 0.22 0.22" specular="0.06 0.06 0.06"/>
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
    <geom name="floor" type="plane" pos="{_f(target[0])} {_f(target[1])} {_f(layout.z0)}" size="3 3 0.05" material="floor" group="0"/>
    {chassis}
    {chr(10).join(trash)}
    {chr(10).join(labware)}
    {gantry}
  </worldbody>
</mujoco>
"""


def write_model(deck: Deck, spec: SceneSpec, folder: Path = EXPORT) -> Path:
    """Write ``flex.xml`` and its ``flex_assets/`` into ``folder``."""

    folder.mkdir(parents=True, exist_ok=True)
    xml_path = folder / "flex.xml"
    xml_path.write_text(build_xml(deck, spec, folder / "flex_assets"))
    return xml_path
