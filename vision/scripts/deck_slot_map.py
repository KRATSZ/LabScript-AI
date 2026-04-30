"""
Flex 12-slot mapping from image bbox centers + optional deck homography.

Aligned with Opentrons-Lab-Agent `vision_check.py` corner order and grid logic.
Used by `deck_infer_report.py`; no Ultralytics dependency.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# deck plane u,v in [0,1]: A1 -> (0,0), A3 -> (1,0), D3 -> (1,1), D1 -> (0,1)
DECK_CORNER_ORDER_DOC = "A1_A3_D3_D1_clockwise_deck_view"

FLEX_SLOTS = [
    "A1",
    "A2",
    "A3",
    "B1",
    "B2",
    "B3",
    "C1",
    "C2",
    "C3",
    "D1",
    "D2",
    "D3",
]


def parse_optional_deck_corners_dict(data: dict) -> list[list[float]] | None:
    """Read optional_deck_corners_norm from a labels sidecar dict (MCP-compatible)."""
    corners = data.get("optional_deck_corners_norm")
    if not isinstance(corners, list) or len(corners) != 4:
        return None
    out: list[list[float]] = []
    for c in corners:
        if not isinstance(c, (list, tuple)) or len(c) < 2:
            return None
        out.append([float(c[0]), float(c[1])])
    return out


def load_deck_corners_labels_file(labels_path: Path) -> list[list[float]] | None:
    """Load four normalized deck corners from a standalone *.labels.json file."""
    if not labels_path.is_file():
        return None
    try:
        data = json.loads(labels_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return parse_optional_deck_corners_dict(data)


def load_sidecar_deck_corners(image_path: Path) -> list[list[float]] | None:
    sidecar = image_path.parent / "labels" / f"{image_path.stem}.labels.json"
    if not sidecar.is_file():
        return None
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parse_optional_deck_corners_dict(data)


def build_homography_from_corners_norm(
    corners_norm: list[list[float]],
    w: int,
    h: int,
) -> tuple[Any | None, list[str]]:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None, ["homography_requires_opencv"]

    if len(corners_norm) != 4:
        return None, ["deck_corners_norm_need_four_points"]
    try:
        src_list: list[list[float]] = []
        for c in corners_norm:
            src_list.append([float(c[0]) * w, float(c[1]) * h])
        src = np.array(src_list, dtype=np.float32)
        dst = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]], dtype=np.float32)
        hmat = cv2.getPerspectiveTransform(src, dst)
        return hmat, []
    except Exception as exc:
        return None, [f"homography_failed:{type(exc).__name__}:{exc}"]


def _grid_cell(nx: float, ny: float) -> tuple[str, list[str]]:
    uncertainties: list[str] = []
    eps = 0.02
    for b in (1.0 / 3.0, 2.0 / 3.0):
        if abs(nx - b) < eps:
            uncertainties.append(f"near_vertical_grid nx={nx:.3f}")
    for b in (0.25, 0.5, 0.75):
        if abs(ny - b) < eps:
            uncertainties.append(f"near_horizontal_grid ny={ny:.3f}")

    col = min(2, max(0, int(nx * 3)))
    if nx >= 1.0:
        col = 2
    row = min(3, max(0, int(ny * 4)))
    if ny >= 1.0:
        row = 3
    letter = chr(ord("A") + row)
    slot = f"{letter}{col + 1}"
    return slot, uncertainties


def _deck_plane_to_slot(ux: float, uy: float) -> tuple[str, list[str]]:
    uncertainties: list[str] = []
    eps = 0.02
    ux = max(0.0, min(1.0, ux))
    uy = max(0.0, min(1.0, uy))
    for b in (1.0 / 3.0, 2.0 / 3.0):
        if abs(ux - b) < eps:
            uncertainties.append(f"near_vertical_deck_ux={ux:.3f}")
    for b in (0.25, 0.5, 0.75):
        if abs(uy - b) < eps:
            uncertainties.append(f"near_horizontal_deck_uy={uy:.3f}")
    col = min(2, max(0, int(ux * 3)))
    if ux >= 1.0:
        col = 2
    row = min(3, max(0, int(uy * 4)))
    if uy >= 1.0:
        row = 3
    letter = chr(ord("A") + row)
    slot = f"{letter}{col + 1}"
    return slot, uncertainties


def map_center_to_slot(
    nx: float,
    ny: float,
    w: int,
    h: int,
    hmat: Any | None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    extra: dict[str, Any] | None = None
    if hmat is None:
        slot, notes = _grid_cell(nx, ny)
        return slot, notes, extra
    try:
        import cv2
        import numpy as np
    except ImportError:
        slot, notes = _grid_cell(nx, ny)
        return slot, notes + ["opencv_missing_fell_back_to_image_grid"], extra

    px, py = nx * w, ny * h
    pt = np.array([[[float(px), float(py)]]], dtype=np.float32)
    out = cv2.perspectiveTransform(pt, hmat)
    ux, uy = float(out[0, 0, 0]), float(out[0, 0, 1])
    ux = max(0.0, min(1.0, ux))
    uy = max(0.0, min(1.0, uy))
    slot, notes = _deck_plane_to_slot(ux, uy)
    extra = {"deck_plane_norm": [round(ux, 4), round(uy, 4)]}
    return slot, notes, extra
