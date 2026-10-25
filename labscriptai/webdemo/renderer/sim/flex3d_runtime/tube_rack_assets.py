"""Procedural appearance mesh for tube-rack inserts; not collision CAD."""

from __future__ import annotations

import math
from pathlib import Path

from .flex_shell import _MeshBuilder

_BEVEL = 0.0003
_TAU = 2.0 * math.pi


def _positive(name: str, value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a finite positive number") from None
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return number


def _angles(cx: float, cy: float, x0: float, x1: float, y0: float, y1: float) -> list[float]:
    values = [_TAU * i / 32.0 for i in range(32)]
    values += [math.atan2(py - cy, px - cx) % _TAU
               for px in (x0, x1) for py in (y0, y1)]
    result: list[float] = []
    for angle in sorted(values):
        if not result or angle - result[-1] > 1e-10:
            result.append(angle)
    return result


def _boundary(cx: float, cy: float, bounds: tuple[float, float, float, float], angle: float):
    x0, x1, y0, y1 = bounds
    dx, dy = math.cos(angle), math.sin(angle)
    tx = (x1 - cx) / dx if dx > 1e-12 else (x0 - cx) / dx if dx < -1e-12 else math.inf
    ty = (y1 - cy) / dy if dy > 1e-12 else (y0 - cy) / dy if dy < -1e-12 else math.inf
    t = min(tx, ty)
    return (min(max(cx + t * dx, x0), x1), min(max(cy + t * dy, y0), y1))


def _cap(mesh: _MeshBuilder, cx: float, cy: float, radius: float,
         bounds: tuple[float, float, float, float], angles: list[float],
         z: float, up: bool, width: float, depth: float) -> None:
    normal = (0.0, 0.0, 1.0 if up else -1.0)
    def vertex(x, y):
        return mesh.add((x, y, z), normal, (x / width, y / depth))
    outer = [vertex(*_boundary(cx, cy, bounds, a)) for a in angles]
    inner = [vertex(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in angles]
    for i in range(len(angles)):
        j = (i + 1) % len(angles)
        mesh.tri(outer[i], outer[j], inner[j], normal)
        mesh.tri(outer[i], inner[j], inner[i], normal)


def _wall(mesh: _MeshBuilder, cx: float, cy: float, radius: float,
          angles: list[float], z: float, z_normal: float) -> list[int]:
    scale = math.hypot(1.0, z_normal)
    return [mesh.add((cx + radius * math.cos(a), cy + radius * math.sin(a), z),
                     (-math.cos(a) / scale, -math.sin(a) / scale, z_normal / scale))
            for a in angles]


def write_insert(path: Path, width: float, depth: float,
                 openings: list[tuple[float, float, float]], thickness: float = 0.005) -> None:
    """Write an OBJ plate with through holes, annular caps, and a top-hole bevel."""
    width = _positive("width", width)
    depth = _positive("depth", depth)
    thickness = _positive("thickness", thickness)
    bevel = min(_BEVEL, thickness / 2.0)

    holes = []
    for opening in list(openings):
        try:
            hx, hy, radius = opening
        except (TypeError, ValueError):
            raise ValueError("each opening must be (x, y, radius)") from None
        hx, hy = _positive("hole x", hx), _positive("hole y", hy)
        radius = _positive("hole radius", radius)
        holes.append((hx, hy, radius))

    if not holes:
        raise ValueError("at least one hole is required")

    columns: dict[float, list[tuple[float, float, float]]] = {}
    for hole in holes:
        columns.setdefault(hole[0], []).append(hole)
    column_x = sorted(columns)
    x_edges = [0.0] + [(a + b) / 2.0 for a, b in zip(column_x, column_x[1:])] + [width]

    mesh = _MeshBuilder()
    for x0, x1, hx in zip(x_edges, x_edges[1:], column_x):
        column = sorted(columns[hx], key=lambda hole: hole[1])
        y_edges = [0.0] + [(a[1] + b[1]) / 2.0 for a, b in zip(column, column[1:])] + [depth]
        for y0, y1, (hx, hy, radius) in zip(y_edges, y_edges[1:], column):
            if not (hx - radius - bevel > x0 and hx + radius + bevel < x1
                    and hy - radius - bevel > y0 and hy + radius + bevel < y1):
                raise ValueError(
                    f"hole ({hx}, {hy}, r={radius}) must fit strictly inside its "
                    f"cell ({x0}, {x1}) x ({y0}, {y1}), including bevel")
            bounds = (x0, x1, y0, y1)
            angles = _angles(hx, hy, x0, x1, y0, y1)
            _cap(mesh, hx, hy, radius, bounds, angles, 0.0, False, width, depth)
            _cap(mesh, hx, hy, radius + bevel, bounds, angles, thickness, True, width, depth)
            bottom = _wall(mesh, hx, hy, radius, angles, 0.0, 0.0)
            shoulder = _wall(mesh, hx, hy, radius, angles, thickness - bevel, 0.0)
            top = _wall(mesh, hx, hy, radius + bevel, angles, thickness, 1.0)
            for i in range(len(angles)):
                j = (i + 1) % len(angles)
                mid = (angles[i] + angles[j]) / 2.0 if j else (angles[i] + _TAU) / 2.0
                inward = (-math.cos(mid), -math.sin(mid), 0.0)
                mesh.tri(bottom[i], bottom[j], shoulder[j], inward)
                mesh.tri(bottom[i], shoulder[j], shoulder[i], inward)
                bevel_facing = (-math.cos(mid), -math.sin(mid), 1.0)
                mesh.tri(shoulder[i], shoulder[j], top[j], bevel_facing)
                mesh.tri(shoulder[i], top[j], top[i], bevel_facing)

    for x0, x1 in zip(x_edges, x_edges[1:]):
        for y0, y1 in zip([0.0], [depth]):
            sides = (((x0, y0), (x1, y0), (0.0, -1.0, 0.0)),
                     ((x1, y0), (x1, y1), (1.0, 0.0, 0.0)),
                     ((x1, y1), (x0, y1), (0.0, 1.0, 0.0)),
                     ((x0, y1), (x0, y0), (-1.0, 0.0, 0.0)))
            for p, q, normal in sides:
                a = mesh.add((*p, 0.0), normal)
                b = mesh.add((*q, 0.0), normal)
                c = mesh.add((*q, thickness), normal)
                d = mesh.add((*p, thickness), normal)
                mesh.tri(a, b, c, normal)
                mesh.tri(a, c, d, normal)

    mesh.write(path, with_uv=True)
