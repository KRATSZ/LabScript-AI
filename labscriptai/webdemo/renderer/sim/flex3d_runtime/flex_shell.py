"""Visual shell for the Flex (OT-3) MuJoCo scene.

The moving skeleton lives in ``flex_scene.py``: ``y`` (crossbar), ``x`` (slider)
and one Z joint per mounted tool: ``z`` (1000 uL, right mount), ``z_8``
(8-channel, left mount), ``z_gripper`` (extension mount). This module only
produces the look: enclosure, deck fixtures, and the parts that hang on those
joints. Everything is visual (contype 0).

What the reference photos show, and what this model does with it
----------------------------------------------------------------
Front (``front-touchscreen``, ``educational``) and front three-quarter
(``flex-hero``, ``flex-physical-components``) views are the only exterior
angles the vendor publishes. So:

* modelled from those photos: the black front with rounded top corners, the
  logo above a long blue status light, the door glass and its two hinges in
  the top corners, the handle slot under the deck, the touchscreen standing
  proud of the frame at gantry height, the silver frame that wraps both sides
  and the top, the large side window, handle caps and handle recesses on the
  base, the USB strip on the right rear pillar, small feet.
* left side: the vendor has no left photo. It mirrors the right side, minus
  the USB strip.
* back: no photo at all. One plain silver panel that follows the frame
  profile.
* cable chain, rear connectors: not modelled.

Overall size is 87 x 69 x 84 cm (W x D x H) from NOTES.md. Slot size and
positions come from ``cad/flex/deck/ot3_standard.json`` through
``flex_scene.Deck``. Where the deck sits inside the shell (height above the
floor, gaps to the walls) is a judgement call, not a measurement.

Gantry. The photos put the crossbar across the middle of the window: a tall
aluminium beam whose ends ride on silver rail covers that show through the
side windows. Its depth is never visible; it is kept at 4 cm so the home pose
at the back of the deck still fits. The head is a dark mounting plate with a
column behind it, rising above the beam as in ``front-touchscreen``.
The pipettes and gripper hang on the plate's front face and slide out below
it; the plate stops well above the tallest labware.

Mounts, from NOTES.md: a Flex carries two pipettes (any mix of 1-channel and
8-channel) or one 96-channel across both mounts, plus a gripper on the
extension mount beside them. The scene builds one pipette per mount the
protocol actually loads (``SceneSpec.tools``); an empty mount stays empty.
Pipettes follow ``pipettes-hero``: black front with the drop logo
and the volume label, silver sides, a long black ejector shaft on the
1-channel. The 50 uL 1-channel from the hero photo is not mounted; it would
take one of these two mounts. The 8-channel nozzle row runs along y (front
to back) because the labware JSON lays wells A..H of column 1 along y; the
photos show the row head-on, so they do not settle the direction.

The gripper follows ``gripper-components.png``: a thin white slab, long front
to back, with the rounded notch at the back, base with the calibration pin,
attachment screws, black jaws, white paddles. ``gripperV1.3.json`` fixes the
rest: the jaw centre sits 74 mm in front of the mount and the jaws close along
y (calibration pins at y ±54 mm), 60-92 mm apart. Opentrons grips labware by
its y dimension (``get_gripper_width_specs``: ``targetY = dimensions.y``), so
the paddles meet the plate's front and back faces. The jaws slide on their own
joints (``jaw_f`` front, ``jaw_b`` back) along a guide under the base.

Disposable tips: ``tip_mesh`` is a lathed 200 uL Flex tip. When a protocol
gives a tip length, each pipette carries one hidden tip per nozzle that the
player shows after ``pickUpTip``, plus a ``tip_end`` site at the tip's end.

Labels (logo, touchscreen, pipette fronts) are thin meshes with UVs: MuJoCo
only maps a 2D texture cleanly onto the z faces of a box.

Geom groups (the viewer shows 0-2 by default; toggle with the number keys):
    0 machine, deck, labware   1 opaque shell and its inner liners   2 glass
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

MM = 0.001

OUTER_W, OUTER_D, OUTER_H = 0.87, 0.69, 0.84
WALL_SIDE, WALL_FRONT, WALL_BACK, WALL_TOP = 0.04, 0.03, 0.03, 0.03
BASE_BELOW_DECK = 0.16
FOOT_H = 0.012

# The touchscreen stands this far proud of the black front.
FRONT_RECESS = 0.014
# Black front (door frame) depth; it ends where the interior starts.
FRONT_DEPTH = WALL_FRONT - FRONT_RECESS
# Room left of column 1 and in front of row D. Opentrons gives the deck plate
# 76.6 mm in front of row D (``cornerOffsetFromOrigin``) and ``camera-default``
# shows a deep lip there; the gripper needs it to reach a front-row plate
# while the pipettes work the H row. The left gap lets the gripper centre
# reach column 1.
GAP_LEFT = 0.140
GAP_FRONT = 0.085

TOP_FRAME = 0.60
SILL = 0.03
POST_W = 0.045
CORNER_TOP_R = 0.05
CORNER_BOTTOM_R = 0.02
# Silver frame sits this far inside the black front's outline.
SHELL_INSET = 0.0015
DECK_UNDER = -0.008
SCREEN_Z = 0.40

RAIL_Z_M = 0.40
BEAM_DY = (0.026, 0.066)
BEAM_H = 0.11
# Front face of the head plate. Every tool's back face sits on it.
MOUNT_Y = 0.012
BLOCK_DY = (0.020, 0.074)
BLOCK_H = BEAM_H + 0.024
BLOCK_DX = (-0.09, 0.098)
TRUCK_W = 0.025
HEAD_TOP = 0.60

PIPETTE_W = 0.046
PIPETTE_DY = (-0.032, MOUNT_Y)
# Deep enough to sit over all eight nozzles, no further forward than nozzle H.
PIPETTE_8_DY = (-0.066, MOUNT_Y)
PIPETTE_H = 0.28
PIPETTE_BOTTOM = 0.07
# Nozzle A of the left 8-channel sits 54 mm left of the right 1-channel nozzle:
# mount offsets -13.5 / 40.5 mm in ``defaults_ot3.py``, equal ``nozzleOffset`` x.
PIPETTE_8_DX = -0.054
# Nozzle A of a right-mount 8-channel is the right 1-channel nozzle, at x = 0.
# Jaw centre 71.5 mm right of the 1-channel nozzle: gripper mount offset 84.55 mm
# plus ``baseOffsetFromMount`` 19.5 mm, less the right nozzle at 32.5 mm.
GRIPPER_DX = 0.0715
GRIPPER_W = 0.036
# Half-distance between paddle inner faces, from ``jawWidth`` 60-92 mm.
JAW_OPEN = 0.046
JAW_CLOSED_MIN = 0.030
# Jaw bar thickness along y, and paddle width along x.
JAW_PAD = 0.005
PADDLE_W = 0.022
# On the robot the jaw centre is 4.6 mm in front of the 1-channel nozzle, from a
# gripper mount 48 mm behind the pipette mounts. This head has one flat mount
# plate 12 mm behind the nozzles, so the jaw centre sits 40 mm forward: the
# open back jaw then stays in front of that plate.
JAW_FORWARD = -0.040
GRIPPER_FRONT = JAW_FORWARD - JAW_OPEN - JAW_PAD
NOZZLE_PITCH = 0.009

Z_RANGE = (-0.01, 0.21)
# Lowest edge of the head plate. Every tool still overlaps it by 5 cm at the
# bottom of its stroke, and it clears the 99 mm tip rack.
Z_PLATE_BOTTOM = 0.25
Z_PARK = Z_RANGE[1]


def _f(value: float) -> str:
    return f"{value:.5f}"


def _v(*values: float) -> str:
    return " ".join(_f(v) for v in values)


@dataclass(frozen=True)
class Tool:
    """One Z-moving tool. ``site`` sits at (dx, dy, dz) from the carriage origin when its joint is 0."""

    body: str
    joint: str
    site: str
    dx: float
    dy: float
    dz: float


TOOLS = (
    Tool("pipette_8", "z_8", "tip_8_A", PIPETTE_8_DX, 0.0, 0.0),
    Tool("pipette_1000", "z", "tip", 0.0, 0.0, 0.0),
    # 1000 uL single on the left mount: same x offset as the 8-channel, its own Z joint.
    Tool("pipette_1000_left", "z_left", "tip_left", PIPETTE_8_DX, 0.0, 0.0),
    # 8-channel on the right mount: nozzle A at the right single's x, its own Z joint.
    Tool("pipette_8_right", "z_8_right", "tip_8r_A", 0.0, 0.0, 0.0),
    Tool("gripper", "z_gripper", "gripper_center", GRIPPER_DX, JAW_FORWARD, 0.0),
)
TOOL_BY_NAME = {t.body: t for t in TOOLS}
NOZZLE_ROWS = "ABCDEFGH"


@dataclass(frozen=True)
class Layout:
    """Outer shell and interior, robot frame, meters."""

    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float
    ix0: float
    ix1: float
    iy0: float
    iy1: float
    iz1: float
    slot_x: tuple[float, float]
    slot_y: tuple[float, float]

    @classmethod
    def for_deck(cls, deck) -> "Layout":
        slot_w, slot_d = deck.slot_size
        origins = [
            ((pos[0] + deck.corner[0]) * MM, (pos[1] + deck.corner[1]) * MM)
            for pos in deck.slots.values()
        ]
        sx = (min(o[0] for o in origins), max(o[0] for o in origins) + slot_w * MM)
        sy = (min(o[1] for o in origins), max(o[1] for o in origins) + slot_d * MM)
        ix0 = sx[0] - GAP_LEFT
        iy0 = sy[0] - GAP_FRONT
        x0 = ix0 - WALL_SIDE
        y0 = iy0 - WALL_FRONT
        x1 = x0 + OUTER_W
        y1 = y0 + OUTER_D
        z0 = -BASE_BELOW_DECK
        z1 = z0 + OUTER_H
        return cls(
            x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1,
            ix0=ix0, ix1=x1 - WALL_SIDE, iy0=iy0, iy1=y1 - WALL_BACK,
            iz1=z1 - WALL_TOP, slot_x=sx, slot_y=sy,
        )

    @property
    def outer_size(self) -> tuple[float, float, float]:
        return (self.x1 - self.x0, self.y1 - self.y0, self.z1 - self.z0)

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def view_target(self) -> tuple[float, float, float]:
        return (self.center_x, (self.y0 + self.y1) / 2, 0.25)

    @property
    def post_right_inner(self) -> float:
        return self.x1 - POST_W

    @property
    def home_x_max(self) -> float:
        """Largest carriage x that keeps the gripper clear of the right front post."""

        reach = GRIPPER_DX + GRIPPER_W / 2 + 0.002
        return self.post_right_inner - 0.005 - reach

    @property
    def center_y_inner(self) -> float:
        return (self.iy0 + self.iy1) / 2

    @property
    def rail_x(self) -> tuple[float, float]:
        return (self.ix0 + 0.02, self.ix1 - 0.02)

    def joint_ranges(self) -> dict[str, tuple[float, float]]:
        """Slide ranges that keep every hung part clear of trucks and walls."""

        left_truck = self.rail_x[0] + TRUCK_W / 2
        right_truck = self.rail_x[1] - TRUCK_W / 2
        margin = 0.005
        return {
            "x": (left_truck - BLOCK_DX[0] + margin, right_truck - BLOCK_DX[1] - margin),
            "y": (self.iy0 + 0.03, self.iy1 - BLOCK_DY[1] - 0.003),
            "z": Z_RANGE,
            "z_8": Z_RANGE,
            "z_left": Z_RANGE,
            "z_8_right": Z_RANGE,
            "z_gripper": Z_RANGE,
            "jaw_f": (-JAW_OPEN - 0.0005, -JAW_CLOSED_MIN),
            "jaw_b": (JAW_CLOSED_MIN, JAW_OPEN + 0.0005),
            "labware_x": (-0.45, 0.65),
            "labware_y": (-0.25, 0.75),
            "labware_z": (-0.005, 0.25),
        }


# ---------------------------------------------------------------- meshes


def _write_obj(path: Path, verts, norms, faces, uvs=None) -> None:
    out = [f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in verts]
    out += [f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}" for n in norms]
    if uvs is None:
        out += [f"f {a}//{a} {b}//{b} {c}//{c}" for a, b, c in faces]
    else:
        out += [f"vt {u:.5f} {v:.5f}" for u, v in uvs]
        out += [f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}" for a, b, c in faces]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


class _MeshBuilder:
    """Vertices with per-vertex normals; triangles are wound to face a given direction."""

    def __init__(self) -> None:
        self.verts: list[np.ndarray] = []
        self.norms: list[np.ndarray] = []
        self.uvs: list[tuple[float, float]] = []
        self.faces: list[tuple[int, int, int]] = []

    def add(self, p, n, uv=(0.0, 0.0)) -> int:
        self.verts.append(np.asarray(p, dtype=float))
        self.norms.append(np.asarray(n, dtype=float))
        self.uvs.append(uv)
        return len(self.verts)

    def tri(self, a: int, b: int, c: int, facing) -> None:
        pa, pb, pc = self.verts[a - 1], self.verts[b - 1], self.verts[c - 1]
        if np.dot(np.cross(pb - pa, pc - pa), facing) < 0:
            b, c = c, b
        self.faces.append((a, b, c))

    def write(self, path: Path, with_uv: bool = False) -> None:
        _write_obj(path, self.verts, self.norms, self.faces, self.uvs if with_uv else None)


def write_rounded_box(path: Path, size: tuple[float, float, float], radius: float, bands: int = 4) -> None:
    """Rounded box centred on the origin, as an OBJ with smooth normals."""

    half = np.array(size) / 2
    inner = half - radius
    axes: list[np.ndarray] = []
    for i in inner:
        pos = i + np.linspace(0.0, radius, bands + 1)
        axes.append(np.unique(np.concatenate([-pos, pos, [-i, i]])))
    mesh = _MeshBuilder()

    def project(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        q = np.clip(p, -inner, inner)
        d = p - q
        length = np.linalg.norm(d)
        n = d / length if length > 1e-12 else np.array([0.0, 0.0, 1.0])
        return q + radius * n, n

    for axis in range(3):
        u_axis, v_axis = [a for a in range(3) if a != axis]
        for sign in (-1.0, 1.0):
            grid: list[list[int]] = []
            for u in axes[u_axis]:
                row = []
                for v in axes[v_axis]:
                    p = np.zeros(3)
                    p[axis] = sign * half[axis]
                    p[u_axis] = u
                    p[v_axis] = v
                    row.append(mesh.add(*project(p)))
                grid.append(row)
            for a in range(len(grid) - 1):
                for b in range(len(grid[a]) - 1):
                    i00, i01 = grid[a][b], grid[a][b + 1]
                    i10, i11 = grid[a + 1][b], grid[a + 1][b + 1]
                    for tri in ((i00, i10, i11), (i00, i11, i01)):
                        mesh.tri(*tri, mesh.norms[tri[0] - 1])
    mesh.write(path)


def _turn(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _area(poly) -> float:
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))


def _ear_clip(poly: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """Triangulate a simple counter-clockwise polygon."""

    def inside(p, a, b, c) -> bool:
        return _turn(a, b, p) > 1e-14 and _turn(b, c, p) > 1e-14 and _turn(c, a, p) > 1e-14

    idx = list(range(len(poly)))
    tris = []
    while len(idx) > 3:
        n = len(idx)
        for k in range(n):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % n]
            if _turn(poly[a], poly[b], poly[c]) <= 1e-14:
                continue
            if any(inside(poly[j], poly[a], poly[b], poly[c]) for j in idx if j not in (a, b, c)):
                continue
            tris.append((a, b, c))
            idx.pop(k)
            break
        else:
            raise ValueError("profile is not a simple polygon")
    tris.append(tuple(idx))
    return tris


def write_extrusion(
    path: Path,
    outer: list[tuple[float, float]],
    hole: list[tuple[float, float]] | None,
    axis: int,
    lo: float,
    hi: float,
    smooth_deg: float = 40.0,
) -> None:
    """A 2D profile swept along ``axis`` from ``lo`` to ``hi``.

    Profile coordinates are the two remaining axes in increasing order (for
    ``axis=1`` that is (x, z)). ``hole`` must have as many points as ``outer``
    and lie inside it; caps are stitched point to point between the two.
    Edges that turn by less than ``smooth_deg`` share a normal, so arcs shade round.
    """

    ua, va = [a for a in range(3) if a != axis]

    def p3(uv, w) -> np.ndarray:
        p = np.zeros(3)
        p[ua], p[va], p[axis] = uv[0], uv[1], w
        return p

    def n3(nuv) -> np.ndarray:
        n = np.zeros(3)
        n[ua], n[va] = nuv
        return n

    if _area(outer) < 0:
        outer = outer[::-1]
    if hole is not None and _area(hole) < 0:
        hole = hole[::-1]
    mesh = _MeshBuilder()
    for w, sign in ((lo, -1.0), (hi, 1.0)):
        facing = np.zeros(3)
        facing[axis] = sign
        if hole is None:
            ids = [mesh.add(p3(p, w), facing) for p in outer]
            for a, b, c in _ear_clip(outer):
                mesh.tri(ids[a], ids[b], ids[c], facing)
        else:
            oid = [mesh.add(p3(p, w), facing) for p in outer]
            iid = [mesh.add(p3(p, w), facing) for p in hole]
            for k in range(len(outer)):
                k2 = (k + 1) % len(outer)
                mesh.tri(oid[k], oid[k2], iid[k2], facing)
                mesh.tri(oid[k], iid[k2], iid[k], facing)

    cos_lim = math.cos(math.radians(smooth_deg))

    def walls(loop, outward: float) -> None:
        n = len(loop)
        normals = []
        for k in range(n):
            a, b = loop[k], loop[(k + 1) % n]
            du, dv = b[0] - a[0], b[1] - a[1]
            length = math.hypot(du, dv)
            normals.append((outward * dv / length, -outward * du / length))

        def blend(a, b):
            if a[0] * b[0] + a[1] * b[1] < cos_lim:
                return None
            s = (a[0] + b[0], a[1] + b[1])
            length = math.hypot(*s)
            return (s[0] / length, s[1] / length)

        for k in range(n):
            nk = normals[k]
            ns = blend(normals[k - 1], nk) or nk
            ne = blend(nk, normals[(k + 1) % n]) or nk
            a, b = loop[k], loop[(k + 1) % n]
            i0 = mesh.add(p3(a, lo), n3(ns))
            i1 = mesh.add(p3(b, lo), n3(ne))
            i2 = mesh.add(p3(b, hi), n3(ne))
            i3 = mesh.add(p3(a, hi), n3(ns))
            mesh.tri(i0, i1, i2, n3(nk))
            mesh.tri(i0, i2, i3, n3(nk))

    walls(outer, 1.0)
    if hole is not None:
        walls(hole, -1.0)
    mesh.write(path)


def write_lathe(path: Path, profile: list[tuple[float, float]], seg: int = 28) -> None:
    """Revolve an ordered (radius, z) contour; close at the axis or with a hollow wall loop."""

    mesh = _MeshBuilder()
    rings: list[list[int]] = []
    for k, (r, z) in enumerate(profile):
        prev = profile[max(k - 1, 0)]
        nxt = profile[min(k + 1, len(profile) - 1)]
        dr, dz = nxt[0] - prev[0], nxt[1] - prev[1]
        nr, nz = dz, -dr
        length = math.hypot(nr, nz) or 1.0
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            c, s = math.cos(a), math.sin(a)
            ring.append(mesh.add((r * c, r * s, z), (nr / length * c, nr / length * s, nz / length)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        r_mid = (profile[k][0] + profile[k + 1][0]) / 2
        for j in range(seg):
            j2 = (j + 1) % seg
            a = 2 * math.pi * (j + 0.5) / seg
            z_mid = (profile[k][1] + profile[k + 1][1]) / 2
            out = np.array([math.cos(a), math.sin(a), 0.0])
            dz = profile[k + 1][1] - profile[k][1]
            dr = profile[k + 1][0] - profile[k][0]
            facing = out * dz - np.array([0.0, 0.0, 1.0]) * dr
            if np.linalg.norm(facing) < 1e-12:
                facing = np.array([0.0, 0.0, 1.0 if z_mid > profile[0][1] else -1.0])
            if r_mid < 1e-9:
                continue
            i00, i01, i10, i11 = rings[k][j], rings[k][j2], rings[k + 1][j], rings[k + 1][j2]
            mesh.tri(i00, i01, i11, facing)
            mesh.tri(i00, i11, i10, facing)
    mesh.write(path)


def tip_profile(length_mm: float, top_diameter_mm: float) -> list[tuple[float, float]]:
    """Outline of a Flex filter-less tip in meters: narrow cone, then the collar the nozzle seals in."""

    L, r_top = length_mm, top_diameter_mm / 2 + 0.55
    points_mm = [
        (0.0, 0.0),
        (0.42, 0.0),
        (0.75, 3.0),
        (1.55, 0.30 * L),
        (2.35, 0.62 * L),
        (2.75, 0.78 * L),
        (r_top - 0.2, 0.80 * L),
        (r_top - 0.1, 0.97 * L),
        (r_top + 0.35, 0.975 * L),
        (r_top + 0.35, L),
        (0.0, L),
    ]
    return [(r * MM, z * MM) for r, z in points_mm]


def tip_visual_profile(length_mm: float, top_diameter_mm: float) -> list[tuple[float, float]]:
    """Open, thin-wall appearance only; ``tip_profile`` still defines liquid volume.

    The exterior and end planes are unchanged. Wall thickness and the collar
    are illustrative, not a manufacturer CAD or a measured PE bore.
    """

    outer = tip_profile(length_mm, top_diameter_mm)[1:-1]
    inner = [(max(0.10 * MM, r - min(0.35 * MM, 0.45 * r)), z) for r, z in outer]
    return outer + list(reversed(inner)) + [outer[0]]


def write_label(path: Path, width: float, height: float, thickness: float = 0.0004) -> None:
    """Thin slab centred on the origin whose -y face carries the whole texture (u along +x, v along +z)."""

    x, y, z = width / 2, thickness / 2, height / 2
    mesh = _MeshBuilder()
    corner_uv = (0.002, 0.998)
    faces = (
        ((0, -1, 0), [(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        ((0, 1, 0), [(-x, y, -z), (x, y, -z), (x, y, z), (-x, y, z)], None),
        ((-1, 0, 0), [(-x, -y, -z), (-x, y, -z), (-x, y, z), (-x, -y, z)], None),
        ((1, 0, 0), [(x, -y, -z), (x, y, -z), (x, y, z), (x, -y, z)], None),
        ((0, 0, -1), [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z)], None),
        ((0, 0, 1), [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)], None),
    )
    for normal, quad, uvs in faces:
        ids = [mesh.add(p, normal, uvs[i] if uvs else corner_uv) for i, p in enumerate(quad)]
        mesh.tri(ids[0], ids[1], ids[2], normal)
        mesh.tri(ids[0], ids[2], ids[3], normal)
    mesh.write(path, with_uv=True)


def arc(center: tuple[float, float], radius: float, a0: float, a1: float, seg: int = 10) -> list[tuple[float, float]]:
    return [
        (center[0] + radius * math.cos(math.radians(a0 + (a1 - a0) * k / seg)),
         center[1] + radius * math.sin(math.radians(a0 + (a1 - a0) * k / seg)))
        for k in range(seg + 1)
    ]


def rrect(u0: float, u1: float, v0: float, v1: float, r_low: float, r_high: float, seg: int = 10) -> list[tuple[float, float]]:
    """Counter-clockwise rounded rectangle; ``r_low`` on the two v0 corners, ``r_high`` on the v1 corners."""

    r_low, r_high = max(r_low, 0.0005), max(r_high, 0.0005)
    return (
        arc((u0 + r_low, v0 + r_low), r_low, 180, 270, seg)
        + arc((u1 - r_low, v0 + r_low), r_low, 270, 360, seg)
        + arc((u1 - r_high, v1 - r_high), r_high, 0, 90, seg)
        + arc((u0 + r_high, v1 - r_high), r_high, 90, 180, seg)
    )


class AssetBook:
    """Collects mesh and texture files and the asset XML that names them.

    Everything in ``folder`` is generated, so stale files are cleared first.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        for stale in [*folder.glob("*.obj"), *folder.glob("*.png")]:
            stale.unlink()
        self._meshes: dict[str, str] = {}
        self._materials: dict[str, str] = {}

    def _mesh(self, key: str, write) -> str:
        if key not in self._meshes:
            write(self.folder / f"{key}.obj")
            self._meshes[key] = f"{key}.obj"
        return key

    def rbox_mesh(self, size: tuple[float, float, float], radius: float) -> str:
        radius = min(radius, 0.45 * min(size))
        key = "rb_" + "_".join(f"{round(s * 1e4)}" for s in size) + f"_r{round(radius * 1e4)}"
        return self._mesh(key, lambda p: write_rounded_box(p, size, radius))

    def extrusion(self, name: str, outer, hole, axis: int, lo: float, hi: float) -> str:
        return self._mesh(f"ex_{name}", lambda p: write_extrusion(p, outer, hole, axis, lo, hi))

    def tip_mesh(self, length_mm: float, top_diameter_mm: float, hollow: bool = False) -> str:
        """Tip whose mesh origin is its end; the top is ``length_mm`` above."""

        key = f"tip_{round(length_mm * 100)}_{round(top_diameter_mm * 100)}"
        if hollow:
            key += "_open"
        profile = tip_visual_profile if hollow else tip_profile
        return self._mesh(key, lambda p: write_lathe(p, profile(length_mm, top_diameter_mm), seg=40 if hollow else 28))

    def label_mesh(self, size: tuple[float, float]) -> str:
        key = f"lbl_{round(size[0] * 1e4)}_{round(size[1] * 1e4)}"
        return self._mesh(key, lambda p: write_label(p, *size))

    def texture(self, name: str, image: Image.Image, specular: float = 0.15, shininess: float = 0.2, emission: float = 0.0) -> str:
        image.save(self.folder / f"{name}.png")
        self._materials[name] = (
            f'<texture name="{name}_tex" type="2d" file="{name}.png"/>'
            f'<material name="{name}" texture="{name}_tex" specular="{specular}" shininess="{shininess}" emission="{emission}"/>'
        )
        return name

    def asset_xml(self) -> str:
        lines = [f'<mesh name="{name}" file="{file}"/>' for name, file in self._meshes.items()]
        lines += list(self._materials.values())
        return "\n    ".join(lines)


# ---------------------------------------------------------------- geom helpers


def rbox(
    book: AssetBook,
    name: str,
    lo: tuple[float, float, float],
    hi: tuple[float, float, float],
    material: str,
    radius: float = 0.004,
    group: int = 1,
) -> str:
    size = tuple(h - l for l, h in zip(lo, hi))
    center = tuple((h + l) / 2 for l, h in zip(lo, hi))
    mesh = book.rbox_mesh(size, radius)
    return (
        f'<geom name="{name}" type="mesh" mesh="{mesh}" pos="{_v(*center)}" '
        f'material="{material}" group="{group}"/>'
    )


def mesh_geom(name: str, mesh: str, material: str, group: int, pos=(0.0, 0.0, 0.0)) -> str:
    return f'<geom name="{name}" type="mesh" mesh="{mesh}" pos="{_v(*pos)}" material="{material}" group="{group}"/>'


def label(book: AssetBook, name: str, center: tuple[float, float, float], size: tuple[float, float], material: str, group: int = 0) -> str:
    """Textured face looking toward -y, ``size`` = (width along x, height along z)."""

    return mesh_geom(name, book.label_mesh(size), material, group, center)


def cyl(
    name: str,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    radius: float,
    material: str,
    group: int = 0,
) -> str:
    return (
        f'<geom name="{name}" type="cylinder" fromto="{_v(*a)} {_v(*b)}" '
        f'size="{_f(radius)}" material="{material}" group="{group}"/>'
    )


# ---------------------------------------------------------------- textures


CJK_FONTS = (
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
)


def _font(size: int, bold: bool = False, italic: bool = False, light: bool = False, cjk: bool = False) -> ImageFont.ImageFont:
    index = 4 + italic if light else (1 if bold else 0) + (2 if italic else 0)
    for path, idx in (
        *(CJK_FONTS if cjk else ()),
        ("/System/Library/Fonts/Helvetica.ttc", index),
        ("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", 0),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0),
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=idx)
            except OSError:
                continue
    return ImageFont.load_default(size)


def _text_center(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font, fill) -> None:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (left + right) / 2, xy[1] - (top + bottom) / 2), text, font=font, fill=fill)


# Texture backgrounds match the material colour of the surface a label sits on.
PIANO_BLACK = (12, 13, 14)
SATIN_BLACK = (20, 21, 23)


def _logo() -> Image.Image:
    img = Image.new("RGB", (1200, 180), PIANO_BLACK)
    draw = ImageDraw.Draw(img)
    big = _font(128)
    draw.text((8, 18), "opentrons", font=big, fill=(236, 238, 240))
    width = draw.textlength("opentrons", font=big)
    draw.text((width + 30, 18), "FLEX", font=_font(128, italic=True, light=True), fill=(110, 185, 245))
    return img


def _screen(title: str, labware_count: int) -> Image.Image:
    w, h = 880, 550
    img = Image.new("RGB", (w, h), (8, 9, 10))
    draw = ImageDraw.Draw(img)
    pad = 26
    draw.rectangle((pad, pad, w - pad, h - pad), fill=(246, 247, 249))
    draw.text((pad + 26, pad + 22), "LOCAL PREVIEW", font=_font(26), fill=(110, 116, 124))
    title_font = _font(36, bold=True, cjk=not title.isascii())
    while draw.textlength(title, font=title_font) > w - 2 * pad - 230 and len(title) > 4:
        title = title.rstrip("\u2026")[:-1].rstrip() + "\u2026"
    draw.text((pad + 26, pad + 56), title, font=title_font, fill=(22, 26, 32))
    rx, ry, r = w - pad - 140, pad + 54, 28
    draw.ellipse((rx - r, ry - r, rx + r, ry + r), fill=(214, 58, 58))
    draw.line((rx - 10, ry - 10, rx + 10, ry + 10), fill=(255, 255, 255), width=6)
    draw.line((rx - 10, ry + 10, rx + 10, ry - 10), fill=(255, 255, 255), width=6)
    bx = w - pad - 66
    draw.ellipse((bx - r, ry - r, bx + r, ry + r), fill=(0, 108, 250))
    draw.polygon([(bx - 8, ry - 13), (bx - 8, ry + 13), (bx + 14, ry)], fill=(255, 255, 255))
    rows = (
        ("Instruments", "Protocol model", (226, 232, 237), None),
        ("Modules", "Protocol model", (226, 232, 237), None),
        ("Labware", f"{labware_count} on deck", (226, 229, 233), None),
        ("Robot connection", "Not checked", (226, 229, 233), None),
    )
    y = pad + 128
    for title, status, fill, dot in rows:
        draw.rounded_rectangle((pad + 20, y, w - pad - 20, y + 74), 14, fill=fill)
        x_text = pad + 46
        if dot:
            draw.ellipse((pad + 38, y + 23, pad + 66, y + 51), fill=dot)
            draw.line((pad + 45, y + 37, pad + 51, y + 44, pad + 60, y + 30), fill=(255, 255, 255), width=4)
            x_text = pad + 84
        draw.text((x_text, y + 20), title, font=_font(30, bold=True), fill=(22, 26, 32))
        status_font = _font(24)
        draw.text((w - pad - 50 - draw.textlength(status, font=status_font), y + 25), status, font=status_font, fill=(80, 86, 94))
        y += 90
    return img


def _pipette_face(volume: str, channels: str) -> Image.Image:
    """Front of a Flex pipette as in ``pipettes-hero``: drop logo near the top, label near the bottom."""

    w, h = 168, 1092
    img = Image.new("RGB", (w, h), SATIN_BLACK)
    draw = ImageDraw.Draw(img)
    cx, cy, r = w / 2, 112, 38
    grey = (92, 96, 102)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=grey, width=6)
    draw.ellipse((cx - 13, cy - 2, cx + 13, cy + 24), fill=grey)
    draw.polygon([(cx, cy - 24), (cx - 12, cy + 6), (cx + 12, cy + 6)], fill=grey)
    for y in (h * 0.38, h * 0.62):
        draw.ellipse((cx - 6, y - 6, cx + 6, y + 6), fill=(54, 57, 61))
    draw.rounded_rectangle((14, h - 250, w - 14, h - 70), 10, fill=(30, 32, 35))
    _text_center(draw, (cx, h - 214), "FLEX", _font(30, italic=True), (150, 156, 164))
    _text_center(draw, (cx, h - 160), f"{volume} \u00b5L", _font(36, bold=True), (240, 242, 244))
    _text_center(draw, (cx, h - 112), f"{channels}-Channel", _font(24), (170, 176, 182))
    return img


def make_textures(book: AssetBook, layout: Layout, deck, title: str = "Flex Transfer Demo", labware_count: int = 2) -> None:
    """Logo, touchscreen and the deck print. Deck letters follow the JSON slot rows.
    Pipette fronts are made per mounted tool in ``flex_scene.build_xml``."""

    book.texture("logo", _logo(), specular=0.5, shininess=0.8)
    book.texture("screen", _screen(title, labware_count), specular=0.6, shininess=0.9, emission=0.55)

    px_per_m = 2000
    w = round((layout.ix1 - layout.ix0) * px_per_m)
    h = round((layout.iy1 - layout.iy0) * px_per_m)
    deck_img = Image.new("RGB", (w, h), (44, 48, 52))
    draw = ImageDraw.Draw(deck_img)
    font = _font(44, True)
    slot_w, slot_d = deck.slot_size
    rows: dict[str, float] = {}
    cols: dict[str, float] = {}
    for name, pos in deck.slots.items():
        rows[name[0]] = (pos[1] + deck.corner[1] + slot_d / 2) * MM
        cols[name[1:]] = (pos[0] + deck.corner[0] + slot_w / 2) * MM
    ring = (150, 154, 160)
    for letter, y in rows.items():
        px = (layout.slot_x[0] - 0.05 - layout.ix0) * px_per_m
        py = h - (y - layout.iy0) * px_per_m
        draw.ellipse((px - 34, py - 34, px + 34, py + 34), outline=ring, width=4)
        _text_center(draw, (px, py), letter, font, (215, 218, 222))
    for number, x in cols.items():
        px = (x - layout.ix0) * px_per_m
        py = h - (layout.slot_y[1] + 0.05 - layout.iy0) * px_per_m
        draw.ellipse((px - 34, py - 34, px + 34, py + 34), outline=ring, width=4)
        _text_center(draw, (px, py), number, font, (215, 218, 222))
    book.texture("deck", deck_img, specular=0.2, shininess=0.3)


def materials_xml() -> str:
    return """
    <texture name="sky" type="skybox" builtin="flat" rgb1="1 1 1" rgb2="1 1 1" width="512" height="512"/>
    <material name="labware_rack" rgba="0.095 0.112 0.125 1" specular="0.24" shininess="0.20"/>
    <material name="labware_rack_insert" rgba="0.16 0.185 0.20 1" specular="0.35" shininess="0.36"/>
    <material name="labware_tube" rgba="0.62 0.69 0.72 0.14" specular="0.6" shininess="0.66"/>
    <material name="labware_tube_rim" rgba="0.59 0.66 0.69 0.55" specular="0.45" shininess="0.42"/>
    <material name="labware_pe_rack_base" rgba="0.31 0.36 0.38 1" specular="0.25" shininess="0.28"/>
    <material name="labware_pe_rack_body" rgba="0.62 0.67 0.68 1" specular="0.34" shininess="0.38"/>
    <material name="labware_pe_rack_rim" rgba="0.78 0.81 0.81 1" specular="0.40" shininess="0.42"/>
    <material name="labware_pe_rack_insert" rgba="0.30 0.40 0.43 1" specular="0.30" shininess="0.30"/>
    <material name="labware_pe_tip" rgba="0.52 0.59 0.62 1" specular="0.12" shininess="0.18"/>
    <material name="floor" rgba="0.87 0.88 0.895 1" reflectance="0.10" specular="0.1" shininess="0.2"/>
    <material name="piano_black" rgba="0.047 0.051 0.055 1" specular="0.5" shininess="0.8"/>
    <material name="satin_black" rgba="0.078 0.082 0.09 1" specular="0.25" shininess="0.3"/>
    <material name="matte_black" rgba="0.065 0.07 0.075 1" specular="0.12" shininess="0.12"/>
    <material name="recess" rgba="0.02 0.021 0.023 1" specular="0.05" shininess="0.05"/>
    <material name="graphite" rgba="0.17 0.18 0.195 1" specular="0.3" shininess="0.35"/>
    <material name="head_plate" rgba="0.24 0.25 0.27 1" specular="0.45" shininess="0.5"/>
    <material name="charcoal" rgba="0.12 0.125 0.135 1" specular="0.15" shininess="0.2"/>
    <material name="rubber" rgba="0.03 0.03 0.03 1" specular="0.02" shininess="0.05"/>
    <material name="aluminum" rgba="0.76 0.78 0.80 1" specular="0.55" shininess="0.55"/>
    <material name="aluminum_dark" rgba="0.52 0.54 0.57 1" specular="0.45" shininess="0.45"/>
    <material name="rail_cover" rgba="0.76 0.78 0.80 1" specular="0.5" shininess="0.5" emission="0.35"/>
    <material name="beam" rgba="0.88 0.89 0.90 1" specular="0.5" shininess="0.6"/>
    <material name="white" rgba="0.93 0.94 0.95 1" specular="0.35" shininess="0.35"/>
    <material name="chrome" rgba="0.86 0.88 0.90 1" specular="0.9" shininess="0.85" reflectance="0.2"/>
    <material name="glass" rgba="0.70 0.80 0.88 0.10" specular="0.9" shininess="0.95"/>
    <material name="tint" rgba="0.68 0.72 0.75 0.08" specular="0.35" shininess="0.6"/>
    <material name="led_blue" rgba="0.06 0.40 1.0 1" emission="0.65" specular="0"/>
    <material name="led_white" rgba="1 1 1 1" emission="0.9"/>
    <material name="accent_blue" rgba="0.12 0.45 0.90 1" specular="0.3" emission="0.15"/>
    <material name="slot_plate" rgba="0.70 0.72 0.75 1" specular="0.55" shininess="0.5"/>
    <material name="tip_marker" rgba="0.95 0.22 0.15 1" emission="0.3"/>
    <material name="lens" rgba="0.02 0.03 0.05 1" specular="0.9" shininess="0.9"/>
    """


# ---------------------------------------------------------------- enclosure


def chassis_xml(book: AssetBook, layout: Layout, deck) -> str:
    """Static body (frame, panels, deck, rails), then the door and the two side windows."""

    L = layout
    g: list[str] = []
    f0 = L.y0 + FRONT_RECESS
    f1 = f0 + FRONT_DEPTH
    floor_z = L.z0 + FOOT_H
    post_l, post_r = L.x0 + POST_W, L.x1 - POST_W
    cx = L.center_x
    s = SHELL_INSET
    sx0, sx1, sz0, sz1 = L.x0 + s, L.x1 - s, floor_z + s, L.z1 - s
    rt, rb = CORNER_TOP_R - s, CORNER_BOTTOM_R - s
    ys0, ys1 = f1 - 0.002, L.y1 - WALL_BACK

    for i, (fx, fy) in enumerate(
        [(L.x0 + 0.06, L.y0 + 0.06), (L.x1 - 0.06, L.y0 + 0.06), (L.x0 + 0.06, L.y1 - 0.06), (L.x1 - 0.06, L.y1 - 0.06)]
    ):
        g.append(cyl(f"foot_{i}", (fx, fy, L.z0), (fx, fy, floor_z + 0.002), 0.017, "rubber", 1))

    front = rrect(L.x0, L.x1, floor_z, L.z1, CORNER_BOTTOM_R, CORNER_TOP_R)
    window = rrect(post_l, post_r, SILL, TOP_FRAME, 0.012, 0.012)
    g.append(mesh_geom("front_frame", book.extrusion("front_frame", front, window, 1, f0, f1), "piano_black", 1))

    # Silver frame: top arch and base run the full depth; side walls carry the windows.
    top = [(sx0, TOP_FRAME), (L.ix0, TOP_FRAME), (L.ix0, L.iz1), (L.ix1, L.iz1), (L.ix1, TOP_FRAME), (sx1, TOP_FRAME)]
    top += arc((sx1 - rt, sz1 - rt), rt, 0, 90) + arc((sx0 + rt, sz1 - rt), rt, 90, 180)
    base = arc((sx0 + rb, sz0 + rb), rb, 180, 270) + arc((sx1 - rb, sz0 + rb), rb, 270, 360)
    base += [(sx1, SILL), (L.ix1, SILL), (L.ix1, DECK_UNDER), (L.ix0, DECK_UNDER), (L.ix0, SILL), (sx0, SILL)]
    g.append(mesh_geom("shell_top", book.extrusion("shell_top", top, None, 1, ys0, ys1), "aluminum", 1))
    g.append(mesh_geom("shell_base", book.extrusion("shell_base", base, None, 1, ys0, ys1), "aluminum", 1))
    pillar, margin = 0.03, 0.015
    win_y = (ys0 + pillar, ys1 - pillar)
    win_z = (SILL + margin, TOP_FRAME - margin)
    side = rrect(ys0, ys1, SILL, TOP_FRAME, 0.0, 0.0)
    hole = rrect(win_y[0], win_y[1], win_z[0], win_z[1], 0.016, 0.016)
    for name, lo, hi in (("left", sx0, L.ix0), ("right", L.ix1, sx1)):
        g.append(mesh_geom(f"side_{name}_frame", book.extrusion(f"side_{name}", side, hole, 0, lo, hi), "aluminum", 1))
    back = rrect(sx0, sx1, sz0, sz1, rb, rt)
    g.append(mesh_geom("back_panel", book.extrusion("back_panel", back, None, 1, ys1, L.y1), "aluminum", 1))

    led_half = 0.22
    g.append(rbox(book, "led_bar", (cx - led_half, f0 - 0.0012, 0.620), (cx + led_half, f0 + 0.002, 0.6265), "led_blue", 0.0025, 1))
    g.append(label(book, "logo", (cx - led_half + 0.072, f0 - 0.0004, 0.6475), (0.144, 0.0216), "logo", 1))
    g.append(rbox(book, "door_handle", (cx - 0.22, f0 - 0.0015, -0.098), (cx + 0.22, f0 + 0.001, -0.077), "recess", 0.004, 1))
    g.append(rbox(book, "door_handle_lip", (cx - 0.214, f0 - 0.0019, -0.0790), (cx + 0.214, f0 - 0.0010, -0.0776), "graphite", 0.0003, 1))

    screen_x = L.x1 - 0.12
    g.append(rbox(book, "touch_bezel", (screen_x - 0.095, L.y0 + 0.0008, SCREEN_Z - 0.062), (screen_x + 0.095, f0 + 0.002, SCREEN_Z + 0.062), "aluminum", 0.008, 1))
    g.append(label(book, "touch_screen", (screen_x, L.y0 + 0.0005, SCREEN_Z), (0.178, 0.111), "screen", 1))

    for name, x_face, out in (("left", sx0, -1.0), ("right", sx1, 1.0)):
        x_lo, x_hi = sorted((x_face - out * 0.001, x_face + out * (s - 0.0002)))
        for k, (ya, yb) in enumerate(((ys0 + 0.13, ys0 + 0.28), (ys0 + 0.31, ys0 + 0.46))):
            g.append(rbox(book, f"handle_{name}_{k}", (x_lo, ya, -0.122), (x_hi, yb, -0.084), "recess", 0.005, 1))
        for k, y in enumerate((ys0 + 0.05, ys1 - 0.05)):
            a, b = (x_face - out * 0.001, y, -0.096), (x_face + out * (s - 0.0002), y, -0.096)
            g.append(cyl(f"handle_ring_{name}_{k}", a, (x_face + out * (s - 0.0006), y, -0.096), 0.0145, "graphite", 1))
            g.append(cyl(f"handle_cap_{name}_{k}", a, b, 0.0115, "chrome", 1))
    usb_x = (sx1 - 0.001, L.x1 - 0.0002)
    g.append(rbox(book, "usb_strip", (usb_x[0], ys1 - 0.023, 0.07), (usb_x[1], ys1 - 0.007, 0.19), "recess", 0.003, 1))
    for k in range(3):
        z = 0.095 + 0.035 * k
        g.append(rbox(book, f"usb_port_{k}", (usb_x[0], ys1 - 0.019, z), (usb_x[1] + 0.0001, ys1 - 0.011, z + 0.012), "aluminum_dark", 0.001, 1))

    g.append(rbox(book, "liner_back", (L.ix0, L.iy1 - 0.004, 0.0), (L.ix1, L.iy1, L.iz1), "charcoal", 0.0015, 1))
    g.append(rbox(book, "liner_top", (L.ix0, L.iy0, L.iz1 - 0.004), (L.ix1, L.iy1, L.iz1), "charcoal", 0.0015, 1))
    for name, x in (("left", L.ix0 + 0.03), ("right", L.ix1 - 0.03)):
        g.append(rbox(book, f"led_ceiling_{name}", (x - 0.008, L.iy0 + 0.03, L.iz1 - 0.008), (x + 0.008, L.iy1 - 0.03, L.iz1 - 0.0035), "led_white", 0.0015, 1))
    for name, xa, xb in (("left", L.ix0, L.ix0 + 0.006), ("right", L.ix1 - 0.006, L.ix1)):
        g.append(rbox(book, f"rail_cover_{name}", (xa, L.iy0 + 0.004, RAIL_Z_M - 0.068), (xb, L.iy1 - 0.004, RAIL_Z_M + 0.068), "rail_cover", 0.002, 1))
    cam_x, cam_y, cam_z = post_l + 0.06, f1 + 0.004, TOP_FRAME - 0.022
    g.append(cyl("camera_body", (cam_x, cam_y, cam_z), (cam_x, cam_y + 0.026, cam_z), 0.011, "matte_black", 1))
    g.append(cyl("camera_lens", (cam_x, cam_y - 0.0015, cam_z), (cam_x, cam_y, cam_z), 0.0065, "lens", 1))

    for name, x in (("left", L.rail_x[0]), ("right", L.rail_x[1])):
        g.append(rbox(book, f"rail_{name}", (x - 0.006, L.iy0 + 0.01, RAIL_Z_M - 0.008), (x + 0.006, L.iy1 - 0.01, RAIL_Z_M + 0.008), "chrome", 0.003, 0))
        g.append(rbox(book, f"rail_{name}_mount", (x - 0.012, L.iy0 + 0.01, RAIL_Z_M - 0.03), (x + 0.012, L.iy1 - 0.01, RAIL_Z_M - 0.008), "graphite", 0.003, 0))

    g.append(
        f'<geom name="deck_plate" type="box" pos="{_v((L.ix0 + L.ix1) / 2, (L.iy0 + L.iy1) / 2, DECK_UNDER / 2)}" '
        f'size="{_v((L.ix1 - L.ix0) / 2, (L.iy1 - L.iy0) / 2, -DECK_UNDER / 2)}" material="deck" group="0"/>'
    )
    slot_w, slot_d = deck.slot_size
    for name, pos in sorted(deck.slots.items()):
        x0 = (pos[0] + deck.corner[0]) * MM
        y0 = (pos[1] + deck.corner[1]) * MM
        x1 = x0 + slot_w * MM
        y1 = y0 + slot_d * MM
        g.append(rbox(book, f"slot_{name}", (x0, y0, 0.0), (x1, y1, 0.0018), "slot_plate", 0.0007, 0))
        arm, bar = 0.016, 0.0035
        for k, (cx_, cy_, ix, iy) in enumerate(
            [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]
        ):
            along_x = sorted((cx_, cx_ + ix * arm))
            along_y = sorted((cy_, cy_ + iy * arm))
            edge_x = sorted((cx_, cx_ + ix * bar))
            edge_y = sorted((cy_, cy_ + iy * bar))
            g.append(rbox(book, f"slot_{name}_c{k}a", (along_x[0], edge_y[0], 0.0), (along_x[1], edge_y[1], 0.0026), "accent_blue", 0.0006, 0))
            g.append(rbox(book, f"slot_{name}_c{k}b", (edge_x[0], along_y[0], 0.0), (edge_x[1], along_y[1], 0.0026), "accent_blue", 0.0006, 0))
        for k, x in enumerate((x0 + 0.005, x1 - 0.005)):
            g.append(cyl(f"slot_{name}_screw{k}", (x, (y0 + y1) / 2, 0.0), (x, (y0 + y1) / 2, 0.0024), 0.0028, "chrome", 0))

    body = "\n      ".join(g)

    door_lo = (post_l - 0.012, f0 + 0.008, SILL - 0.012)
    door_hi = (post_r + 0.012, f0 + 0.014, TOP_FRAME + 0.012)
    door = [
        f'<geom name="door_glass" type="box" pos="{_v(*[(a + b) / 2 for a, b in zip(door_lo, door_hi)])}" '
        f'size="{_v(*[(b - a) / 2 for a, b in zip(door_lo, door_hi)])}" material="glass" group="2"/>',
    ]
    for name, xa, xb in (("left", post_l + 0.008, post_l + 0.042), ("right", post_r - 0.042, post_r - 0.008)):
        door.append(rbox(book, f"door_hinge_{name}", (xa, f1, TOP_FRAME - 0.03), (xb, f1 + 0.016, TOP_FRAME - 0.004), "matte_black", 0.003, 1))

    windows = []
    for name, x in (("left", L.x0 + 0.014), ("right", L.x1 - 0.014)):
        lo = (x - 0.003, win_y[0] - 0.008, win_z[0] - 0.008)
        hi = (x + 0.003, win_y[1] + 0.008, win_z[1] + 0.008)
        windows.append(
            f'<body name="window_{name}">\n'
            f'      <geom name="window_{name}_glass" type="box" pos="{_v(*[(a + b) / 2 for a, b in zip(lo, hi)])}" '
            f'size="{_v(*[(b - a) / 2 for a, b in zip(lo, hi)])}" material="tint" group="2"/>\n'
            f"    </body>"
        )

    return (
        f'<body name="chassis">\n      {body}\n    </body>\n'
        f'    <body name="door">\n      ' + "\n      ".join(door) + "\n    </body>\n    " + "\n    ".join(windows)
    )


# ---------------------------------------------------------------- gantry


def bridge_geoms(book: AssetBook, layout: Layout) -> str:
    """Y crossbar and its two trucks. Geoms are in the bridge frame (x absolute, y = tip y)."""

    L = layout
    z, h = RAIL_Z_M, BEAM_H / 2
    x0, x1 = L.ix0 + 0.03, L.ix1 - 0.03
    face = BEAM_DY[0]
    g = [
        rbox(book, "beam", (x0, BEAM_DY[0], z - h), (x1, BEAM_DY[1], z + h), "beam", 0.008, 0),
        rbox(book, "beam_groove", (x0 + 0.02, face - 0.0008, z + h - 0.021), (x1 - 0.02, face + 0.002, z + h - 0.013), "graphite", 0.001, 0),
        rbox(book, "beam_seam", (x0 + 0.02, face - 0.0005, z - h + 0.014), (x1 - 0.02, face + 0.002, z - h + 0.0155), "aluminum_dark", 0.0003, 0),
    ]
    for side, x in (("left", L.rail_x[0]), ("right", L.rail_x[1])):
        g.append(
            rbox(
                book, f"truck_{side}",
                (x - TRUCK_W / 2, BLOCK_DY[0] - 0.004, z - h - 0.012), (x + TRUCK_W / 2, BLOCK_DY[1], z + h + 0.012),
                "matte_black", 0.005, 0,
            )
        )
    return "\n        ".join(g)


def carriage_geoms(book: AssetBook, tools: tuple[str, ...] = ()) -> str:
    """X slider: dark head plate in front, a block around the beam and a column above it.

    Carriage frame: x = 1000 uL tip x, y = tip y, z absolute. The tools hang on
    the plate's front face at ``MOUNT_Y``. ``tools`` are the mounted pipette
    tool names; the seams are drawn only between bays that hold something.
    """

    z, hb = RAIL_Z_M, BLOCK_H / 2
    x0, x1 = BLOCK_DX
    g = [
        rbox(book, "z_rail_plate", (x0, MOUNT_Y, Z_PLATE_BOTTOM), (x1, BLOCK_DY[0], HEAD_TOP), "head_plate", 0.004, 0),
        rbox(book, "carriage_block", (x0 + 0.004, BLOCK_DY[0] - 0.001, z - hb), (x1 - 0.004, BLOCK_DY[1], z + hb), "graphite", 0.008, 0),
        rbox(book, "carriage_column", (x0 + 0.012, BLOCK_DY[0] - 0.001, z + hb - 0.01), (x1 - 0.012, BLOCK_DY[0] + 0.036, HEAD_TOP - 0.004), "graphite", 0.006, 0),
        rbox(book, "carriage_foot", (x0 + 0.003, MOUNT_Y + 0.001, Z_PLATE_BOTTOM - 0.006), (x1 - 0.003, BLOCK_DY[0] + 0.012, Z_PLATE_BOTTOM + 0.002), "graphite", 0.002, 0),
    ]
    for side, x in (("left", x0 + 0.0055), ("right", x1 - 0.0035)):
        g.append(rbox(book, f"z_rail_{side}", (x - 0.0025, MOUNT_Y - 0.004, Z_PLATE_BOTTOM + 0.01), (x + 0.0025, MOUNT_Y, HEAD_TOP - 0.01), "chrome", 0.0012, 0))
    # Seams between the mounted bays, in x order: left mount, right mount, gripper.
    centers = []
    if "pipette_8" in tools or "pipette_1000_left" in tools:
        centers.append(PIPETTE_8_DX)
    if "pipette_1000" in tools or "pipette_8_right" in tools:
        centers.append(0.0)
    centers.append(GRIPPER_DX)
    for k, (a, b) in enumerate(zip(centers, centers[1:])):
        x = (a + b) / 2
        g.append(rbox(book, f"head_seam_{k}", (x - 0.0015, MOUNT_Y - 0.0006, Z_PLATE_BOTTOM + 0.012), (x + 0.0015, MOUNT_Y + 0.001, HEAD_TOP - 0.012), "graphite", 0.0004, 0))
    return "\n          ".join(g)


def pipette_face_material(book: AssetBook, tool: str, volume: str, channels: str) -> str:
    """Front label texture for one mounted pipette (its volume and channel count), as a material name."""

    return book.texture(f"label_{tool}", _pipette_face(volume, channels), specular=0.25, shininess=0.3)


def _pipette_xml(book: AssetBook, name: str, face: str, dy: tuple[float, float]) -> list[str]:
    """Silver housing with the black front label, top vent and a dark foot."""

    half = PIPETTE_W / 2
    top = PIPETTE_BOTTOM + PIPETTE_H
    front, back = dy
    return [
        rbox(book, f"{name}_housing", (-half, front, PIPETTE_BOTTOM), (half, back, top), "aluminum", 0.004, 0),
        label(book, f"{name}_face", (0.0, front - 0.0003, (PIPETTE_BOTTOM + top) / 2), (PIPETTE_W - 0.003, PIPETTE_H - 0.003), face, 0),
        rbox(book, f"{name}_vent", (-half + 0.004, front + 0.004, top - 0.001), (half - 0.004, back - 0.004, top + 0.0012), "graphite", 0.0008, 0),
        rbox(book, f"{name}_foot", (-half + 0.002, front + 0.002, PIPETTE_BOTTOM - 0.004), (half - 0.002, back - 0.002, PIPETTE_BOTTOM + 0.001), "graphite", 0.0015, 0),
    ]


def _joint(tool: Tool, z_range: str) -> str:
    return f'<joint name="{tool.joint}" type="slide" axis="0 0 1" range="{z_range}"/>'


@dataclass(frozen=True)
class TipSpec:
    """A disposable tip as mounted: ``reach_mm`` below the nozzle end (``tipLength`` in
    the analysis), ``length_mm`` overall, so ``length_mm - reach_mm`` overlaps the nozzle."""

    mesh: str
    reach_mm: float
    length_mm: float


TIP_RGBA = "0.95 0.96 0.97 0"
TIP_LIQUID_RGBA = "0.2 0.5 0.9 0"
TIP_LIQUID_R = 0.0011


def _mounted_tip(prefix: str, x: float, y: float, tip: TipSpec) -> list[str]:
    """Hidden tip, the liquid inside it, and the end site, for one nozzle at (x, y, 0)."""

    end = -tip.reach_mm * MM
    appearance = ('material="labware_pe_tip" rgba="0.52 0.59 0.62 0"'
                  if tip.mesh.endswith("_open") else f'rgba="{TIP_RGBA}"')
    return [
        f'<geom name="{prefix}" type="mesh" mesh="{tip.mesh}" pos="{_v(x, y, end)}" {appearance} group="0"/>',
        f'<geom name="{prefix}_liquid" type="cylinder" pos="{_v(x, y, end + 0.002)}" size="{_v(TIP_LIQUID_R, 0.0005)}" rgba="{TIP_LIQUID_RGBA}" group="0"/>',
    ]


def pipette_1000_body(book: AssetBook, tip: TipSpec | None = None, face: str = "label_1000") -> str:
    """Active pipette. Sits in ``head`` (joint ``z``); its origin is the nozzle end, the ``tip`` site.

    With ``tip``, the red bead is left off (it would show through the tip) and
    ``tip_end`` marks where a mounted tip ends.
    """

    g = _pipette_xml(book, "pipette_1000", face, PIPETTE_DY) + [
        cyl("pipette_1000_ejector", (0.0, 0.0, 0.026), (0.0, 0.0, PIPETTE_BOTTOM - 0.003), 0.0046, "satin_black", 0),
        cyl("pipette_1000_collar", (0.0, 0.0, PIPETTE_BOTTOM - 0.013), (0.0, 0.0, PIPETTE_BOTTOM - 0.003), 0.0075, "graphite", 0),
        '<geom name="nozzle" type="cylinder" fromto="0 0 0 0 0 0.032" size="0.0034" material="chrome" group="0"/>',
        '<site name="tip" pos="0 0 0" size="0.004" group="4"/>',
    ]
    if tip is None:
        g.append('<geom name="tip_bead" type="sphere" pos="0 0 0.0028" size="0.0028" material="tip_marker" group="0"/>')
    else:
        g += _mounted_tip("pipette_1000_tip", 0.0, 0.0, tip)
        g.append(f'<site name="tip_end" pos="{_v(0.0, 0.0, -tip.reach_mm * MM)}" size="0.0015" group="4"/>')
    return '<body name="pipette_1000" pos="0 0 0">\n          ' + "\n          ".join(g) + "\n        </body>"


def pipette_1000_left_body(book: AssetBook, z_range: str, tip: TipSpec | None = None, face: str = "label_1000") -> str:
    """1000 uL single on the left mount (tool ``pipette_1000_left``).

    Same housing as the right-mount single, on its own Z joint ``z_left`` at the
    8-channel's x offset. Its origin is the nozzle end, the ``tip_left`` site.
    """

    tool = TOOL_BY_NAME["pipette_1000_left"]
    name = tool.body
    g = _pipette_xml(book, name, face, PIPETTE_DY) + [
        cyl(f"{name}_ejector", (0.0, 0.0, 0.026), (0.0, 0.0, PIPETTE_BOTTOM - 0.003), 0.0046, "satin_black", 0),
        cyl(f"{name}_collar", (0.0, 0.0, PIPETTE_BOTTOM - 0.013), (0.0, 0.0, PIPETTE_BOTTOM - 0.003), 0.0075, "graphite", 0),
        f'<geom name="{name}_nozzle" type="cylinder" fromto="0 0 0 0 0 0.032" size="0.0034" material="chrome" group="0"/>',
        f'<site name="{tool.site}" pos="0 0 0" size="0.004" group="4"/>',
    ]
    if tip is None:
        g.append(f'<geom name="{name}_bead" type="sphere" pos="0 0 0.0028" size="0.0028" material="tip_marker" group="0"/>')
    else:
        g += _mounted_tip(f"{name}_tip", 0.0, 0.0, tip)
        g.append(f'<site name="{tool.site}_end" pos="{_v(0.0, 0.0, -tip.reach_mm * MM)}" size="0.0015" group="4"/>')
    return (
        f'<body name="{name}" pos="{_v(tool.dx, tool.dy, 0.0)}">\n          '
        + _joint(tool, z_range)
        + "\n          "
        + "\n          ".join(g)
        + "\n        </body>"
    )


def _eight_channel_body(
    book: AssetBook, tool_name: str, z_range: str, tip: TipSpec | None, nozzle_prefix: str, site_prefix: str, face: str = "label_8"
) -> str:
    """One 8-channel. Nozzle A is the body origin; B..H follow toward the front at 9 mm.

    The row runs front to back because that is how a plate column A1..H1 lies
    in the labware JSON (wells 9 mm apart in y).
    """

    tool = TOOL_BY_NAME[tool_name]
    front = PIPETTE_8_DY[0]
    g = _pipette_xml(book, tool.body, face, PIPETTE_8_DY) + [
        rbox(book, f"{nozzle_prefix}_block", (-0.0175, front + 0.002, 0.038), (0.0175, 0.006, PIPETTE_BOTTOM - 0.003), "graphite", 0.004, 0),
    ]
    for k, row in enumerate(NOZZLE_ROWS):
        y = -NOZZLE_PITCH * k
        g.append(f'<geom name="{nozzle_prefix}_nozzle_{row}" type="cylinder" fromto="0 {_f(y)} 0 0 {_f(y)} 0.04" size="0.0034" material="chrome" group="0"/>')
        g.append(f'<site name="{site_prefix}_{row}" pos="0 {_f(y)} 0" size="0.003" group="4"/>')
        if tip is not None:
            g += _mounted_tip(f"{nozzle_prefix}_tip_{row}", 0.0, y, tip)
            g.append(f'<site name="{site_prefix}_end_{row}" pos="{_v(0.0, y, -tip.reach_mm * MM)}" size="0.0015" group="4"/>')
    return (
        f'<body name="{tool.body}" pos="{_v(tool.dx, tool.dy, 0.0)}">\n          '
        + _joint(tool, z_range)
        + "\n          "
        + "\n          ".join(g)
        + "\n        </body>"
    )


def pipette_8_body(book: AssetBook, z_range: str, tip: TipSpec | None = None, face: str = "label_8") -> str:
    """8-channel on the left mount."""

    return _eight_channel_body(book, "pipette_8", z_range, tip, "pipette_8", "tip_8", face)


def pipette_8_right_body(book: AssetBook, z_range: str, tip: TipSpec | None = None, face: str = "label_8") -> str:
    """8-channel on the right mount. Same housing as the left one; nozzle A is at x = 0."""

    return _eight_channel_body(book, "pipette_8_right", z_range, tip, "pipette_8r", "tip_8r", face)


def gripper_body(book: AssetBook, z_range: str, jaw_f_range: str, jaw_b_range: str) -> str:
    """Gripper on the extension mount. Z is its own joint; the jaws slide apart along y.

    The slab is thin in x and runs from the mount plate forward past the front
    jaw; the notch cuts the lower back corner. ``gripper_center`` is the bottom
    midpoint between the two paddles, 74 mm in front of the mount. A plate grip
    commands that point to ``gripHeightFromLabwareBottom`` minus half the paddle.
    """

    tool = TOOL_BY_NAME["gripper"]
    w = GRIPPER_W
    front, back = GRIPPER_FRONT, MOUNT_Y
    base_lo, base_hi = 0.070, 0.106
    top = PIPETTE_BOTTOM + PIPETTE_H
    z_notch, fillet = 0.205, 0.016
    yn = back - 0.030
    corner = [(yn, z_notch - fillet), (yn, z_notch), (yn + fillet, z_notch)]
    corner += arc((yn + fillet, z_notch - fillet), fillet, 90, 180)[1:-1]
    side = w / 2
    g = [
        rbox(book, "gripper_housing", (-side, front, z_notch), (side, back, top - 0.004), "white", 0.003, 0),
        rbox(book, "gripper_lower", (-side, front, base_hi), (side, yn, z_notch + 0.004), "white", 0.003, 0),
        mesh_geom("gripper_fillet", book.extrusion("gripper_fillet", corner, None, 0, -side + 0.0008, side - 0.0008), "white", 0),
        rbox(book, "gripper_cap", (-side + 0.003, front + 0.003, top - 0.006), (side - 0.003, back - 0.003, top), "graphite", 0.002, 0),
        rbox(book, "gripper_base", (-side - 0.001, front, base_lo), (side + 0.001, yn + 0.002, base_hi), "white", 0.004, 0),
        rbox(book, "gripper_base_trim", (-side, yn + 0.002, base_lo + 0.004), (side, yn + 0.007, base_hi + 0.03), "satin_black", 0.001, 0),
        rbox(book, "gripper_jaw_guide", (-0.010, front, base_lo - 0.008), (0.010, JAW_FORWARD + JAW_OPEN + JAW_PAD, base_lo), "graphite", 0.0015, 0),
        rbox(book, "gripper_pin_slot", (side + 0.0004, front + 0.020, 0.082), (side + 0.0016, front + 0.050, 0.096), "recess", 0.002, 0),
        cyl("gripper_calibration_pin", (side + 0.0022, front + 0.025, 0.089), (side + 0.0022, front + 0.045, 0.089), 0.0026, "chrome", 0),
    ]
    for k, z in enumerate((z_notch - 0.034, base_hi + 0.014)):
        g.append(cyl(f"gripper_screw_{k}", (side - 0.001, yn - 0.007, z), (side + 0.0008, yn - 0.007, z), 0.0022, "chrome", 0))
    jaws = []
    y0 = JAW_FORWARD
    for name, sign, jaw_range in (("front", -1, jaw_f_range), ("back", 1, jaw_b_range)):
        span = lambda a, b: tuple(sorted((y0 + sign * a, y0 + sign * b)))
        bar = span(0.001, JAW_PAD)
        pad = span(0.0, 0.0045)
        slot = span(0.0042, 0.0050)
        shoulder = span(-0.004, JAW_PAD)
        parts = [
            rbox(book, f"gripper_jaw_shoulder_{name}", (-0.012, shoulder[0], base_lo - 0.014), (0.012, shoulder[1], base_lo - 0.008), "graphite", 0.0015, 0),
            rbox(book, f"gripper_jaw_bar_{name}", (-0.006, bar[0], 0.006), (0.006, bar[1], base_lo - 0.008), "satin_black", 0.0015, 0),
            rbox(book, f"gripper_paddle_{name}", (-PADDLE_W / 2, pad[0], 0.0), (PADDLE_W / 2, pad[1], 0.008), "white", 0.0012, 0),
            rbox(book, f"gripper_paddle_slot_{name}", (-0.008, slot[0], 0.0022), (0.008, slot[1], 0.0052), "recess", 0.0003, 0),
        ]
        jaws.append(
            f'<body name="gripper_jaw_{name}" pos="0 0 0">\n          '
            f'<joint name="jaw_{name[0]}" type="slide" axis="0 1 0" range="{jaw_range}"/>\n          '
            + "\n          ".join(parts)
            + "\n        </body>"
        )
    return (
        f'<body name="gripper" pos="{_v(tool.dx, 0.0, 0.0)}">\n          '
        + _joint(tool, z_range)
        + "\n          "
        + "\n          ".join(g)
        + f'\n          <site name="gripper_center" pos="0 {_f(JAW_FORWARD)} 0" size="0.004" group="4"/>\n          '
        + "\n          ".join(jaws)
        + "\n        </body>"
    )


def scene_lighting(layout: Layout) -> str:
    """Directional lights only. Any spot inside the enclosure, even without
    shadows, darkens the top panel and front print; interior parts that
    sit in the shell's shadow use material emission instead."""

    cx = layout.center_x
    return f"""
    <light name="key" pos="{_v(cx + 1.0, -1.3, 2.0)}" dir="-0.40 0.55 -0.75" directional="true" diffuse="0.52 0.52 0.52" specular="0.32 0.32 0.32" castshadow="true"/>
    <light name="fill" pos="{_v(cx - 1.2, -1.0, 1.2)}" dir="0.50 0.65 -0.30" directional="true" diffuse="0.24 0.24 0.24" specular="0.10 0.10 0.10" castshadow="false"/>
    <light name="rim" pos="{_v(cx, 1.6, 1.6)}" dir="0 -0.70 -0.55" directional="true" diffuse="0.12 0.12 0.12" specular="0.16 0.16 0.16" castshadow="false"/>    """
