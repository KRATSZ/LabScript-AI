"""OT-2 scene in the official deck frame.

Cutout and well numbers come from the Opentrons JSON in ``cad/``.
``cornerOffsetFromOrigin`` converts deck millimeters into the robot frame
that ``opentrons analyze`` reports. MuJoCo uses meters.

The Basic mesh is the enclosure (one welded shell, nothing inside to move).
The Detailed mesh is the same shell plus the gantry. Moving parts are cut
out of Detailed and hung on the three slide joints: the crossbeam on ``y``,
the carriage on ``x``, the pipette on ``z``. The pipette mesh is shifted so
its nozzle face centre sits on the head origin, which is the tip.
"""

from __future__ import annotations

import json
import hashlib
import math
import os
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from sim.flex_scene import LIQUID_FILL, Labware as SpecLabware, camera_axes, liquid_column
from sim import ot2_shell as shell

ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "cad" / "ot2" / "deck" / "ot2_standard.json"
# Vendored schema-3 module definitions (opentrons_shared_data
# .../module/definitions/3). The engine reads schema 2 for apiLevel 2, but the
# two agree on every number used here; schema 3 just writes slotTransforms as
# 4x4 matrices and adds the drawing fields schema 2 lacks (xDimension,
# labwareInterface, lidHeight, maxEngageHeight).
MODULES_PATH = ROOT / "cad" / "ot2" / "modules"
_EXPORT_OVERRIDE = os.environ.get("LABSCRIPTAI_RENDERER_EXPORT")
EXPORT = Path(_EXPORT_OVERRIDE).expanduser().resolve() if _EXPORT_OVERRIDE else ROOT / "exports" / "mujoco"
BASE_STL = ROOT / "cad" / "ot2" / "stl" / "OT-2 Reference Model Basic.STL"
DETAILED_STL = ROOT / "cad" / "ot2" / "stl" / "OT-2 Reference Model Detailed.STL"
MM = 0.001
PITCH_MM = 9.0
HEAD_Z_RANGE_M = (-0.02, 0.28)
CENTER_OFFSET_MM = 3.5 * PITCH_MM
NOZZLE_ROWS = tuple("ABCDEFGH")
RACK_RGBA = "0.19 0.205 0.225 1"
# OT-2 tips are translucent polypropylene.  Keep the visible wall readable
# against the dark rack while leaving the bore/underlying metal nozzle legible.
# Length and insertion are still taken from the loaded labware definition.
TIP_RGBA = "0.84 0.90 0.94 0.40"
PLATE_RGBA = "0.93 0.945 0.96 1"
WELL_RGBA = "0.82 0.86 0.90 0.32"
MOD_RGBA = "0.66 0.69 0.72 1"
MOD_HOT_RGBA = "0.72 0.62 0.50 1"
MOD_PIN_RGBA = "0.24 0.27 0.31 1"
MOD_LID_RGBA = "0.44 0.47 0.51 1"
# Official raw STL -> protocol-frame mapping.  The vendor files use
# (x=width, y=height, z=depth), whereas the simulator uses
# (x=width, y=front/back, z=up).  The local CAD manifest and
# blender/build_ot2_blend.py agree on this translation in millimetres.
RAW_AXIS_ORDER = (0, 2, 1)
SHELL_SHIFT_MM = (231.3, 190.03, 72.0)
RAW_TO_ROBOT_MM = np.asarray(SHELL_SHIFT_MM, dtype=np.float64)


@dataclass(frozen=True)
class Well:
    x: float
    y: float
    z: float
    depth: float
    radius: float


@dataclass(frozen=True)
class Labware:
    load_name: str
    x: float
    y: float
    z: float
    offset: tuple[float, float, float]
    wells: dict[str, Well]


@dataclass(frozen=True)
class Trash:
    origin: tuple[float, float, float]
    size: tuple[float, float, float]

    @property
    def center(self) -> tuple[float, float, float]:
        return tuple(self.origin[i] + self.size[i] / 2 for i in range(3))

    @property
    def top_z(self) -> float:
        return self.origin[2] + self.size[2]


@dataclass(frozen=True)
class Deck:
    corner: tuple[float, float, float]
    size: tuple[float, float, float]
    slots: dict[str, tuple[float, float, float]]
    trash: Trash
    slot_size: tuple[float, float]


@dataclass(frozen=True)
class Pose:
    """One sampled tip target. ``command`` uses LogicPass / analyze names."""

    command: str
    where: str
    deck_mm: tuple[float, float, float]

def load_deck(path: Path = DECK_PATH) -> Deck:
    raw = json.loads(path.read_text())
    cutouts = {item["id"]: tuple(item["position"]) for item in raw["locations"]["cutouts"]}
    slots: dict[str, tuple[float, float, float]] = {}
    for fixture in raw["cutoutFixtures"]:
        for cutout_id, areas in fixture["providesAddressableAreas"].items():
            for area in areas:
                slots[area] = cutouts[cutout_id]
    trash_raw = next(
        area for area in raw["locations"]["addressableAreas"] if area["id"] == "fixedTrash"
    )
    cutout = slots["fixedTrash"]
    offset = trash_raw["offsetFromCutoutFixture"]
    box = trash_raw["boundingBox"]
    origin = (
        cutout[0] + offset[0],
        cutout[1] + offset[1],
        cutout[2] + offset[2],
    )
    trash = Trash(
        origin=origin,
        size=(box["xDimension"], box["yDimension"], box["zDimension"]),
    )
    slot_boxes = {
        (area["boundingBox"]["xDimension"], area["boundingBox"]["yDimension"])
        for area in raw["locations"]["addressableAreas"]
        if area["id"] in slots and area["id"] != "fixedTrash"
    }
    if len(slot_boxes) != 1:
        raise ValueError(f"slot sizes differ in {path.name}: {slot_boxes}")
    return Deck(
        corner=tuple(raw["cornerOffsetFromOrigin"]),
        size=tuple(raw["dimensions"]),
        slots=slots,
        trash=trash,
        slot_size=slot_boxes.pop(),
    )


def load_labware(path: Path) -> Labware:
    raw = json.loads(path.read_text())
    wells = {
        name: Well(
            x=float(well["x"]),
            y=float(well["y"]),
            z=float(well["z"]),
            depth=float(well["depth"]),
            radius=float(well.get("diameter", 6.0)) / 2,
        )
        for name, well in raw["wells"].items()
    }
    dims = raw["dimensions"]
    corner = raw["cornerOffsetFromSlot"]
    return Labware(
        load_name=raw["parameters"]["loadName"],
        x=float(dims["xDimension"]),
        y=float(dims["yDimension"]),
        z=float(dims["zDimension"]),
        offset=(float(corner["x"]), float(corner["y"]), float(corner["z"])),
        wells=wells,
    )


def load_module_def(model: str) -> dict:
    path = MODULES_PATH / f"{model}.json"
    if not path.exists():
        raise FileNotFoundError(f"no definition vendored for {model}")
    return json.loads(path.read_text())


def robot_m(deck: Deck, deck_mm: tuple[float, float, float]) -> tuple[float, float, float]:
    """Deck millimeters plus ``cornerOffsetFromOrigin``, in meters."""

    return tuple((deck_mm[i] + deck.corner[i]) * MM for i in range(3))


def qpos_for_tip(tip_m: tuple[float, float, float]) -> dict[str, float]:
    """Map a robot-frame tip position onto the slide joints, by joint name.

    The head body origin is the pipette tip, so each joint value is that
    coordinate of the tip. The carriage inherits x and y; the beam inherits y.
    """

    x, y, z = tip_m
    return {"x": x, "y": y, "z": z}


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

    In the labware JSON, ``z`` is the well bottom: for the NEST plate,
    ``z + depth`` equals the labware height.
    """

    origin = labware_origin(deck, slot, labware)
    well = labware.wells[well_name]
    bottom = (origin[0] + well.x, origin[1] + well.y, origin[2] + well.z)
    top = (bottom[0], bottom[1], bottom[2] + well.depth)
    return bottom, top


def _pose(command: str, where: str, deck_mm: tuple[float, float, float]) -> Pose:
    return Pose(command=command, where=where, deck_mm=deck_mm)


def demo_poses(deck: Deck, tiprack: Labware, plate: Labware) -> list[Pose]:
    """A short OT-2 transfer: pick A1, aspirate plate A1, dispense B1, drop in trash.

    Motion between wells is ``moveToWell``, which LogicPass allowlists and does
    not treat as a volume change. The four state-changing commands match the
    leaf types LogicPass consumes.
    """

    _, tip_top = well_points(deck, "1", tiprack, "A1")
    a_bottom, a_top = well_points(deck, "2", plate, "A1")
    b_bottom, b_top = well_points(deck, "2", plate, "B1")
    trash_xy = (deck.trash.center[0], deck.trash.center[1])
    trash_top = deck.trash.top_z

    def above(point: tuple[float, float, float], lift: float = 40.0) -> tuple[float, float, float]:
        return (point[0], point[1], point[2] + lift)

    home = (
        deck.size[0] / 2,
        deck.size[1] - 40.0,
        tip_top[2] + 80.0,
    )
    return [
        _pose("home", "start", home),
        _pose("moveToWell", "tiprack A1", above(tip_top)),
        _pose("pickUpTip", "tiprack A1", tip_top),
        _pose("moveToWell", "tiprack A1", above(tip_top)),
        _pose("moveToWell", "plate A1", above(a_top)),
        _pose("aspirate", "plate A1", (a_bottom[0], a_bottom[1], a_bottom[2] + 1.5)),
        _pose("moveToWell", "plate A1", above(a_top)),
        _pose("moveToWell", "plate B1", above(b_top)),
        _pose("dispense", "plate B1", (b_bottom[0], b_bottom[1], b_bottom[2] + 1.5)),
        _pose("moveToWell", "plate B1", above(b_top)),
        _pose("moveToWell", "trash", (trash_xy[0], trash_xy[1], trash_top + 40.0)),
        _pose("dropTip", "trash", (trash_xy[0], trash_xy[1], trash_top + 15.0)),
        _pose("moveToWell", "trash", (trash_xy[0], trash_xy[1], trash_top + 60.0)),
    ]


def _load_triangles(path: Path) -> np.ndarray:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    record = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.frombuffer(data, dtype=record, count=count, offset=84)["v"].astype(np.float64).copy()


def _raw_to_robot_triangles(triangles: np.ndarray) -> np.ndarray:
    """Convert official OT-2 STL vertices into the protocol frame (mm).

    The raw files are millimetres and use ``x, height, depth``.  Applying the
    axis permutation before the translation is important: subtracting the
    translation in raw order was the source of the former 662/567.5
    Y/Z-swapped shell and its oversized clearance proxy.
    """

    return np.asarray(triangles, dtype=np.float64)[:, :, RAW_AXIS_ORDER] - RAW_TO_ROBOT_MM


def _write_stl(path: Path, triangles: np.ndarray) -> None:
    triangles = np.asarray(triangles, dtype=np.float32)
    count = len(triangles)
    normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    length = np.linalg.norm(normal, axis=1, keepdims=True)
    normal = normal / np.maximum(length, 1e-8)
    record = np.zeros(count, dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    record["n"] = normal
    record["v"] = triangles
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"OT-2".ljust(80, b"\0") + np.uint32(count).tobytes() + record.tobytes())


def _contained(
    triangles: np.ndarray,
    xlim: float,
    ymin: float,
    ymax: float,
) -> np.ndarray:
    """Keep triangles that lie entirely inside the nozzle window.

    A centroid test keeps spikes from the long extrusion. The wide floor sheet
    is kept when ``xlim`` covers it; callers narrow that sheet about x = 0.
    """

    low = triangles.min(axis=1)
    high = triangles.max(axis=1)
    keep = (
        (low[:, 0] >= -xlim)
        & (high[:, 0] <= xlim)
        & (low[:, 1] >= ymin)
        & (high[:, 1] <= ymax)
    )
    kept = triangles[keep]
    if len(kept) < 40:
        raise RuntimeError(f"nozzle window left {len(kept)} triangles")
    return kept


def _fit_x(triangles: np.ndarray, half_mm: float) -> None:
    """Narrow about x = 0 so the head stays inside the shell at slot 1.

    Slot 1 is about 15 mm from the outer left skin, so a full-width trough
    cannot reach it. Scaling the already-windowed head keeps a solid block.
    """

    half = float(np.max(np.abs(triangles[:, :, 0])))
    if half > half_mm:
        triangles[:, :, 0] *= half_mm / half


def _box_from_mm(triangles: np.ndarray) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Axis-aligned collision box in the mesh frame, meters. Size is half-extents."""

    points = triangles.reshape(-1, 3)
    low = points.min(axis=0)
    high = points.max(axis=0)
    center = (low + high) / 2 * MM
    half = np.maximum((high - low) / 2 * MM, 0.004)
    return tuple(float(v) for v in center), tuple(float(v) for v in half)


def _nozzle_tip_mm(triangles: np.ndarray) -> np.ndarray:
    """Legacy reference face in raw Detailed-mesh millimeters.

    The vendor Detailed STL is a static reference shell rather than the
    protocol's moving instrument.  This stable face is retained only to make
    the standalone mesh splitter deterministic; it is transformed explicitly
    before any mesh is written and is never used as a joint/site target.
    """

    low = triangles.min(axis=1)
    high = triangles.max(axis=1)
    central = (
        (low[:, 0] > 240.0)
        & (high[:, 0] < 400.0)
        & (low[:, 1] > 450.0)
        & (high[:, 1] < 620.0)
        & (low[:, 2] > 200.0)
        & (high[:, 2] < 280.0)
    )
    if not np.any(central):
        raise RuntimeError("Detailed OT-2 mesh has no pipette housing")
    floor = float(triangles[central][:, :, 2].min())
    face = central & (high[:, 2] < floor + 1.5)
    points = triangles[face].reshape(-1, 3)
    return np.array(
        [
            (points[:, 0].min() + points[:, 0].max()) / 2,
            (points[:, 1].min() + points[:, 1].max()) / 2,
            points[:, 2].min(),
        ]
    )


def write_gantry_meshes(folder: Path = EXPORT, x_shift_mm: float | None = None) -> dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]]:
    """Split the statue into shell, beam, carriage, and pipette STLs.

    Shell comes from the Basic mesh with the front door panel removed so the
    deck stays visible. Beam, carriage, and pipette come from the Detailed
    mesh, written already in the joint frame (millimetres):

    * beam moves with ``y`` only, so its x and z stay in the robot frame and
      its y is relative to the nozzle;
    * carriage moves with ``x`` and ``y``, so x and y are relative to the nozzle
      and z stays in the robot frame;
    * pipette moves with all three, and its nozzle centre is the origin.

    The raw static files are converted with the official axis permutation and
    translation before the split.  ``x_shift_mm`` is retained for API
    compatibility but intentionally ignored: all four written meshes are
    already in the corrected protocol frame or an explicitly documented local
    joint frame.  The spec model is built procedurally in ``sim.ot2_shell``;
    this helper remains for the standalone demo and legacy checks.
    """

    shell_tri = _raw_to_robot_triangles(_load_triangles(BASE_STL))
    shell_c = shell_tri.mean(axis=1)
    door = (
        (shell_c[:, 1] < shell.Y0 * 1000.0 + 28.0)
        & (shell_c[:, 0] > shell.DOOR_X0 * 1000.0)
        & (shell_c[:, 0] < shell.DOOR_X1 * 1000.0)
        & (shell_c[:, 2] > shell.DOOR_Z0 * 1000.0)
        & (shell_c[:, 2] < shell.DOOR_Z1 * 1000.0)
    )
    _write_stl(folder / "ot2_shell.stl", shell_tri[~door])

    detailed = _raw_to_robot_triangles(_load_triangles(DETAILED_STL))
    # Preserve the old deterministic reference face, then transform its
    # coordinates in the same order as the mesh.  It is not an authoritative
    # nozzle/site position and never changes the protocol skeleton.
    raw_tip = _nozzle_tip_mm(_load_triangles(DETAILED_STL))
    tip = raw_tip[list(RAW_AXIS_ORDER)] - RAW_TO_ROBOT_MM
    low = detailed.min(axis=1)
    high = detailed.max(axis=1)
    extent = high - low

    # Every vertex has to sit inside the part. A centroid test keeps triangles
    # that spike out of the cut and the carriage falls apart.
    beam = (
        (extent[:, 0] > 400.0)
        & (low[:, 2] > 397.97)
        & (high[:, 2] < 578.0)
        & (low[:, 1] > 49.97)
        & (high[:, 1] < 169.97)
        & (low[:, 0] > -216.3)
        & (high[:, 0] < 378.7)
    )
    # Carriage is the gantry head around the nozzle: the block, its rails, and
    # the bracket. The length of that head stays short so a move to the front
    # of the deck does not drag the whole rear rail out the door.
    seam = float(tip[1] + 86.0)
    head = (
        (low[:, 0] >= tip[0] - 70.0)
        & (high[:, 0] <= tip[0] + 70.0)
        & (low[:, 2] >= tip[2] - 140.0)
        & (high[:, 2] <= tip[2] + 120.0)
        & (low[:, 1] >= tip[1] - 2.0)
        & (high[:, 1] <= 239.97)
        & ~beam
    )
    # The old splitter's seam was expressed in raw depth.  After the explicit
    # axis conversion that dimension is robot y, so preserve the same physical
    # partition there instead of accidentally swapping it into robot z.
    pipette = head & (high[:, 1] <= seam)
    carriage = head & (low[:, 1] >= seam - 1.0) & ~pipette
    if min(int(beam.sum()), int(carriage.sum()), int(pipette.sum())) < 40:
        raise RuntimeError(
            f"gantry split failed: beam {int(beam.sum())}, "
            f"carriage {int(carriage.sum())}, pipette {int(pipette.sum())}"
        )

    beam_mm = detailed[beam].copy()
    beam_mm[:, :, 1] -= tip[1]
    carriage_mm = detailed[carriage].copy()
    carriage_mm[:, :, 0] -= tip[0]
    carriage_mm[:, :, 1] -= tip[1]
    pipette_mm = detailed[pipette].copy()
    pipette_mm[:, :, 0] -= tip[0]
    pipette_mm[:, :, 1] -= tip[1]
    pipette_mm[:, :, 2] -= tip[2]
    bottom = pipette_mm.reshape(-1, 3)
    floor = float(bottom[:, 2].min())
    face = bottom[bottom[:, 2] < floor + 0.05]
    face_center = np.array(
        [
            (face[:, 0].min() + face[:, 0].max()) / 2,
            (face[:, 1].min() + face[:, 1].max()) / 2,
            face[:, 2].min(),
        ]
    )
    pipette_mm -= face_center
    # Cut the rear extrusion. Keep the trough, including its floor sheet.
    pipette_mm = _contained(pipette_mm, xlim=70.0, ymin=-48.0, ymax=40.0)
    # The floor sheet is 114 mm wide and sits on many wells at once. Keep the
    # upright bracket and centre it on the needle; the needle is the tip.
    upright = pipette_mm.max(axis=1)[:, 2] >= 8.0
    pipette_mm = pipette_mm[upright]
    pipette_mm[:, :, 1] -= float(pipette_mm[:, :, 1].mean())
    # After the raw-axis correction the legacy reference face is still in the
    # transformed assembly depth until its local centre is removed below;
    # window it there, not with the old raw-axis y cap.
    carriage_mm = _contained(carriage_mm, xlim=70.0, ymin=80.0, ymax=170.0)
    # The rails form a ring. Put the ring's centre on the needle, not the AABB.
    carriage_center = carriage_mm.reshape(-1, 3).mean(axis=0)
    carriage_mm[:, :, 0] -= carriage_center[0]
    carriage_mm[:, :, 1] -= carriage_center[1]
    # Hang the head just under the beam so the needle meets it in view,
    # instead of ending inside the beam.
    beam_bottom = float(beam_mm[:, :, 2].min())
    carriage_mm[:, :, 2] -= float(carriage_mm[:, :, 2].max()) - beam_bottom + 2.0
    # 13 mm leaves the head inside the left skin when the tip is at slot 1.
    _fit_x(carriage_mm, 13.0)
    _fit_x(pipette_mm, 13.0)
    # Floor stays above the wells. The needle geom runs from the site up to it.
    pipette_mm[:, :, 2] += 42.0

    _write_stl(folder / "ot2_beam.stl", beam_mm)
    _write_stl(folder / "ot2_carriage.stl", carriage_mm)
    _write_stl(folder / "ot2_pipette.stl", pipette_mm)
    return {
        "beam": _box_from_mm(beam_mm),
        "carriage": _box_from_mm(carriage_mm),
        "pipette": _box_from_mm(pipette_mm),
    }


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


def _hit(name: str, center: tuple[float, float, float], half: tuple[float, float, float]) -> str:
    """Collision box. Group 3 stays out of the default picture; the mesh is the look."""

    pos = " ".join(_f(v) for v in center)
    size = " ".join(_f(v) for v in half)
    return (
        f'<geom name="{name}" type="box" pos="{pos}" size="{size}" group="3" '
        f'rgba="0.45 0.48 0.50 0.35"/>'
    )


def build_xml(
    deck: Deck,
    placed: list[tuple[str, str, Labware]],
    parts: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]],
) -> str:
    """``placed`` is (geom prefix, slot id, labware)."""

    geoms: list[str] = []
    deck_center = robot_m(
        deck, (deck.size[0] / 2, deck.size[1] / 2, -4.0)
    )
    geoms.append(
        _box("deck_plate", deck_center, (deck.size[0] * MM, deck.size[1] * MM, 8 * MM), "0.80 0.82 0.84 1")
    )
    geoms.append(
        f'<geom name="shell" type="mesh" mesh="shell" material="ot2_shell" '
        f'pos="0 0 0" contype="0" conaffinity="0" group="2"/>'
    )

    for prefix, slot, labware in placed:
        origin = labware_origin(deck, slot, labware)
        pad = robot_m(deck, (origin[0] + labware.x / 2, origin[1] + labware.y / 2, 1.5))
        geoms.append(_box(f"{prefix}_pad", pad, (labware.x * MM, labware.y * MM, 3 * MM), "0.22 0.26 0.30 1"))
        for well_name, well in labware.wells.items():
            center = robot_m(
                deck,
                (
                    origin[0] + well.x,
                    origin[1] + well.y,
                    origin[2] + well.z + well.depth / 2,
                ),
            )
            color = "0.20 0.45 0.82 1" if prefix == "tips" else "0.93 0.78 0.35 1"
            geoms.append(
                _cylinder(
                    f"{prefix}_{well_name}",
                    center,
                    well.radius * MM,
                    well.depth * MM,
                    color,
                )
            )

    trash = deck.trash
    trash_center = robot_m(deck, trash.center)
    geoms.append(
        _box(
            "trash",
            trash_center,
            (trash.size[0] * MM, trash.size[1] * MM, trash.size[2] * MM),
            "0.18 0.18 0.20 1",
        )
    )

    left = robot_m(deck, (0.0, 0.0, 0.0))[0]
    right = robot_m(deck, (deck.size[0], 0.0, 0.0))[0]
    y0 = robot_m(deck, (0.0, -10.0, 0.0))[1]
    y1 = robot_m(deck, (0.0, deck.size[1] + 10.0, 0.0))[1]
    beam_box = _hit("beam_box", *parts["beam"])
    carriage_box = _hit("carriage_box", *parts["carriage"])
    pipette_box = _hit("pipette_box", *parts["pipette"])

    body = f"""
    <body name="bridge" pos="0 0 0">
      <joint name="y" type="slide" axis="0 1 0" range="{_f(y0 - 0.05)} {_f(y1 + 0.05)}"/>
      <geom name="beam" type="mesh" mesh="beam" material="ot2_gantry" contype="0" conaffinity="0" group="2"/>
      {beam_box}
      <body name="carriage" pos="0 0 0">
        <joint name="x" type="slide" axis="1 0 0" range="{_f(left - 0.05)} {_f(right + 0.05)}"/>
        <geom name="carriage" type="mesh" mesh="carriage" material="ot2_gantry" contype="0" conaffinity="0" group="2"/>
        {carriage_box}
        <body name="head" pos="0 0 0">
          <joint name="z" type="slide" axis="0 0 1" range="-0.02 0.28"/>
          <geom name="pipette" type="mesh" mesh="pipette" material="ot2_head" contype="0" conaffinity="0" group="2"/>
          {pipette_box}
          <geom name="needle" type="capsule" fromto="0 0 0.002 0 0 0.20" size="0.0022" rgba="0.78 0.80 0.84 1" contype="0" conaffinity="0" group="2"/>
          <site name="tip" pos="0 0 0" size="0.004"/>
        </body>
      </body>
    </body>
    """

    look = robot_m(deck, (deck.size[0] / 2, deck.size[1] / 2, 80.0))
    return f"""<mujoco model="ot2">
  <compiler angle="radian"/>
  <option gravity="0 0 0"/>
  <visual>
    <global azimuth="128" elevation="-22" offwidth="960" offheight="720"/>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.65 0.65 0.65"/>
  </visual>
  <asset>
    <material name="ot2_shell" rgba="0.82 0.84 0.86 1" specular="0.25" shininess="0.3"/>
    <material name="ot2_gantry" rgba="0.68 0.71 0.74 1" specular="0.2" shininess="0.22"/>
    <material name="ot2_head" rgba="0.55 0.60 0.66 1" specular="0.3" shininess="0.35"/>
    <mesh name="shell" file="ot2_shell.stl" scale="{MM} {MM} {MM}"/>
    <mesh name="beam" file="ot2_beam.stl" scale="{MM} {MM} {MM}"/>
    <mesh name="carriage" file="ot2_carriage.stl" scale="{MM} {MM} {MM}"/>
    <mesh name="pipette" file="ot2_pipette.stl" scale="{MM} {MM} {MM}"/>
  </asset>
  <worldbody>
    <light pos="0.4 -0.4 1.4" dir="-0.2 0.3 -1" diffuse="0.9 0.9 0.88"/>
    <camera name="overview" pos="{_f(look[0] + 0.85)} {_f(look[1] - 0.95)} 0.72" xyaxes="0.72 0.70 0 -0.28 0.30 0.91" fovy="42"/>
    {chr(10).join(geoms)}
    {body}
  </worldbody>
</mujoco>
"""


def write_model(deck: Deck, placed: list[tuple[str, str, Labware]]) -> Path:
    parts = write_gantry_meshes()
    xml_path = EXPORT / "ot2.xml"
    xml_path.write_text(build_xml(deck, placed, parts))
    return xml_path


# ---------------------------------------------------------------- spec model
# The rest of this module builds the scene an analysis drives: named well and
# liquid geoms the player toggles, one head body per loaded mount, and the
# "deck" camera the renderer orbits. It shares flex_scene's Labware type.


def _annulus(book, name: str, center: tuple[float, float], outer_r: float, inner_r: float, z0: float, z1: float, material: str, group: int = 0) -> str:
    """A thin annular mesh with a real open centre, in metres."""

    segments = 28
    outer = [
        (center[0] + outer_r * math.cos(2.0 * math.pi * k / segments), center[1] + outer_r * math.sin(2.0 * math.pi * k / segments))
        for k in range(segments)
    ]
    inner = [
        (center[0] + inner_r * math.cos(2.0 * math.pi * k / segments), center[1] + inner_r * math.sin(2.0 * math.pi * k / segments))
        for k in range(segments)
    ]
    mesh = book.extrusion(f"annulus_{name}", outer, inner, 2, z0, z1)
    return shell.mesh_geom(name, mesh, material, group)


def _tiprack_spec_geoms(item, tip_mesh: str, book) -> list[str]:
    """Rack pad, rack body and one lathed tip per well, local frame.

    The original rack was a dark block with loose cones.  Keep the same
    well-origin geometry and add a thin top lip plus socket collars so the
    tips visibly seat in a rack instead of hovering over a slab.
    """

    lw = item.labware
    mid = (lw.x / 2, lw.y / 2)
    top = lw.top - 11.0
    geoms = [
        _box(f"{item.key}_pad", (mid[0] * MM, mid[1] * MM, 1.5 * MM), (lw.x * MM, lw.y * MM, 3 * MM), RACK_RGBA),
        _box(
            f"body_{item.key}",
            (mid[0] * MM, mid[1] * MM, (3.0 + top) / 2 * MM),
            ((lw.x - 3.0) * MM, (lw.y - 3.0) * MM, (top - 3.0) * MM),
            RACK_RGBA,
        ),
    ]
    edge = 3.0
    for side, lo, hi in (
        ("front", (0.0, 0.0, top - 1.8), (lw.x, edge, top + 0.2)),
        ("back", (0.0, lw.y - edge, top - 1.8), (lw.x, lw.y, top + 0.2)),
        ("left", (0.0, edge, top - 1.8), (edge, lw.y - edge, top + 0.2)),
        ("right", (lw.x - edge, edge, top - 1.8), (lw.x, lw.y - edge, top + 0.2)),
    ):
        geoms.append(shell.rbox(book, f"viz_{item.key}_top_edge_{side}", tuple(v * MM for v in lo), tuple(v * MM for v in hi), "rack_edge", 0.0012, 0))
    # The molded rack has a stepped lower skirt and four feet.  These shallow
    # parts sit outside the well field, so they give the consumable a grounded
    # frame without changing a tip origin or its insertion depth.
    base_h = 5.5
    for side, lo, hi in (
        ("front", (1.5, 0.8, 3.0), (lw.x - 1.5, 3.0, base_h)),
        ("back", (1.5, lw.y - 3.0, 3.0), (lw.x - 1.5, lw.y - 0.8, base_h)),
        ("left", (0.8, 3.0, 3.0), (3.0, lw.y - 3.0, base_h)),
        ("right", (lw.x - 3.0, 3.0, 3.0), (lw.x - 0.8, lw.y - 3.0, base_h)),
    ):
        geoms.append(shell.rbox(book, f"viz_{item.key}_base_{side}", tuple(v * MM for v in lo), tuple(v * MM for v in hi), "rack_edge", 0.0015, 0))
    for corner, cx, cy in (
        ("fl", 4.5, 4.5),
        ("fr", lw.x - 4.5, 4.5),
        ("bl", 4.5, lw.y - 4.5),
        ("br", lw.x - 4.5, lw.y - 4.5),
    ):
        geoms.append(shell.rbox(book, f"viz_{item.key}_foot_{corner}", ((cx - 3.2) * MM, (cy - 3.2) * MM, 1.8 * MM), ((cx + 3.2) * MM, (cy + 3.2) * MM, 4.6 * MM), "rack_edge", 0.0013, 0))
    for name, well in lw.wells.items():
        end = well.z + well.depth - lw.tip_length
        geoms.append(
            f'<geom name="{item.key}_{name}" type="mesh" mesh="{tip_mesh}" '
            f'pos="{_f(well.x * MM)} {_f(well.y * MM)} {_f(end * MM)}" rgba="{TIP_RGBA}" material="ot2_tip_clear"/>'
        )
        geoms.append(
            _annulus(
                book,
                f"viz_{item.key}_socket_{name}",
                (well.x * MM, well.y * MM),
                (well.radius + 1.10) * MM,
                (well.radius + 0.60) * MM,
                (top - 0.3) * MM,
                (top + 7.5) * MM,
                "graphite",
                0,
            )
        )
    return geoms


def _plate_spec_geoms(item, liquid_wells: set[str], book) -> list[str]:
    """Plate or reservoir, local frame: pad, side walls, clear wells, liquid columns."""

    lw = item.labware
    margin = 5.5
    x, y, z = lw.x, lw.y, lw.z
    conical = conical_plate(lw)
    geoms = [
        _box(f"{item.key}_pad", (x / 2 * MM, y / 2 * MM, 0.0012), ((x - 2 * margin) * MM, (y - 2 * margin) * MM, 0.0024), PLATE_RGBA)
    ]
    if conical:
        # Full-skirt PCR plates are hollow underneath their tapered wells.
        # Retain the old analytical pad but do not let it visually cap the
        # cone apex 1.5 mm above the original well bottom.
        geoms[0] = geoms[0].replace("/>", ' group="3"/>')
    rails = (
        ("left", (margin / 2, y / 2, z / 2), (margin, y, z)),
        ("right", (x - margin / 2, y / 2, z / 2), (margin, y, z)),
        ("front", (x / 2, margin / 2, z / 2), (x - 2 * margin, margin, z)),
        ("back", (x / 2, y - margin / 2, z / 2), (x - 2 * margin, margin, z)),
    )
    for name, center, size in rails:
        geoms.append(_box(f"{item.key}_side_{name}", tuple(v * MM for v in center), tuple(v * MM for v in size), PLATE_RGBA))
    # A thin molded base step and corner pads make the plate read as a
    # supported consumable rather than four white rails floating above the
    # deck.  The well definitions and all named proxy geoms remain untouched.
    step_h = 3.2
    for side, lo, hi in (
        ("front", (margin - 1.0, 1.0, 0.8), (x - margin + 1.0, margin + 0.8, step_h)),
        ("back", (margin - 1.0, y - margin - 0.8, 0.8), (x - margin + 1.0, y - 1.0, step_h)),
        ("left", (1.0, margin + 0.8, 0.8), (margin + 0.8, y - margin - 0.8, step_h)),
        ("right", (x - margin - 0.8, margin + 0.8, 0.8), (x - 1.0, y - margin - 0.8, step_h)),
    ):
        geoms.append(shell.rbox(book, f"viz_{item.key}_base_{side}", tuple(v * MM for v in lo), tuple(v * MM for v in hi), "ot2_plate_plastic", 0.0012, 0))
    for corner, cx, cy in (
        ("fl", 4.0, 4.0),
        ("fr", x - 4.0, 4.0),
        ("bl", 4.0, y - 4.0),
        ("br", x - 4.0, y - 4.0),
    ):
        geoms.append(shell.rbox(book, f"viz_{item.key}_foot_{corner}", ((cx - 2.8) * MM, (cy - 2.8) * MM, 0.7 * MM), ((cx + 2.8) * MM, (cy + 2.8) * MM, 3.0 * MM), "ot2_plate_plastic", 0.001, 0))
    if len(lw.wells) == 96 and all(w.shape == "circular" for w in lw.wells.values()):
        # A real microplate is a joined perforated deck and skirt, not an
        # array of exposed free-standing tubes. Stitch material between the
        # unchanged openings; never cap the analytical well field.
        geoms.append(shell.mesh_geom(f"viz_{item.key}_perforated_deck", _plate_deck_mesh(book, lw, margin), "ot2_plate_plastic", 0))
        geoms.extend(_plate_index_geoms(item, book))
    for name, well in lw.wells.items():
        geoms.append(_well_spec_geom(item.key, name, well))
        geoms.extend(_well_visual_geoms(item.key, name, well, book, conical=conical))
        # A narrow raised collar makes the top opening and the liquid contact
        # plane legible in the deck view.  It follows the labware JSON exactly;
        # it is only a visual ring and never changes the well target.
        top = (well.z + well.depth) * MM
        if well.shape == "rectangular":
            rx = well.size_x / 2 + 0.55
            ry = well.size_y / 2 + 0.55
            thickness = 0.8
            geoms.extend(
                (
                    _box(f"viz_{item.key}_{name}_rim_l", ((well.x - rx + thickness / 2) * MM, well.y * MM, top), (thickness * MM, well.size_y * MM, 0.8 * MM), "0.70 0.74 0.79 0.72"),
                    _box(f"viz_{item.key}_{name}_rim_r", ((well.x + rx - thickness / 2) * MM, well.y * MM, top), (thickness * MM, well.size_y * MM, 0.8 * MM), "0.70 0.74 0.79 0.72"),
                    _box(f"viz_{item.key}_{name}_rim_f", (well.x * MM, (well.y - ry + thickness / 2) * MM, top), (well.size_x * MM, thickness * MM, 0.8 * MM), "0.70 0.74 0.79 0.72"),
                    _box(f"viz_{item.key}_{name}_rim_b", (well.x * MM, (well.y + ry - thickness / 2) * MM, top), (well.size_x * MM, thickness * MM, 0.8 * MM), "0.70 0.74 0.79 0.72"),
                )
            )
        else:
            geoms.append(
                _annulus(
                    book,
                    f"viz_{item.key}_{name}_rim",
                    (well.x * MM, well.y * MM),
                    (well.radius + 0.30) * MM,
                    well.radius * MM,
                    (well.z + well.depth - 0.12) * MM,
                    (well.z + well.depth + 0.28) * MM,
                    "ot2_plate_plastic",
                    0,
                )
            )
    for name in sorted(liquid_wells):
        geoms.append(_liquid_spec_geom(item.key, name, lw.wells[name], conical=conical))
    return geoms


def conical_plate(labware) -> bool:
    """Only the reference-confirmed NEST 0.1 ml full-skirt PCR plate.

    Preserve its original well coordinates, depth and diameter. The visual
    V-bottom profile is an estimate; this does not redefine engine capacity.
    """
    return labware.load_name == "nest_96_wellplate_100ul_pcr_full_skirt"


def _plate_index_geoms(item, book) -> list[str]:
    """Small printed row/column indices on the solid border, never over wells."""
    from PIL import Image, ImageDraw
    lw = item.labware
    stem = "ot2_plate_index_" + hashlib.sha256(lw.load_name.encode()).hexdigest()[:10]
    columns = Image.new("RGB", (2048, 80), (237, 242, 246))
    rows = Image.new("RGB", (80, 1536), (237, 242, 246))
    dc, dr = ImageDraw.Draw(columns), ImageDraw.Draw(rows)
    for n in range(1, 13):
        w = lw.wells.get(f"A{n}")
        if w is not None:
            shell._text_center(dc, (w.x / lw.x * 2048, 40), str(n), shell._font(49), (67, 77, 91))
    for name in "ABCDEFGH":
        w = lw.wells.get(name + "1")
        if w is not None:
            shell._text_center(dr, (40, (lw.y - w.y) / lw.y * 1536), name, shell._font(49), (67, 77, 91))
    book.texture(stem + "_cols", columns, specular=.05)
    book.texture(stem + "_rows", rows, specular=.05)
    z = (lw.z + .035) * MM
    # label_mesh normally faces -Y; -90 degrees around X puts it face-up.
    q = ' quat="0.70710678 -0.70710678 0 0"'
    out = []
    for suffix, pos, size in (
        ("cols", (lw.x / 2 * MM, (lw.y - 2.8) * MM, z), (lw.x * MM, 4 * MM)),
        ("rows", (2.8 * MM, lw.y / 2 * MM, z), (4 * MM, lw.y * MM)),
    ):
        g = shell.mesh_geom(f"viz_{item.key}_index_{suffix}", book.label_mesh(size), stem + "_" + suffix, 0, pos)
        out.append(g.replace("/>", q + "/>"))
    return out


def _plate_deck_mesh(book, lw, margin: float) -> str:
    """One joined sheet with actual circular openings at the source wells.

    Rectangular cells meet edge to edge; each cell is stitched to its hole.
    Explicit corner rays avoid chamfer gaps between unequal edge cells.
    """
    from sim.flex_shell import _MeshBuilder

    xs = sorted({w.x for w in lw.wells.values()})
    ys = sorted({w.y for w in lw.wells.values()})
    cells = []
    for w in lw.wells.values():
        ix, iy = xs.index(w.x), ys.index(w.y)
        x0 = (xs[ix - 1] + w.x) / 2 if ix else margin
        x1 = (w.x + xs[ix + 1]) / 2 if ix + 1 < len(xs) else lw.x - margin
        y0 = (ys[iy - 1] + w.y) / 2 if iy else margin
        y1 = (w.y + ys[iy + 1]) / 2 if iy + 1 < len(ys) else lw.y - margin
        cells.append((w.x, w.y, w.radius + .12, x0, y0, x1, y1, w.z + w.depth - .6))
    key = "ot2_plate_deck_" + hashlib.sha256(json.dumps(cells).encode()).hexdigest()[:12]

    def write(path):
        mesh = _MeshBuilder()
        for cx, cy, r, x0, y0, x1, y1, top in cells:
            angles = {round(2 * math.pi * k / 32, 12) for k in range(32)}
            angles.update(round(math.atan2(y - cy, x - cx) % (2 * math.pi), 12) for x in (x0, x1) for y in (y0, y1))
            angles = sorted(angles)
            outer, hole = [], []
            for a in angles:
                dx, dy = math.cos(a), math.sin(a)
                tx = ((x1 - cx) if dx > 0 else (x0 - cx)) / dx if abs(dx) > 1e-12 else math.inf
                ty = ((y1 - cy) if dy > 0 else (y0 - cy)) / dy if abs(dy) > 1e-12 else math.inf
                t = min(tx, ty)
                outer.append((cx + t * dx, cy + t * dy))
                hole.append((cx + r * dx, cy + r * dy))
            for z, sign in ((top - .9, -1), (top, 1)):
                n = np.array([0., 0., sign])
                o = [mesh.add(np.array([x, y, z]) * MM, n) for x, y in outer]
                h = [mesh.add(np.array([x, y, z]) * MM, n) for x, y in hole]
                for k in range(len(angles)):
                    j = (k + 1) % len(angles)
                    mesh.tri(o[k], o[j], h[j], n)
                    mesh.tri(o[k], h[j], h[k], n)
            for loop, inward in ((outer, False), (hole, True)):
                for k, (x, y) in enumerate(loop):
                    xx, yy = loop[(k + 1) % len(loop)]
                    n = np.array([yy - y, x - xx, 0.])
                    n = n / np.linalg.norm(n) * (-1 if inward else 1)
                    a = mesh.add(np.array([x, y, top - .9]) * MM, n)
                    b = mesh.add(np.array([xx, yy, top - .9]) * MM, n)
                    c = mesh.add(np.array([xx, yy, top]) * MM, n)
                    d = mesh.add(np.array([x, y, top]) * MM, n)
                    mesh.tri(a, b, c, n); mesh.tri(a, c, d, n)
        mesh.write(path)
    return book._mesh(key, write)


def well_liquid_geometry(well, volume_ul: float, conical: bool = False):
    """Visual liquid only; ledger volumes/capacity stay in the protocol model.

    A V-bottom uses a thin free-surface disk at its estimated cone height,
    avoiding the old full-radius cylinder protruding through the taper.
    """
    if not conical:
        return liquid_column(well, min(volume_ul / well.area_mm2(), well.depth))
    depth, radius = well.depth, well.radius
    height = min(depth, (3 * max(0., volume_ul) * depth * depth / (math.pi * radius * radius)) ** (1 / 3))
    disk = min(.30, max(.001, height * .25))
    # Fit the whole thin disk inside the taper, including its lower edge.
    # Using the free-surface radius for its full thickness clips the wall at
    # small volumes, even though its centre is inside the cone.
    disk_radius = max(.002, radius * max(0., height - disk) / depth * .96)
    return ((well.x * MM, well.y * MM, (well.z + height - disk / 2) * MM),
            (disk_radius * MM, disk * MM / 2, 0.))


def _well_spec_geom(key: str, name: str, well) -> str:
    """Keep the original named well proxy, hidden from the beauty render.

    The proxy remains the same primitive, frame, size, name, and rgba used by
    target/clearance code.  Group 3 is MuJoCo's non-default debug group, so it
    cannot cap the opening in the rendered deck view.  The visible well is
    built separately below as a hollow wall plus an inset floor.
    """

    center = (well.x * MM, well.y * MM, (well.z + well.depth / 2) * MM)
    if well.shape == "rectangular":
        return _box(f"{key}_{name}", center, (well.size_x * MM, well.size_y * MM, well.depth * MM), WELL_RGBA).replace("/>", ' group="3"/>')
    return _cylinder(f"{key}_{name}", center, well.radius * MM, well.depth * MM, WELL_RGBA).replace("/>", ' group="3"/>')


def _well_visual_geoms(key: str, name: str, well, book, conical: bool = False) -> list[str]:
    """Build a shallow, readable open well around the unchanged well proxy.

    The inner opening keeps the labware definition's radius/rectangle and its
    full z span.  The floor is recessed at the definition's well bottom, so a
    nozzle can be seen entering a cavity rather than meeting a translucent cap.
    These names start with ``viz_`` and therefore stay out of protocol target
    lookup and the analytical clearance sweep.
    """

    top = (well.z + well.depth) * MM
    bottom = well.z * MM
    floor_h = min(0.0006, max(0.0002, well.depth * MM * 0.08))
    floor_z = bottom + floor_h / 2
    floor_rgba = "0.65 0.69 0.73 1"
    if well.shape == "rectangular":
        wall = 0.00055
        sx = well.size_x * MM
        sy = well.size_y * MM
        outer_x, outer_y = sx + 2 * wall, sy + 2 * wall
        cx, cy = well.x * MM, well.y * MM
        wall_h = well.depth * MM
        wall_geoms = [
            shell.rbox(book, f"viz_{key}_{name}_wall_l", (cx - outer_x / 2, cy - outer_y / 2, bottom), (cx - sx / 2, cy + outer_y / 2, bottom + wall_h), "ot2_plate_plastic", 0.00018, 0),
            shell.rbox(book, f"viz_{key}_{name}_wall_r", (cx + sx / 2, cy - outer_y / 2, bottom), (cx + outer_x / 2, cy + outer_y / 2, bottom + wall_h), "ot2_plate_plastic", 0.00018, 0),
            shell.rbox(book, f"viz_{key}_{name}_wall_f", (cx - sx / 2, cy - outer_y / 2, bottom), (cx + sx / 2, cy - sy / 2, bottom + wall_h), "ot2_plate_plastic", 0.00018, 0),
            shell.rbox(book, f"viz_{key}_{name}_wall_b", (cx - sx / 2, cy + sy / 2, bottom), (cx + sx / 2, cy + outer_y / 2, bottom + wall_h), "ot2_plate_plastic", 0.00018, 0),
        ]
        wall_geoms.append(_box(f"viz_{key}_{name}_floor", (cx, cy, floor_z), (sx, sy, floor_h), floor_rgba))
        return wall_geoms

    if conical:
        from sim.flex_shell import write_lathe
        # The cone apex and mouth remain at the source bottom/top. Wall
        # thickness and the taper are visual estimates, not calibrated CAD.
        profile = [(.30 * MM, bottom), ((well.radius + .12) * MM, top),
                   (well.radius * MM, top), (.05 * MM, bottom), (.30 * MM, bottom)]
        mesh = book._mesh(f"ot2_pcr_cone_{round(well.radius * 100)}_{round(well.depth * 100)}_{round(well.z * 100)}", lambda path: write_lathe(path, profile, seg=32))
        return [shell.mesh_geom(f"viz_{key}_{name}_wall", mesh, "ot2_plate_plastic", 0, (well.x * MM, well.y * MM, 0.)),
                _cylinder(f"viz_{key}_{name}_floor", (well.x * MM, well.y * MM, bottom - .0001), .30 * MM, .0002, floor_rgba)]
    return [
        _annulus(
            book,
            f"viz_{key}_{name}_wall",
            (well.x * MM, well.y * MM),
            (well.radius + 0.12) * MM,
            well.radius * MM,
            bottom,
            top,
            "ot2_plate_plastic",
            0,
        ),
        _cylinder(
            f"viz_{key}_{name}_floor",
            (well.x * MM, well.y * MM, floor_z),
            max(0.20, well.radius - 0.10) * MM,
            floor_h,
            floor_rgba,
        ),
    ]


def _liquid_spec_geom(key: str, name: str, well, conical: bool = False) -> str:
    """Hidden at first; the player sizes and colours it as liquid moves."""

    pos, size = well_liquid_geometry(well, well.area_mm2(), conical=conical)
    kind = "box" if well.shape == "rectangular" else "cylinder"
    dims = size if kind == "box" else size[:2]
    return (
        f'<geom name="{key}_liquid_{name}" type="{kind}" pos="{" ".join(_f(v) for v in pos)}" '
        f'size="{" ".join(_f(v) for v in dims)}" rgba="0.24 0.47 0.85 0"/>'
    )


# ---------------------------------------------------------------- modules


def module_top_mm(definition: dict) -> float:
    """Fixed/closed module envelope above its slot, for crossing clearance.

    ``dimensions.bareOverallHeight`` covers the bare module, but engaged
    magnets reach ``labwareOffset.z + config.maxEngageHeight``. For the
    The thermocycler's upright lid is avoided in XY, rather than pretending
    the pipette's Z stroke can rise above its documented 312 mm open height.
    """

    dims = definition["dimensions"]
    if "maxEngageHeight" in definition.get("config", {}):
        return max(
            dims["bareOverallHeight"],
            definition["labwareOffset"]["z"] + definition["config"]["maxEngageHeight"],
        )
    if "lidHeight" in dims:
        from sim.ot2_thermocycler import V1_CLOSED_HEIGHT_MM
        return V1_CLOSED_HEIGHT_MM
    return dims["bareOverallHeight"]


def thermocycler_lid_poses(definition: dict, child) -> tuple[tuple, tuple]:
    """Reference-based GEN1 outer lid poses, module-local mm."""
    from sim.ot2_thermocycler import thermocycler_v1_lid_poses
    return thermocycler_v1_lid_poses(definition, child)


def _module_rbox(book, prefix: str, name: str, lo_mm, hi_mm, material: str, radius_mm: float = 1.5) -> str:
    """Rounded visual-only module detail in a module-local mm frame.

    These parts start with ``viz_mod_``. OT-2's clearance sweep includes them
    alongside the original module proxies, preserving the labware interface
    while checking the extra visible supports and moving lid skins.
    """

    lo = tuple(float(v) * MM for v in lo_mm)
    hi = tuple(float(v) * MM for v in hi_mm)
    return shell.rbox(book, f"viz_{prefix}_{name}", lo, hi, material, radius_mm * MM, 0)


def _module_casing_geoms(mod, book) -> list[str]:
    """White side skins and a dark short control end, from product views.

    The original full-body proxy stays hidden in group 3 and in clearance.
    The vent field has real gaps with a recessed dark backing; port depths,
    panel thickness and knob details are illustrative, not internal CAD.
    """
    d = mod.definition
    x, y = (float(d["dimensions"][k]) for k in ("xDimension", "yDimension"))
    h = float(d["labwareOffset"]["z"])
    p = mod.prefix
    parts = (
        ("case_floor", (0, 0, 0), (x, y, 2), "graphite"),
        ("case_side_front", (1.5, 0, 1.5), (x, 2, h), "gantry_white"),
        ("case_side_back", (1.5, y - 2, 1.5), (x, y, h), "gantry_white"),
        ("case_end", (x - 2, 2, 1.5), (x, y - 2, h), "gantry_white"),
        ("case_top", (2, 2, h - 2), (x - 2, y - 2, h), "matte_black"),
    )
    g = [_module_rbox(book, p, n, lo, hi, mat, .8) for n, lo, hi, mat in parts]
    if mod.model.startswith("temperature"):
        # Product photos put the grille on the short x=0 end, not a patch
        # beneath the long-side plate edge. Eight rows/eleven columns are
        # an estimated readable grille, not a documented hole count.
        for n, lo, hi in (
            ("control_bottom", (-.6, 2, 2), (1.5, y - 2, 12)),
            ("control_top", (-.6, 2, 68), (1.5, y - 2, h)),
            ("control_left", (-.6, 2, 12), (1.5, 7, 68)),
            ("control_right", (-.6, y - 7, 12), (1.5, y - 2, 68)),
            ("vent_backing", (5, 5, 9), (6, y - 5, 72)),
        ):
            g.append(_module_rbox(book, p, n, lo, hi, "graphite", .4))
        for k in range(9):
            z = 12 + 7 * k
            g.append(_module_rbox(book, p, f"grille_row_{k}", (-.6, 7, z), (1.5, y - 7, z + 1.3), "graphite", .2))
        for k in range(12):
            yy = 7 + (y - 14) * k / 11
            g.append(_module_rbox(book, p, f"grille_col_{k}", (-.6, yy - .65, 12), (1.5, yy + .65, 68), "graphite", .2))
    else:
        g.append(_module_rbox(book, p, "control_end", (-.6, 2, 2), (1.5, y - 2, h), "graphite", .8))
        # The manual tray-adjustment knob is a static exterior feature.
        c = (y * .5, h - 12)
        g.append(shell.cyl(f"viz_{p}_adjuster_seat", (-1.2 * MM, c[0] * MM, c[1] * MM), (.5 * MM, c[0] * MM, c[1] * MM), 10 * MM, "matte_black", 0))
        g.append(shell.cyl(f"viz_{p}_adjuster", (-5 * MM, c[0] * MM, c[1] * MM), (-1 * MM, c[0] * MM, c[1] * MM), 8 * MM, "steel", 0))
    return g


def _module_spec_geoms(mod, book) -> list[str]:
    """Module body plus evidence-based OT-2 visual layers, module-local mm.

    The vendored schema-3 dimensions and authoritative labware origins remain
    the interface. Slot-relative child/pin positions are converted into the
    module body's local frame; the lid is a simplified reference-based panel.
    Original proxies and extra visible layers both participate in clearance.
    """

    d = mod.definition
    dims = d["dimensions"]
    platform = d["labwareOffset"]["z"]
    x, y = dims["xDimension"], dims["yDimension"]
    geoms: list[str] = []
    prefix = mod.prefix

    def child_bounds() -> tuple[float, float, float, float]:
        if mod.child is not None:
            return tuple(float(v) for v in mod.child[:4])
        off = d["labwareOffset"]
        return (
            float(off["x"]),
            float(off["y"]),
            float(off["x"] + dims["labwareInterfaceXDimension"]),
            float(off["y"] + dims["labwareInterfaceYDimension"]),
        )

    if "lidHeight" in dims:
        # Thermocycler: retain the original named open chassis/body/block
        # geometry for checks.  The real V1 silhouette has a black front fascia,
        # side skins, a recessed plate deck and a rounded dark lid; the small
        # layers below make those features readable without claiming TC2.
        h = dims["bareOverallHeight"]
        t = 8.0
        walls = (
            ("floor", (x / 2, y / 2, t / 2), (x, y, t)),
            ("wall_front", (x / 2, t / 2, h / 2), (x, t, h)),
            ("wall_back", (x / 2, y - t / 2, h / 2), (x, t, h)),
            ("wall_left", (t / 2, y / 2, h / 2), (t, y - 2 * t, h)),
            ("wall_right", (x - t / 2, y / 2, h / 2), (t, y - 2 * t, h)),
        )
        for part, c, size in walls:
            geoms.append(_box(f"{prefix}_{part}", tuple(v * MM for v in c), tuple(v * MM for v in size), MOD_RGBA))
        off = d["labwareOffset"]
        cx0, cy0, cx1, cy1 = child_bounds()
        bx, by = cx0, cy0
        bwd, blen = dims["labwareInterfaceXDimension"], dims["labwareInterfaceYDimension"]
        # Plate base on the OT-2 sits the legacy 10.7 mm below labwareOffset.z
        # (engine ``_OFFSET_ON_TC_OT2``); the block fills up to it.
        top = off["z"] - 10.7
        geoms.append(
            _box(
                f"{prefix}_block",
                ((bx + bwd / 2) * MM, (by + blen / 2) * MM, (top - 5.0) * MM),
                (bwd * MM, blen * MM, 10 * MM),
                MOD_HOT_RGBA,
            )
        )
        # A closed top deck surrounds the plate opening. The old open box
        # exposed a floating block far below its plate; the plate datum itself
        # is retained and the 10 mm hot block now supports that exact base.
        for name, lo, hi in (
            ("front", (0, 0, h - 1.7), (x, cy0 - 1, h + .3)),
            ("back", (0, cy1 + 1, h - 1.7), (x, y, h + .3)),
            ("left", (0, cy0 - 1, h - 1.7), (cx0 - 1, cy1 + 1, h + .3)),
            ("right", (cx1 + 1, cy0 - 1, h - 1.7), (x, cy1 + 1, h + .3)),
        ):
            if all(b > a for a, b in zip(lo, hi)):
                geoms.append(_module_rbox(book, prefix, f"chassis_top_{name}", lo, hi, "matte_black", 1.2))
        # Black inset around the plate interface.  It remains outside the
        # plate's well field and reads as the removable block surround.
        geoms.extend(
            (
                _module_rbox(book, prefix, "deck_front", (cx0 - 3.0, cy0 - 4.5, platform - 1.0), (cx1 + 3.0, cy0 + 1.5, platform + 1.7), "matte_black", 2.0),
                _module_rbox(book, prefix, "deck_back", (cx0 - 3.0, cy1 - 1.5, platform - 1.0), (cx1 + 3.0, cy1 + 4.5, platform + 1.7), "matte_black", 2.0),
                _module_rbox(book, prefix, "deck_left", (cx0 - 4.5, cy0 + 1.0, platform - 1.0), (cx0 + 1.5, cy1 - 1.0, platform + 1.7), "matte_black", 2.0),
                _module_rbox(book, prefix, "deck_right", (cx1 - 1.5, cy0 + 1.0, platform - 1.0), (cx1 + 4.5, cy1 - 1.0, platform + 1.7), "matte_black", 2.0),
            )
        )
        # Front status/control fascia and two rows of shallow ventilation
        # slots.  They are on the fixed front wall, so they remain valid while
        # the lid geom follows Scene's existing dynamic pose.
        geoms.append(_module_rbox(book, prefix, "front_fascia", (10.0, -0.5, 13.0), (x - 10.0, 0.8, h - 12.0), "graphite", 2.0))
        for row, z in enumerate((24.0, 32.0, 40.0, 48.0, 56.0)):
            for col, xx in enumerate((18.0, 29.0, x - 29.0, x - 18.0)):
                geoms.append(_module_rbox(book, prefix, f"front_vent_{row}_{col}", (xx - 2.6, -0.9, z - 1.1), (xx + 2.6, -0.5, z + 1.1), "aluminum_dark", 0.7))
        from sim.ot2_thermocycler import thermocycler_v1_geoms
        geoms.extend(thermocycler_v1_geoms(mod, book, prefix, mod.child))
        for side, xx in (("l", 0.0), ("r", x - 2.0)):
            geoms.append(_module_rbox(book, prefix, f"case_side_{side}", (xx, 2.0, 2.0), (xx + 2.0, y - 2.0, h - 1.0), "gantry_white", 1.0))
        return geoms

    # Magnetic / temperature: retain the full named body as the dimensional
    # proxy.  Only add shallow top/side layers around the child interface.
    geoms.append(_box(f"{prefix}_body", (x / 2 * MM, y / 2 * MM, platform / 2 * MM), (x * MM, y * MM, platform * MM), MOD_RGBA).replace("/>", ' group="3"/>'))
    geoms.extend(_module_casing_geoms(mod, book))

    if mod.model.startswith("magnetic"):
        cx0, cy0, cx1, cy1 = child_bounds()
        # OT-2 magnetic photos show a dark raised plate tray with adjustable
        # brackets on the long edges.  The open center leaves every labware
        # well and the animated magnetic pins visible.
        geoms.extend(
            (
                _module_rbox(book, prefix, "top_inset", (4.0, 3.0, platform - 0.6), (x - 4.0, y - 3.0, platform + 0.15), "graphite", 2.0),
                _module_rbox(book, prefix, "tray_front", (0.0, cy0 - 1.0, platform + 0.8), (x, cy0 + 3.6, platform + 5.0), "matte_black", 1.6),
                _module_rbox(book, prefix, "tray_back", (0.0, cy1 - 2.6, platform + 0.8), (x, min(y, cy1 + 3.6), platform + 5.0), "matte_black", 1.6),
                _module_rbox(book, prefix, "tray_left", (0.0, cy0 + 1.0, platform + 0.8), (cx0 + 3.6, cy1 - 1.0, platform + 4.0), "matte_black", 1.4),
                _module_rbox(book, prefix, "tray_right", (cx1 - 2.6, cy0 + 1.0, platform + 0.8), (x, cy1 - 1.0, platform + 4.0), "matte_black", 1.4),
            )
        )
        # Two shallow bracket pads at each end are visible in the product
        # silhouette, but stay outside the plate's interior footprint.
        for side, xx in (("l", 3.0), ("r", x - 3.0)):
            geoms.append(_module_rbox(book, prefix, f"bracket_{side}", (xx - 3.2, cy0 + 1.0, platform + 3.4), (xx + 3.2, cy1 - 1.0, platform + 8.0), "frame_dark", 1.8))
        # Fixed rear supports reach the documented bare module height.
        # The earlier low rim used platform height and its Y centre was
        # halved a second time, putting the strip over the loaded plate.
        for side, xx in (("l", 3.0), ("r", x - 3.0)):
            geoms.append(_module_rbox(book, prefix, f"rear_support_{side}", (xx - 2.8, cy1 + .4, platform - 1), (xx + 2.8, y, dims["bareOverallHeight"]), "graphite", .7))
        # The original rim is retained below for the clearance proxy.
    elif mod.model.startswith("temperature"):
        cx0, cy0, cx1, cy1 = child_bounds()
        # The temperature module has a wide side/control wing beside the
        # 128 mm labware interface.  This layered top cap and front fascia
        # match the black top/vented control side seen in official photos
        # without covering the loaded plate or changing its offset.
        # The module's long body corner lies beyond its slot. Once the slot
        # offset is converted correctly, the control wing can be to the left
        # of the plate, rather than an invented extension over its right edge.
        if cx0 > x - cx1:
            wing_x0, wing_x1 = 3.5, cx0 - 2.0
        else:
            wing_x0, wing_x1 = cx1 + 2.0, x - 3.5
        geoms.extend(
            (
                _module_rbox(book, prefix, "top_cap", (wing_x0, 5.0, platform - 0.5), (wing_x1, y - 5.0, platform + 2.0), "matte_black", 2.0),
                _module_rbox(book, prefix, "top_cap_edge", (wing_x0 - 1.0, 3.0, platform + 1.2), (wing_x1 + 1.0, y - 3.0, platform + 3.6), "graphite", 1.4),
            )
        )
        # Reference photos show a top display on the control wing. Keep its
        # lens unlit: this exterior model does not simulate temperature and
        # must not present a fabricated current reading or heating status.
        wx, wy = (wing_x0 + wing_x1) / 2, y / 2
        geoms.append(_module_rbox(book, prefix, "display_lens", (wx - 11, wy - 8, platform + 3.65), (wx + 11, wy + 8, platform + 3.9), "display_dark", .5))
        # Narrow datum shoulders around the interface make the supported plate
        # contact readable from above but leave the child footprint unchanged.
        geoms.extend(
            (
                _module_rbox(book, prefix, "interface_front", (cx0 - 1.8, cy0 - 2.5, platform + 0.8), (cx1 + 1.8, cy0 + 1.0, platform + 2.6), "graphite", 1.0),
                _module_rbox(book, prefix, "interface_back", (cx0 - 1.8, cy1 - 1.0, platform + 0.8), (cx1 + 1.8, cy1 + 2.5, platform + 2.6), "graphite", 1.0),
            )
        )

    if dims.get("overLabwareHeight", 0) > 0 and mod.child is not None:
        # The magnetic module rises overLabwareHeight above its platform;
        # retain the named strip along the back edge for the original proxy.
        y0 = min(mod.child[3] + .4, y - .5)
        rim_top = float(dims["bareOverallHeight"])
        rim_bottom = max(platform, rim_top - float(dims["overLabwareHeight"]))
        geoms.append(
            _box(
                f"{prefix}_rim",
                (x / 2 * MM, (y0 + y) / 2 * MM, (rim_bottom + rim_top) / 2 * MM),
                (x * MM, (y - y0) * MM, (rim_top - rim_bottom) * MM),
                MOD_RGBA,
            )
        )
    if mod.pins:
        # Pin count and placement are not in any module definition; the
        # planner puts one pin per loaded plate column, between the outer
        # rows. Length covers config.maxEngageHeight plus 10 mm of guide
        # inside the body; retracted tops hide 0.6 mm below the platform.
        length = d["config"]["maxEngageHeight"] + 10.0
        for k, (px, py) in enumerate(mod.pins):
            geoms.append(
                _cylinder(
                    f"{prefix}_pin{k}",
                    (px * MM, py * MM, (platform - 0.6 - length / 2) * MM),
                    1.2 * MM,
                    length * MM,
                    MOD_PIN_RGBA,
                )
            )
    return geoms


def _head_body(mount: str, spec, tip, tip_mesh: str | None, book) -> str:
    """One mounted pipette: look geoms, needles, per-nozzle tips and the sites.

    The body origin is nozzle A. The look geoms come from ``ot2_shell`` in the
    real model's shape (``spec.model``) and land in group 0, not the gantry's
    2: the follow close-up hides group 2 (shell, beam) to see the deck, and
    the pipette has to survive that. The analytical needles stay because they
    are the tip-like geoms the clearance check exempts at an aimed well, but
    every model variant puts those capsules in hidden group 3. The visible
    shaft/nozzle comes from the capacity- and generation-specific skins in
    ``ot2_shell``; P300 GEN2 retains its photo-backed hollow nozzle while
    other capacities use their narrower estimate. The shell's duplicate
    nozzle cones are skipped.
    A mounted tip is
    the same lathe the racks use, its point ``reach_mm`` below the nozzle.
    """

    tool = f"pipette_{mount}"
    model = spec.model or "p300_single_gen2"
    tip_names = []
    geoms = shell.pipette_body(book, model, prefix=tool, include_nozzles=False)
    # A mounted head has a short rear slide shoe that follows its own Z
    # stroke into the fixed carriage guide.  The fixed guide is intentionally
    # stopped around z=.324 m in ``ot2_shell`` so an empty mount cannot read as
    # a pair of forks below the instrument.  ``Scene.apply`` updates this
    # visual-only box; the head origin, joint, sites and analytical needles do
    # not move or change.
    follower_y0 = shell.PIPETTE_Y[1] + 0.0005
    follower_y1 = shell.MOUNT_Y + 0.026
    follower_bottom = shell.PIPETTE_TOP
    follower_top = shell.FIXED_GUIDE_Z0
    follower_center = (follower_bottom + follower_top) / 2
    follower_half_y = (follower_y1 - follower_y0) / 2
    geoms.append(
        f'<geom name="{tool}_mount_follower" type="box" '
        f'pos="0 {_f((follower_y0 + follower_y1) / 2)} {_f(follower_center)}" '
        f'size="0.011 {_f(follower_half_y)} {_f((follower_top - follower_bottom) / 2)}" '
        f'material="steel" group="2" contype="0" conaffinity="0"/>'
    )
    n = spec.channels
    for k in range(n):
        y = -k * PITCH_MM * MM
        # This capsule is an analytical clearance proxy, not a universal
        # 43-mm product surface. Keep its stable name/geometry for checks, but
        # hide it for every supported pipette so it cannot obscure the
        # model-specific nozzle skin.
        needle_group = ' group="3"'
        geoms.append(
            f'<geom name="{tool}_needle_{k}" type="capsule" fromto="0 {_f(y)} 0.002 0 {_f(y)} 0.045" '
            f'size="0.0022" rgba="0.78 0.80 0.84 1" contype="0" conaffinity="0"{needle_group}/>'
        )
        if tip is None:
            continue
        name = f"{tool}_tip" if n == 1 else f"{tool}_tip_{NOZZLE_ROWS[k]}"
        tip_names.append(name)
        geoms.append(
            f'<geom name="{name}" type="mesh" mesh="{tip_mesh}" '
            f'pos="0 {_f(y)} {_f(-tip.reach_mm * MM)}" rgba="{TIP_RGBA}" material="ot2_tip_clear" contype="0" conaffinity="0"/>'
        )
        geoms.append(
            f'<geom name="{name}_liquid" type="capsule" pos="0 {_f(y)} {_f(-tip.reach_mm * MM / 2)}" '
            f'size="0.0015 {_f(tip.reach_mm * MM / 2)}" rgba="0.3 0.5 0.9 0" contype="0" conaffinity="0"/>'
        )
    end_z = -tip.reach_mm * MM if tip is not None else 0.0
    sites = [
        f'<site name="tip_{mount}" pos="0 0 0" size="0.004"/>',
        f'<site name="tip_{mount}_end" pos="0 0 {_f(end_z)}" size="0.004"/>',
    ]
    sites += [
        f'<site name="noz_{mount}_{k}" pos="0 {_f(-k * PITCH_MM * MM)} 0" size="0.003"/>'
        for k in range(n)
    ]
    return (
        f'<body name="head_{mount}" pos="{_f(spec.dx * MM)} 0 0">\n'
        f'  <joint name="{spec.joint}" type="slide" axis="0 0 1" range="{HEAD_Z_RANGE_M[0]} {HEAD_Z_RANGE_M[1]}"/>\n'
        f'  {chr(10).join("  " + g for g in geoms)}\n'
        f'  {chr(10).join("  " + s for s in sites)}\n'
        f'</body>'
    )


def _camera(name: str, pos, target, fovy: float) -> str:
    axes = camera_axes(np.array(pos, dtype=float), np.array(target, dtype=float))[:, :2].T.ravel()
    return (
        f'<camera name="{name}" pos="{" ".join(_f(v) for v in pos)}" '
        f'xyaxes="{" ".join(_f(v) for v in axes)}" fovy="{fovy:g}"/>'
    )


def deck_camera_pose(deck: Deck) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """In front of the open door, above the deck edge, looking at the machine.

    The former close framing clipped the upper rails and made the scene read
    as a floating deck.  Keep the same front-facing orientation but give the
    enclosure and working surface enough breathing room to be read together.
    """

    # The JSON's full deck dimensions do not have the shell's centre. Frame
    # the actual enclosure so its header and raised home carriage stay visible.
    look = ((shell.X0 + shell.X1) / 2, (shell.Y0 + shell.Y1) / 2, 0.255)
    pos = (look[0] + 0.18, shell.Y0 - 1.22, 0.82)
    return pos, look


def _deck_visual_geoms(deck: Deck, book) -> list[str]:
    """Machined deck surface, 11 slot recesses, and fixed-trash surround.

    Slot locations and dimensions are read from the vendored OT-2 JSON.  The
    geometry is visual-only and sits a few millimetres above the existing deck
    plate, so no official slot origin or target coordinate is altered.
    """

    geoms: list[str] = []
    sx, sy = (float(v) for v in deck.slot_size)
    for slot, p in sorted(deck.slots.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99):
        if not slot.isdigit() or slot == "12":
            continue
        x0, y0, _ = robot_m(deck, p)
        x1, y1, _ = robot_m(deck, (p[0] + sx, p[1] + sy, 0.0))
        # Recess under the removable labware, with a raised machined edge.
        geoms.append(shell.rbox(book, f"deck_slot_{slot}_recess", (x0 + 0.002, y0 + 0.002, 0.0003), (x1 - 0.002, y1 - 0.002, 0.0017), "deck_slot", 0.0018, 0))
        edge = 0.003
        for side, lo, hi in (
            ("front", (x0, y0, 0.0017), (x1, y0 + edge, 0.0050)),
            ("back", (x0, y1 - edge, 0.0017), (x1, y1, 0.0050)),
            ("left", (x0, y0 + edge, 0.0017), (x0 + edge, y1 - edge, 0.0050)),
            ("right", (x1 - edge, y0 + edge, 0.0017), (x1, y1 - edge, 0.0050)),
        ):
            geoms.append(shell.rbox(book, f"deck_slot_{slot}_edge_{side}", lo, hi, "deck_rim", 0.0012, 0))
        # Four shallow registration holes are visible around an empty slot;
        # their placement is a visual cue only, not a new addressable area.
        for corner, cx, cy in (
            ("fl", x0 + 0.010, y0 + 0.010),
            ("fr", x1 - 0.010, y0 + 0.010),
            ("bl", x0 + 0.010, y1 - 0.010),
            ("br", x1 - 0.010, y1 - 0.010),
        ):
            geoms.append(shell.cyl(f"deck_slot_{slot}_locator_{corner}", (cx, cy, 0.0015), (cx, cy, 0.0043), 0.0017, "deck_locator", 0))

    # The deck is removable and has a visible front lip and rear datum edge.
    # The vendored deck JSON is slightly larger than the measured OT-2 shell
    # in this visual axis order.  Clamp only these beauty surfaces to the
    # inner frame; slot origins, slot dimensions, trash coordinates, and all
    # target/proxy geometry still use the official deck JSON unchanged.
    raw_x0, raw_y0, _ = robot_m(deck, (0.0, 0.0, 0.0))
    raw_x1, raw_y1, _ = robot_m(deck, (deck.size[0], deck.size[1], 0.0))
    x0 = max(raw_x0, shell.X0 + shell.WALL)
    x1 = min(raw_x1, shell.X1 - shell.WALL)
    y0 = max(raw_y0, shell.Y0 + shell.WALL)
    y1 = min(raw_y1, shell.Y1 - shell.WALL)
    geoms.extend(
        (
            shell.rbox(book, "deck_front_lip", (x0, y0 - 0.004, 0.0004), (x1, y0 + 0.004, 0.009), "deck_rim", 0.002, 0),
            shell.rbox(book, "deck_back_lip", (x0, y1 - 0.004, 0.0004), (x1, y1 + 0.004, 0.009), "deck_rim", 0.002, 0),
            shell.rbox(book, "deck_side_lip_left", (x0 - 0.004, y0, 0.0004), (x0 + 0.004, y1, 0.009), "deck_rim", 0.002, 0),
            shell.rbox(book, "deck_side_lip_right", (x1 - 0.004, y0, 0.0004), (x1 + 0.004, y1, 0.009), "deck_rim", 0.002, 0),
            shell.rbox(book, "deck_support_front", (x0 + 0.018, y0 + 0.006, -0.006), (x1 - 0.018, y0 + 0.014, -0.001), "deck_locator", 0.0015, 0),
            shell.rbox(book, "deck_support_back", (x0 + 0.018, y1 - 0.014, -0.006), (x1 - 0.018, y1 - 0.006, -0.001), "deck_locator", 0.0015, 0),
        )
    )
    return geoms


def _trash_visual_geoms(book, name: str, origin: tuple[float, float, float], size: tuple[float, float, float]) -> list[str]:
    """Readable removable OT-2 trash insert with a lip and visible cavity."""

    x0, y0, z0 = origin
    sx, sy, sz = size
    t = 0.0035
    return [
        shell.rbox(book, f"trash_{name}_floor", (x0 + t, y0 + t, z0), (x0 + sx - t, y0 + sy - t, z0 + t), "bin_dark", 0.002, 0),
        shell.rbox(book, f"trash_{name}_wall_front", (x0, y0, z0), (x0 + sx, y0 + t, z0 + sz), "bin_dark", 0.0025, 0),
        shell.rbox(book, f"trash_{name}_wall_back", (x0, y0 + sy - t, z0), (x0 + sx, y0 + sy, z0 + sz), "bin_dark", 0.0025, 0),
        shell.rbox(book, f"trash_{name}_wall_left", (x0, y0 + t, z0), (x0 + t, y0 + sy - t, z0 + sz), "bin_dark", 0.0025, 0),
        shell.rbox(book, f"trash_{name}_wall_right", (x0 + sx - t, y0 + t, z0), (x0 + sx, y0 + sy - t, z0 + sz), "bin_dark", 0.0025, 0),
        shell.rbox(book, f"trash_{name}_inner_floor", (x0 + t + 0.002, y0 + t + 0.002, z0 + 0.008), (x0 + sx - t - 0.002, y0 + sy - t - 0.002, z0 + 0.012), "bin_inner", 0.001, 0),
        shell.rbox(book, f"trash_{name}_liner_front", (x0 + t + 0.006, y0 + t + 0.006, z0 + 0.012), (x0 + sx - t - 0.006, y0 + t + 0.008, z0 + sz - 0.012), "bin_liner", 0.001, 0),
        shell.rbox(book, f"trash_{name}_liner_back", (x0 + t + 0.006, y0 + sy - t - 0.008, z0 + 0.012), (x0 + sx - t - 0.006, y0 + sy - t - 0.006, z0 + sz - 0.012), "bin_liner", 0.001, 0),
        shell.rbox(book, f"trash_{name}_liner_left", (x0 + t + 0.006, y0 + t + 0.008, z0 + 0.012), (x0 + t + 0.008, y0 + sy - t - 0.008, z0 + sz - 0.012), "bin_liner", 0.001, 0),
        shell.rbox(book, f"trash_{name}_liner_right", (x0 + sx - t - 0.008, y0 + t + 0.008, z0 + 0.012), (x0 + sx - t - 0.006, y0 + sy - t - 0.008, z0 + sz - 0.012), "bin_liner", 0.001, 0),
        shell.rbox(book, f"trash_{name}_rim_front", (x0 - 0.003, y0 - 0.003, z0 + sz - 0.006), (x0 + sx + 0.003, y0 + t + 0.003, z0 + sz + 0.004), "bin_rim", 0.002, 0),
        shell.rbox(book, f"trash_{name}_rim_back", (x0 - 0.003, y0 + sy - t - 0.003, z0 + sz - 0.006), (x0 + sx + 0.003, y0 + sy + 0.003, z0 + sz + 0.004), "bin_rim", 0.002, 0),
        shell.rbox(book, f"trash_{name}_rim_left", (x0 - 0.003, y0 + t, z0 + sz - 0.006), (x0 + t + 0.003, y0 + sy - t, z0 + sz + 0.004), "bin_rim", 0.002, 0),
        shell.rbox(book, f"trash_{name}_rim_right", (x0 + sx - t - 0.003, y0 + t, z0 + sz - 0.006), (x0 + sx + 0.003, y0 + sy - t, z0 + sz + 0.004), "bin_rim", 0.002, 0),
        shell.rbox(book, f"trash_{name}_front_badge", (x0 + sx * 0.28, y0 - 0.001, z0 + sz * 0.20), (x0 + sx * 0.72, y0 + 0.001, z0 + sz * 0.28), "deck_rim", 0.001, 0),
    ]


def build_spec_xml(deck: Deck, spec, book, rack_meshes: dict[str, str], head_meshes: dict[str, str]) -> str:
    geoms: list[str] = []
    raw_x0, raw_y0, _ = robot_m(deck, (0.0, 0.0, 0.0))
    raw_x1, raw_y1, _ = robot_m(deck, (deck.size[0], deck.size[1], 0.0))
    visual_x0 = max(raw_x0, shell.X0 + shell.WALL)
    visual_x1 = min(raw_x1, shell.X1 - shell.WALL)
    visual_y0 = max(raw_y0, shell.Y0 + shell.WALL)
    visual_y1 = min(raw_y1, shell.Y1 - shell.WALL)
    deck_center = ((visual_x0 + visual_x1) / 2, (visual_y0 + visual_y1) / 2, -0.004)
    geoms.append(_box("deck_plate", deck_center, (visual_x1 - visual_x0, visual_y1 - visual_y0, 0.008), "0.80 0.82 0.84 1"))
    geoms.extend(_deck_visual_geoms(deck, book))
    # Procedural enclosure: the look plus the invisible "shell" box whose AABB
    # is the clearance envelope (same bounds the STL shell mesh used to give).
    enclosure = shell.enclosure_xml(book)
    rails = shell.rails_xml(book)
    geoms.append(shell.shell_bound())

    bodies: list[str] = []
    liquid_by_key: dict[str, set[str]] = {}
    for key, well in spec.liquid_wells:
        liquid_by_key.setdefault(key, set()).add(well)
    for item in spec.placed:
        local = (
            _tiprack_spec_geoms(item, rack_meshes[item.key], book)
            if item.labware.is_tiprack
            else _plate_spec_geoms(item, liquid_by_key.get(item.key, set()), book)
        )
        origin = robot_m(deck, item.origin)
        bodies.append(
            f'<body name="{item.key}" pos="{" ".join(_f(v) for v in origin)}">\n'
            + "\n".join(f"  {g}" for g in local)
            + "\n</body>"
        )

    for mod in spec.modules:
        origin = robot_m(deck, mod.origin)
        bodies.append(
            f'<body name="{mod.prefix}" pos="{" ".join(_f(v) for v in origin)}">\n'
            + "\n".join(f"  {g}" for g in _module_spec_geoms(mod, book))
            + "\n</body>"
        )

    for bin_ in spec.trash:
        # Open-topped bin, with a rounded lip and visible inner cavity.  The
        # protocol's trash origin/size is unchanged; these are look geoms only.
        origin = robot_m(deck, bin_.origin_mm)
        size = tuple(v * MM for v in bin_.size_mm)
        geoms.extend(_trash_visual_geoms(book, bin_.name, origin, size))

    left = robot_m(deck, (0.0, 0.0, 0.0))[0]
    # Furthest gantry x a command can ask for: the grid's right edge, reached
    # by whichever mount sits furthest left of the gantry.
    grid_right = max(p[0] for p in deck.slots.values()) + deck.slot_size[0]
    right = robot_m(deck, (grid_right, 0.0, 0.0))[0] + max((-m.dx for m in spec.mounts), default=0.0) * MM
    y0 = robot_m(deck, (0.0, -10.0, 0.0))[1]
    y1 = robot_m(deck, (0.0, deck.size[1] + 10.0, 0.0))[1]
    parts = shell.hit_boxes()
    beam_box = _hit("beam_box", *parts["beam"])
    carriage_box = _hit("carriage_box", *parts["carriage"])
    tips_by_tool = spec.tips
    heads = "\n".join(
        _head_body(m.mount, m, tips_by_tool.get(m.tool), head_meshes.get(m.tool), book) for m in spec.mounts
    )
    bridge = shell.bridge_geoms(book)
    carriage = shell.carriage_geoms(book)
    body = f"""
    <body name="bridge" pos="0 0 0">
      <joint name="y" type="slide" axis="0 1 0" range="{_f(y0 - 0.05)} {_f(y1 + 0.05)}"/>
      {bridge}
      {beam_box}
      <body name="carriage" pos="0 0 0">
        <joint name="x" type="slide" axis="1 0 0" range="{_f(left - 0.05)} {_f(right + 0.05)}"/>
        {carriage}
        {carriage_box}
        {heads}
      </body>
    </body>
    """

    deck_pos, deck_look = deck_camera_pose(deck)
    look = ((shell.X0 + shell.X1) / 2, (shell.Y0 + shell.Y1) / 2, 0.26)
    overview = _camera("overview", (look[0] + 0.97, shell.Y0 - 0.94, 0.87), look, 42)
    deck_cam = _camera("deck", deck_pos, deck_look, 33)
    # The builders above register meshes and textures lazily, so the asset
    # block has to be rendered after they have all run.
    assets = book.asset_xml()
    return f"""<mujoco model="ot2">
  <compiler angle="radian"/>
  <option gravity="0 0 0"/>
  {shell.visual_xml()}
  <default>
    <geom contype="0" conaffinity="0"/>
  </default>
  <asset>
    {shell.materials_xml()}
    <material name="ot2_plate_plastic" rgba="0.93 0.95 0.965 1" specular="0.10" shininess="0.12"/>
    <material name="ot2_tip_clear" rgba="0.84 0.90 0.94 0.40" specular="0.12" shininess="0.25"/>
    {assets}
  </asset>
  <worldbody>
    {shell.scene_lighting()}
    {overview}
    {deck_cam}
    {chr(10).join(geoms)}
    {enclosure}
    {rails}
    {chr(10).join(bodies)}
    {body}
  </worldbody>
</mujoco>
"""


def _ot2_tip_mesh(book, length_mm: float, top_diameter_mm: float) -> str:
    """An open OT-2 disposable tip, with its outlet at the original origin.

    Length and mouth bore come from the loaded labware definition. The
    thin-wall/taper/shoulder are appearance estimates from OT-2 tip/rack
    photographs, not a measured internal-volume model. Do not reuse Flex's
    closed generic profile or alter the shared Flex asset generator.
    """
    from sim.flex_shell import write_lathe

    length = float(length_mm)
    bore = float(top_diameter_mm) / 2
    wall = min(0.35, bore * 0.13)
    top = bore + wall
    outlet = min(0.42, top * 0.14)
    outer = [
        (outlet, 0.0), (top * 0.20, length * 0.05),
        (top * 0.45, length * 0.30), (top * 0.72, length * 0.62),
        (top * 0.90, length * 0.80), (top, length * 0.88),
        (top, length * 0.97), (top + 0.18, length * 0.975),
        (top + 0.18, length),
    ]
    # Walk back down the inner wall and close through an annular outlet.
    # No face crosses either mouth: a nozzle can visibly enter the socket.
    inner = [
        (bore, length), (bore, length * 0.88),
        (top * 0.90 - wall, length * 0.80),
        (top * 0.72 - wall, length * 0.62),
        (top * 0.45 - min(wall, 0.22), length * 0.30),
        (top * 0.20 - min(wall, 0.14), length * 0.05),
        (outlet - min(0.14, outlet * 0.4), 0.0),
        outer[0],
    ]
    profile = [(r * MM, z * MM) for r, z in outer + inner]
    key = f"ot2_open_tip_{round(length * 100)}_{round(top_diameter_mm * 100)}"
    return book._mesh(key, lambda path: write_lathe(path, profile, seg=32))


def write_spec_model(deck: Deck, spec, folder: Path) -> Path:
    """Lathed tips, procedural shell geoms and ``ot2.xml`` for one analysis."""

    from sim.flex_shell import AssetBook

    book = AssetBook(folder)
    rack_meshes = {
        item.key: _ot2_tip_mesh(book, item.labware.tip_length, 2 * item.labware.wells["A1"].radius)
        for item in spec.placed
        if item.labware.is_tiprack
    }
    head_meshes = {
        tool: _ot2_tip_mesh(book, tip.length_mm, tip.top_diameter_mm)
        for tool, tip in spec.tips.items()
    }
    shell.make_textures(book)
    xml_path = folder / "ot2.xml"
    xml_path.write_text(build_spec_xml(deck, spec, book, rack_meshes, head_meshes))
    return xml_path
