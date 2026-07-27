#!/usr/bin/env python3
"""
Local vision check for Opentrons-Lab-Agent MCP.

Contract: read one JSON object from stdin, write one JSON object to stdout.

Modes:
  - deck: Ultralytics YOLO. If `weights` is omitted, auto-pick lab-trained
          `vision` deck checkpoints when present, else YOLOE
          (`yoloe-26s-seg.pt`). Lab class names (e.g. tiprack_200) map to
          canonical labels (tiprack, plate, ...). Detections are mapped to
          Flex slots via optional deck homography or a uniform image-grid
          fallback.
  - tiprack: minimal rack-view judgment based on localized tiprack detections.

Does NOT mutate MCP session state - observation-only JSON for agents to compare
with reconcile_state / tip_tracking.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_COCO_FALLBACK_WEIGHTS = "yolo11n.pt"
LOW_CONFIDENCE_THRESHOLD = 0.5
SLOT_WIDTH = 1.0 / 3.0
SLOT_HEIGHT = 1.0 / 4.0
SLOT_AREA = SLOT_WIDTH * SLOT_HEIGHT
BOUNDARY_EPS = 0.02

_REPO_ROOT = Path(os.environ.get("OPENTRONS_PLUGIN_ROOT", Path(__file__).resolve().parents[3])).expanduser().resolve()
_VISION_ROOT = _REPO_ROOT / "vision"
_VISION_WEIGHTS_DIR = _VISION_ROOT / "models" / "weights"
_VISION_RUNS_DIR = _VISION_ROOT / "runs" / "detect"
_DEFAULT_LAYOUT_POLICY_PATH = _REPO_ROOT / "automation" / "deck_layout_policy.json"
_DEFAULT_CALIBRATION_PATH = _REPO_ROOT / "automation" / "photo" / "deck_calibration.json"


def _layout_policy_path() -> Path:
    env = os.environ.get("OPENTRONS_DECK_LAYOUT_POLICY")
    if env:
        return Path(env).expanduser().resolve()
    return _DEFAULT_LAYOUT_POLICY_PATH


def _load_deck_layout_policy() -> dict[str, Any] | None:
    path = _layout_policy_path()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _fixed_slot_names(policy: dict[str, Any] | None) -> set[str]:
    if not policy:
        return set()
    fixed = policy.get("fixed_slots") or {}
    return {str(slot).upper() for slot in fixed}


def _detection_slot_names(policy: dict[str, Any] | None) -> list[str]:
    if not policy:
        return list(FLEX_SLOTS)
    slots = policy.get("detection_slots")
    if isinstance(slots, list) and slots:
        return [str(slot).upper() for slot in slots]
    fixed = _fixed_slot_names(policy)
    return [slot for slot in FLEX_SLOTS if slot not in fixed]


def _detection_class_names(policy: dict[str, Any] | None) -> list[str]:
    if not policy:
        return []
    classes = policy.get("detection_classes")
    if isinstance(classes, list) and classes:
        return [str(name) for name in classes]
    return []


def _load_default_deck_calibration() -> dict[str, Any]:
    path = _DEFAULT_CALIBRATION_PATH
    env = os.environ.get("OPENTRONS_DECK_CALIBRATION")
    if env:
        path = Path(env).expanduser().resolve()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _apply_layout_policy(
    slot_observations: dict[str, dict[str, Any]],
    policy: dict[str, Any] | None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "path": None,
        "fixed_slots": [],
        "detection_slots": list(FLEX_SLOTS),
        "detection_classes": [],
    }
    if not policy:
        return meta

    meta["path"] = str(_layout_policy_path().name)
    meta["fixed_slots"] = sorted(_fixed_slot_names(policy))
    meta["detection_slots"] = _detection_slot_names(policy)
    meta["detection_classes"] = _detection_class_names(policy)

    fixed_entries = policy.get("fixed_slots") or {}
    for slot in meta["fixed_slots"]:
        entry = fixed_entries.get(slot) or {}
        role = entry.get("role") if isinstance(entry, dict) else str(entry)
        note = entry.get("note") if isinstance(entry, dict) else None
        slot_observations[slot] = {
            "state": "fixed",
            "source": "layout_policy",
            "label": role or "fixed",
            "role": role,
            "note": note,
            "confidence_band": "high",
            "reasons": ["fixed_hardware"],
            "covered_by": [],
        }
    return meta


def _default_weights_chain() -> str:
    """
    When MCP does not pass `weights`: prefer lab-trained deck checkpoint, then YOLOE.
    Env OPENTRONS_DECK_YOLO_WEIGHTS overrides auto-pick (explicit path to best.pt).
    """
    env_deck = os.environ.get("OPENTRONS_DECK_YOLO_WEIGHTS")
    if env_deck:
        ep = Path(env_deck).expanduser().resolve()
        if ep.is_file():
            return str(ep)
    candidates = [
        _VISION_WEIGHTS_DIR / "deck_v2_best.pt",
        _VISION_WEIGHTS_DIR / "deck_pilot_best.pt",
        _VISION_RUNS_DIR / "deck_v2" / "weights" / "best.pt",
        _VISION_RUNS_DIR / "deck_pilot" / "weights" / "best.pt",
    ]
    for c in candidates:
        if c.is_file():
            return str(c.resolve())
    env_yoloe = os.environ.get("OPENTRONS_YOLOE_WEIGHTS")
    if env_yoloe and str(env_yoloe).strip():
        return str(env_yoloe).strip()
    bundled_yoloe = _VISION_WEIGHTS_DIR / "yoloe-26s-seg.pt"
    if bundled_yoloe.is_file():
        return str(bundled_yoloe.resolve())
    return "yoloe-26s-seg.pt"


def _path_suggests_trained_deck(weights_path: str) -> bool:
    pl = str(weights_path or "").replace("\\", "/").lower()
    if "/vision/" in pl and "best.pt" in pl:
        return True
    if "/deck_v" in pl or "deck_pilot" in pl:
        return True
    env_deck = os.environ.get("OPENTRONS_DECK_YOLO_WEIGHTS")
    if env_deck:
        try:
            if Path(weights_path).resolve() == Path(env_deck).expanduser().resolve():
                return True
        except OSError:
            pass
    return False


def _model_has_tiprack_family_names(model: Any) -> bool:
    names = getattr(model, "names", None)
    if isinstance(names, dict):
        seq = names.values()
    elif isinstance(names, (list, tuple)):
        seq = names
    else:
        return False
    for v in seq:
        s = str(v).strip().lower()
        if s.startswith("tiprack_"):
            return True
    return False


# Homography corner order (normalized image coords [nx, ny]):
# deck plane u,v in [0,1] with A1 -> (0,0), A3 -> (1,0), D3 -> (1,1), D1 -> (0,1).
DECK_CORNER_ORDER_DOC = "A1_A3_D3_D1_clockwise_deck_view"

# Flex OT-3 standard deck addressable slots (same order as MCP state.js FLEX_SLOT_NAMES)
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

# Text prompts for YOLOE (English; order defines class id -> canonical deck label).
# Rich visual cues help open-vocab matching on angled Flex camera views.
YOLOE_CLASS_PROMPTS = [
    "yellow pipette tip rack on lab robot deck",
    "teal or blue pipette tip rack on lab robot deck",
    "white or clear plastic 96-well microplate",
    "black plastic 96-well microplate",
    "plastic liquid reservoir trough on deck",
    "PCR thermocycler module with open lid and red heating block",
    "black heater shaker module with microplate on top",
    "dark rectangular laboratory trash bin opening on robot deck",
]

# One canonical label per prompt (slot_observations / expected_layout vocabulary).
YOLOE_CANONICAL_LABELS = [
    "tiprack",
    "tiprack",
    "plate",
    "plate",
    "reservoir",
    "module",
    "module",
    "trash_bin",
]

CANONICAL_ALIASES = {
    "tiprack": "tiprack",
    "tiprack_50": "tiprack",
    "tiprack_200": "tiprack",
    "tiprack_1000": "tiprack",
    "tip_rack": "tiprack",
    "plate": "plate",
    "well_plate": "plate",
    "reservoir": "reservoir",
    "module": "module",
    "trash_bin": "trash_bin",
    "trash": "trash_bin",
    "thermocycler": "module",
    "heater_shaker": "module",
    "heater-shaker": "module",
}

# When YOLOE text prompts are unavailable (missing CLIP) or user selects a COCO checkpoint,
# map COCO-ish class names to our deck vocabulary (best-effort; flag needs_human_review).
COCO_NAME_TO_CANONICAL = {
    "cup": "reservoir",
    "bottle": "reservoir",
    "bowl": "reservoir",
    "wine glass": "reservoir",
    "vase": "reservoir",
    "sink": "reservoir",
    "refrigerator": "module",
    "oven": "module",
    "microwave": "module",
    "tv": "module",
    "laptop": "module",
    "keyboard": "module",
    "mouse": "module",
    "book": "plate",
    "cell phone": "module",
    "toaster": "module",
    "person": "unknown",
}

# Lab-tuned YOLO training classes -> MCP expected_layout vocabulary
LAB_CLASS_TO_CANONICAL = {
    "tiprack_50": "tiprack",
    "tiprack_200": "tiprack",
    "tiprack_1000": "tiprack",
    "plate": "plate",
    "reservoir": "reservoir",
    "module": "module",
    "trash_bin": "trash_bin",
}


def _norm_expected_key(slot: str) -> str:
    return str(slot or "").strip().upper()


def _norm_expected_value(val: str) -> str:
    k = str(val or "").strip().lower()
    return CANONICAL_ALIASES.get(k, k)


def _slot_indices() -> dict[str, tuple[int, int]]:
    """Map slot name to (row 0-3, col 0-2) for A1..D3 grid."""
    out: dict[str, tuple[int, int]] = {}
    for slot in FLEX_SLOTS:
        row = ord(slot[0]) - ord("A")
        col = int(slot[1]) - 1
        out[slot] = (row, col)
    return out


SLOT_INDICES = _slot_indices()


def _slot_rect(slot: str) -> tuple[float, float, float, float]:
    row, col = SLOT_INDICES[slot]
    x1 = col * SLOT_WIDTH
    x2 = (col + 1) * SLOT_WIDTH
    y1 = row * SLOT_HEIGHT
    y2 = (row + 1) * SLOT_HEIGHT
    return x1, y1, x2, y2


def _slot_polygon(slot: str) -> list[list[float]]:
    x1, y1, x2, y2 = _slot_rect(slot)
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def _unique(values: list[Any]) -> list[Any]:
    out: list[Any] = []
    seen: set[Any] = set()
    for value in values:
        key = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _confidence_band(confidence: float | None) -> str:
    if confidence is None:
        return "none"
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.55:
        return "medium"
    return "low"


def _slot_center(slot: str) -> tuple[float, float]:
    x1, y1, x2, y2 = _slot_rect(slot)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _slot_delta(primary_slot: str, other_slot: str) -> tuple[int, int]:
    prow, pcol = SLOT_INDICES[primary_slot]
    orow, ocol = SLOT_INDICES[other_slot]
    return abs(orow - prow), abs(ocol - pcol)


def _polygon_span(polygon: list[list[float]]) -> tuple[float, float]:
    if not polygon:
        return 0.0, 0.0
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return max(xs) - min(xs), max(ys) - min(ys)


def _coverage_policy(label: str | None) -> dict[str, Any]:
    if label == "module":
        return {
            "allow_multi_slot": True,
            "absolute_threshold": 0.015,
            "relative_threshold": 0.35,
            "vertical_relative_threshold": 0.5,
            "horizontal_relative_threshold": 0.55,
            "poly_fraction": 0.12,
            "slot_fraction": 0.15,
            "row_span_slots": 1.05,
            "col_span_slots": 1.05,
        }
    if label in {"tiprack", "plate", "reservoir"}:
        return {
            "allow_multi_slot": False,
            "absolute_threshold": 0.02,
            "relative_threshold": 0.7,
            "vertical_relative_threshold": 0.7,
            "horizontal_relative_threshold": 0.7,
            "poly_fraction": 0.2,
            "slot_fraction": 0.2,
            "row_span_slots": 1.2,
            "col_span_slots": 1.2,
        }
    if label == "trash_bin":
        return {
            "allow_multi_slot": False,
            "absolute_threshold": 0.02,
            "relative_threshold": 0.75,
            "vertical_relative_threshold": 0.75,
            "horizontal_relative_threshold": 0.75,
            "poly_fraction": 0.2,
            "slot_fraction": 0.2,
            "row_span_slots": 1.2,
            "col_span_slots": 1.2,
        }
    return {
        "allow_multi_slot": True,
        "absolute_threshold": 0.015,
        "relative_threshold": 0.45,
        "vertical_relative_threshold": 0.45,
        "horizontal_relative_threshold": 0.45,
        "poly_fraction": 0.15,
        "slot_fraction": 0.18,
        "row_span_slots": 1.1,
        "col_span_slots": 1.1,
    }


def _select_covered_slots(
    positive_scores: dict[str, float],
    *,
    primary_slot: str,
    poly_area: float,
    polygon: list[list[float]],
    label: str | None,
) -> list[str]:
    if not positive_scores:
        return []

    policy = _coverage_policy(label)
    if not policy["allow_multi_slot"]:
        return [primary_slot]

    max_overlap = positive_scores.get(primary_slot, 0.0)
    polygon_width, polygon_height = _polygon_span(polygon)
    covered = [primary_slot]
    for slot, score in positive_scores.items():
        if slot == primary_slot:
            continue
        row_delta, col_delta = _slot_delta(primary_slot, slot)
        relative_threshold = policy["relative_threshold"]
        if row_delta and not col_delta:
            relative_threshold = policy.get("vertical_relative_threshold", relative_threshold)
        elif col_delta and not row_delta:
            relative_threshold = policy.get("horizontal_relative_threshold", relative_threshold)
        if score < max(policy["absolute_threshold"], max_overlap * relative_threshold):
            continue
        if not (score / poly_area >= policy["poly_fraction"] or score / SLOT_AREA >= policy["slot_fraction"]):
            continue
        if row_delta and polygon_height < (SLOT_HEIGHT * policy["row_span_slots"] * row_delta):
            continue
        if col_delta and polygon_width < (SLOT_WIDTH * policy["col_span_slots"] * col_delta):
            continue
        covered.append(slot)

    return sorted(covered, key=lambda slot: FLEX_SLOTS.index(slot))


def _grid_cell(nx: float, ny: float) -> tuple[str, list[str]]:
    """
    Map normalized center (nx, ny) in [0,1] to a Flex slot using a uniform 4x3 grid.
    Returns (slot_name, boundary_uncertainty_notes).
    """
    uncertainties: list[str] = []
    for b in (1.0 / 3.0, 2.0 / 3.0):
        if abs(nx - b) < BOUNDARY_EPS:
            uncertainties.append(f"near_vertical_grid nx={nx:.3f}")
    for b in (0.25, 0.5, 0.75):
        if abs(ny - b) < BOUNDARY_EPS:
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
    """Map deck-plane normalized coords (u,v in [0,1]) to A1..D3; u=cols, v=rows A->D."""
    uncertainties: list[str] = []
    ux = max(0.0, min(1.0, ux))
    uy = max(0.0, min(1.0, uy))
    for b in (1.0 / 3.0, 2.0 / 3.0):
        if abs(ux - b) < BOUNDARY_EPS:
            uncertainties.append(f"near_vertical_deck_ux={ux:.3f}")
    for b in (0.25, 0.5, 0.75):
        if abs(uy - b) < BOUNDARY_EPS:
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


def _build_homography_from_corners_norm(
    corners_norm: list[Any],
    w: int,
    h: int,
) -> tuple[Any | None, list[str]]:
    """Image (px) -> deck plane [0,1]^2. corners_norm: four [nx,ny] per DECK_CORNER_ORDER_DOC."""
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
            if not isinstance(c, (list, tuple)) or len(c) < 2:
                return None, ["deck_corners_invalid_point"]
            src_list.append([float(c[0]) * w, float(c[1]) * h])
        src = np.array(src_list, dtype=np.float32)
        dst = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]], dtype=np.float32)
        hmat = cv2.getPerspectiveTransform(src, dst)
        return hmat, []
    except Exception as exc:
        return None, [f"homography_failed:{type(exc).__name__}:{exc}"]


def _load_sidecar_deck_corners(image_path: Path) -> list[list[float]] | None:
    sidecar = image_path.parent / "labels" / f"{image_path.stem}.labels.json"
    if not sidecar.is_file():
        return None
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    corners = data.get("optional_deck_corners_norm")
    if not isinstance(corners, list) or len(corners) != 4:
        return None
    out: list[list[float]] = []
    for c in corners:
        if not isinstance(c, (list, tuple)) or len(c) < 2:
            return None
        out.append([float(c[0]), float(c[1])])
    return _pick_ordered_deck_corners(out)


def _parse_slot_centers_norm(raw: Any) -> dict[str, list[float]] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, list[float]] = {}
    for slot in FLEX_SLOTS:
        pt = raw.get(slot)
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            return None
        out[slot] = [float(pt[0]), float(pt[1])]
    return out


def _mean_or_none(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _extrapolate_outer(low_center: float, inner_boundary: float) -> float:
    return 2.0 * low_center - inner_boundary


def _slot_name_from_indices(row: int, col: int) -> str:
    return f"{chr(ord('A') + row)}{col + 1}"


def _build_slot_polygons_from_centers_norm(
    centers: dict[str, list[float]],
) -> dict[str, list[list[float]]]:
    col_x: list[float | None] = [None, None, None, None]
    for boundary in (1, 2):
        xs: list[float] = []
        for row in range(4):
            left = centers.get(_slot_name_from_indices(row, boundary - 1))
            right = centers.get(_slot_name_from_indices(row, boundary))
            if left and right:
                xs.append((float(left[0]) + float(right[0])) / 2.0)
        col_x[boundary] = _mean_or_none(xs)

    row_y: list[float | None] = [None, None, None, None, None]
    for boundary in (1, 2, 3):
        ys: list[float] = []
        for col in range(3):
            up = centers.get(_slot_name_from_indices(boundary - 1, col))
            down = centers.get(_slot_name_from_indices(boundary, col))
            if up and down:
                ys.append((float(up[1]) + float(down[1])) / 2.0)
        row_y[boundary] = _mean_or_none(ys)

    if col_x[1] is None or col_x[2] is None or row_y[1] is None or row_y[3] is None:
        raise ValueError("slot_centers_norm does not span enough of the deck grid")

    col_x[0] = _mean_or_none(
        [_extrapolate_outer(float(centers[_slot_name_from_indices(r, 0)][0]), col_x[1]) for r in range(4)]
    )
    col_x[3] = _mean_or_none(
        [_extrapolate_outer(float(centers[_slot_name_from_indices(r, 2)][0]), col_x[2]) for r in range(4)]
    )
    row_y[0] = _mean_or_none(
        [_extrapolate_outer(float(centers[_slot_name_from_indices(0, c)][1]), row_y[1]) for c in range(3)]
    )
    row_y[4] = _mean_or_none(
        [_extrapolate_outer(float(centers[_slot_name_from_indices(3, c)][1]), row_y[3]) for c in range(3)]
    )

    polys: dict[str, list[list[float]]] = {}
    for slot in FLEX_SLOTS:
        row = ord(slot[0]) - ord("A")
        col = int(slot[1]) - 1
        polys[slot] = [
            [col_x[col], row_y[row]],
            [col_x[col + 1], row_y[row]],
            [col_x[col + 1], row_y[row + 1]],
            [col_x[col], row_y[row + 1]],
        ]
    return polys


def _load_sidecar_slot_centers(image_path: Path) -> dict[str, list[float]] | None:
    sidecar = image_path.parent / "labels" / f"{image_path.stem}.labels.json"
    if not sidecar.is_file():
        return None
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if str(data.get("calibration_method") or "") != "slot_centers_v1":
        return None
    return _parse_slot_centers_norm(data.get("slot_centers_norm"))


def _point_in_polygon_norm(px: float, py: float, polygon: list[list[float]]) -> bool:
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside


def _slot_mesh_rect(slot: str, slot_polygons: dict[str, list[list[float]]]) -> tuple[float, float, float, float]:
    poly = slot_polygons[slot]
    xs = [float(p[0]) for p in poly]
    ys = [float(p[1]) for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _slot_overlap_scores_mesh(
    polygon: list[list[float]],
    slot_polygons: dict[str, list[list[float]]],
) -> dict[str, float]:
    return {
        slot: _polygon_area(_clip_polygon_to_rect(polygon, _slot_mesh_rect(slot, slot_polygons)))
        for slot in FLEX_SLOTS
    }


def _map_center_to_slot_mesh(
    nx: float,
    ny: float,
    slot_polygons: dict[str, list[list[float]]],
    slot_centers: dict[str, list[float]] | None = None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    hits = [slot for slot in FLEX_SLOTS if _point_in_polygon_norm(nx, ny, slot_polygons[slot])]
    notes: list[str] = []
    if len(hits) == 1:
        return hits[0], notes, None
    if len(hits) > 1:
        notes.append("point_in_multiple_slot_polygons")
        if slot_centers:
            best = min(hits, key=lambda s: (nx - slot_centers[s][0]) ** 2 + (ny - slot_centers[s][1]) ** 2)
            return best, notes, None
        return hits[0], notes, None
    if slot_centers:
        best = min(
            FLEX_SLOTS,
            key=lambda s: (nx - slot_centers[s][0]) ** 2 + (ny - slot_centers[s][1]) ** 2,
        )
        notes.append("nearest_slot_center_fallback")
        return best, notes, None
    slot, grid_notes = _grid_cell(nx, ny)
    return slot, notes + grid_notes + ["slot_mesh_miss_fell_back_to_image_grid"], None


def _resolve_yoloe_prompt_lists(
    class_prompts: list[str] | None,
    canonical_labels: list[str] | None,
) -> tuple[list[str], list[str], dict[str, Any] | None]:
    """Return (prompts, canonical, None) or ([], [], error_result) for early return."""
    if class_prompts is None and canonical_labels is None:
        return list(YOLOE_CLASS_PROMPTS), list(YOLOE_CANONICAL_LABELS), None
    if class_prompts is None or canonical_labels is None:
        err = {
            "mode": "deck",
            "summary": "class_prompts and canonical_labels must both be set when overriding prompts.",
            "observed_items": [],
            "slot_observations": {s: {"state": "unknown"} for s in FLEX_SLOTS},
            "mismatches": [],
            "uncertainties": ["invalid_prompt_override"],
            "needs_human_review": True,
            "annotated_image_path": None,
            "error": {"type": "ValueError", "detail": "class_prompts/canonical_labels mismatch"},
        }
        return [], [], err
    if len(class_prompts) != len(canonical_labels) or len(class_prompts) < 1:
        err = {
            "mode": "deck",
            "summary": "class_prompts and canonical_labels must be non-empty and equal length.",
            "observed_items": [],
            "slot_observations": {s: {"state": "unknown"} for s in FLEX_SLOTS},
            "mismatches": [],
            "uncertainties": ["invalid_prompt_override"],
            "needs_human_review": True,
            "annotated_image_path": None,
            "error": {"type": "ValueError", "detail": "class_prompts length mismatch"},
        }
        return [], [], err
    normed = [str(x).strip().lower() for x in canonical_labels]
    for lab in normed:
        if lab not in CANONICAL_ALIASES and lab not in ("unknown", "empty"):
            err = {
                "mode": "deck",
                "summary": f"Unknown canonical label in canonical_labels: {lab}",
                "observed_items": [],
                "slot_observations": {s: {"state": "unknown"} for s in FLEX_SLOTS},
                "mismatches": [],
                "uncertainties": ["invalid_canonical_label"],
                "needs_human_review": True,
                "annotated_image_path": None,
                "error": {"type": "ValueError", "detail": lab},
            }
            return [], [], err
    return list(class_prompts), normed, None


def _canonical_for_class_id(cls_id: int, canonical_list: list[str]) -> str:
    if 0 <= cls_id < len(canonical_list):
        raw = canonical_list[int(cls_id)]
        return CANONICAL_ALIASES.get(raw, raw)
    return "unknown"


def _should_use_yoloe_prompts(weights: str, use_text_prompts: bool | None) -> bool:
    if use_text_prompts is not None:
        return bool(use_text_prompts)
    w = (weights or "").lower()
    return "yoloe" in w or "yolo-e" in w


def _label_from_coco_name(name: str) -> tuple[str, str]:
    raw = str(name or "").strip().lower()
    if raw in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[raw], raw
    mapped = COCO_NAME_TO_CANONICAL.get(raw, "unknown")
    return mapped, raw


def _label_from_lab_class_name(name: str) -> tuple[str, str]:
    raw = str(name or "").strip().lower()
    if raw in LAB_CLASS_TO_CANONICAL:
        return LAB_CLASS_TO_CANONICAL[raw], raw
    if raw in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[raw], raw
    mapped = COCO_NAME_TO_CANONICAL.get(raw, "unknown")
    return mapped, raw


def _build_empty_slot_observation() -> dict[str, Any]:
    return {
        "state": "unknown",
        "source": "grid_geometry",
        "label": None,
        "confidence_band": "none",
        "reasons": [],
        "covered_by": [],
    }


def _polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        area += (x1 * y2) - (x2 * y1)
    return abs(area) / 2.0


def _clip_polygon_to_rect(
    polygon: list[list[float]],
    rect: tuple[float, float, float, float],
) -> list[list[float]]:
    x_min, y_min, x_max, y_max = rect

    def clip_against(points: list[list[float]], boundary: str) -> list[list[float]]:
        if not points:
            return []
        out: list[list[float]] = []
        prev = points[-1]

        def inside(pt: list[float]) -> bool:
            x, y = pt
            if boundary == "left":
                return x >= x_min
            if boundary == "right":
                return x <= x_max
            if boundary == "top":
                return y >= y_min
            return y <= y_max

        def intersect(p1: list[float], p2: list[float]) -> list[float]:
            x1, y1 = p1
            x2, y2 = p2
            dx = x2 - x1
            dy = y2 - y1
            if boundary in {"left", "right"}:
                x_edge = x_min if boundary == "left" else x_max
                if abs(dx) < 1e-9:
                    return [x_edge, y1]
                t = (x_edge - x1) / dx
                return [x_edge, y1 + t * dy]
            y_edge = y_min if boundary == "top" else y_max
            if abs(dy) < 1e-9:
                return [x1, y_edge]
            t = (y_edge - y1) / dy
            return [x1 + t * dx, y_edge]

        for current in points:
            if inside(current):
                if not inside(prev):
                    out.append(intersect(prev, current))
                out.append(current)
            elif inside(prev):
                out.append(intersect(prev, current))
            prev = current
        return out

    clipped = polygon
    for boundary in ("left", "right", "top", "bottom"):
        clipped = clip_against(clipped, boundary)
        if not clipped:
            break
    return clipped


def _slot_overlap_scores(polygon: list[list[float]]) -> dict[str, float]:
    return {
        slot: _polygon_area(_clip_polygon_to_rect(polygon, _slot_rect(slot)))
        for slot in FLEX_SLOTS
    }


def _normalize_polygon(points: list[list[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for x, y in points:
        out.append([max(0.0, min(1.0, float(x))), max(0.0, min(1.0, float(y)))])
    return out


def _pick_ordered_deck_corners(points: list[list[float]]) -> list[list[float]] | None:
    if len(points) < 4:
        return None

    scorers = [
        lambda p: p[0] + p[1],      # A1: top-left
        lambda p: -(p[0] - p[1]),   # A3: top-right
        lambda p: -(p[0] + p[1]),   # D3: bottom-right
        lambda p: p[0] - p[1],      # D1: bottom-left
    ]
    chosen: list[int] = []
    used: set[int] = set()
    for scorer in scorers:
        ranked = sorted(range(len(points)), key=lambda idx: scorer(points[idx]))
        found = next((idx for idx in ranked if idx not in used), None)
        if found is None:
            return None
        chosen.append(found)
        used.add(found)
    if len(set(chosen)) != 4:
        return None
    return [points[idx] for idx in chosen]


def _project_bbox_polygon(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    w: int,
    h: int,
    hmat: Any | None,
) -> tuple[list[list[float]], list[str]]:
    polygon_image_norm = _normalize_polygon(
        [
            [x1 / w, y1 / h],
            [x2 / w, y1 / h],
            [x2 / w, y2 / h],
            [x1 / w, y2 / h],
        ]
    )
    if hmat is None:
        return polygon_image_norm, ["uniform_grid_fallback"]

    try:
        import cv2
        import numpy as np
    except ImportError:
        return polygon_image_norm, ["opencv_missing_fell_back_to_image_grid", "uniform_grid_fallback"]

    pts = np.array(
        [[[x1, y1], [x2, y1], [x2, y2], [x1, y2]]],
        dtype=np.float32,
    )
    out = cv2.perspectiveTransform(pts, hmat)
    polygon = _normalize_polygon([[float(px), float(py)] for px, py in out[0]])
    return polygon, []


def _map_center_to_slot(
    nx: float,
    ny: float,
    w: int,
    h: int,
    hmat: Any | None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    """
    Map bbox center in image normalized coords to Flex slot.
    If hmat is set, also returns deck_plane_norm in extra dict.
    """
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


def _build_slot_coverage(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    w: int,
    h: int,
    hmat: Any | None,
    label: str | None = None,
    slot_polygons_mesh: dict[str, list[list[float]]] | None = None,
    slot_centers_mesh: dict[str, list[float]] | None = None,
) -> dict[str, Any]:
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    nx = max(0.0, min(1.0, cx / w))
    ny = max(0.0, min(1.0, cy / h))
    deck_extra: dict[str, Any] | None = None
    if slot_polygons_mesh is not None:
        center_slot, center_notes, deck_extra = _map_center_to_slot_mesh(
            nx, ny, slot_polygons_mesh, slot_centers_mesh
        )
        polygon = _normalize_polygon(
            [
                [x1 / w, y1 / h],
                [x2 / w, y1 / h],
                [x2 / w, y2 / h],
                [x1 / w, y2 / h],
            ]
        )
        polygon_notes: list[str] = ["slot_centers_mesh"]
        overlap_scores = _slot_overlap_scores_mesh(polygon, slot_polygons_mesh)
    else:
        center_slot, center_notes, deck_extra = _map_center_to_slot(nx, ny, w, h, hmat)
        polygon, polygon_notes = _project_bbox_polygon(x1, y1, x2, y2, w, h, hmat)
        overlap_scores = _slot_overlap_scores(polygon)
    positive_scores = {slot: score for slot, score in overlap_scores.items() if score > 1e-6}
    max_slot = max(positive_scores, key=positive_scores.get, default=center_slot)
    max_overlap = positive_scores.get(max_slot, 0.0)
    poly_area = max(_polygon_area(polygon), 1e-6)
    assignable_to_slots = True
    if (hmat is not None or slot_polygons_mesh is not None) and max_overlap < 0.005:
        assignable_to_slots = False
        covered_slots = []
    else:
        covered_slots = _select_covered_slots(
            positive_scores,
            primary_slot=max_slot,
            poly_area=poly_area,
            polygon=polygon,
            label=label,
        )
        if not covered_slots:
            covered_slots = [max_slot]

    overlap_reasons: list[str] = []
    if center_notes:
        overlap_reasons.append("near_slot_boundary")
    overlap_reasons.extend(polygon_notes)
    if not assignable_to_slots:
        overlap_reasons.append("outside_deck_projection")
    if len(covered_slots) > 1:
        overlap_reasons.append("coverage_spans_multiple_slots")
    if max_overlap < 0.03:
        overlap_reasons.append("small_projected_overlap")

    covered_slot_overlaps = {slot: round(overlap_scores[slot], 4) for slot in covered_slots}
    payload = {
        "primary_slot": max_slot,
        "covered_slots": covered_slots,
        "covered_slot_overlaps": covered_slot_overlaps,
        "coverage_notes": _unique(overlap_reasons),
        "center_norm": [round(nx, 4), round(ny, 4)],
        "coverage_polygon_norm": [[round(px, 4), round(py, 4)] for px, py in polygon],
        "assignable_to_slots": assignable_to_slots,
        "max_overlap": round(max_overlap, 4),
    }
    if deck_extra:
        payload.update(deck_extra)
    return payload


def _slot_source(use_prompts: bool, lab_tuned: bool) -> str:
    if use_prompts:
        return "yoloe"
    if lab_tuned:
        return "trained_yolo"
    return "coco_fallback"


def _should_promote_reviewable_slot(
    dets: list[dict[str, Any]],
    *,
    slot_mapping_method: str,
    coco_untrusted: bool,
) -> bool:
    if slot_mapping_method not in {"deck_homography", "slot_centers_mesh"} or coco_untrusted or not dets:
        return False

    allowed_reasons = {"low_confidence_detection", "coverage_spans_multiple_slots", "near_slot_boundary"}
    labels = {det.get("label") for det in dets if det.get("label")}
    if len(labels) != 1:
        return False

    max_conf = max(float(det.get("confidence") or 0.0) for det in dets)
    if max_conf < 0.35:
        return False

    combined_reasons: set[str] = set()
    for det in dets:
        reasons = set(det.get("reasons") or [])
        combined_reasons.update(reasons)
        if reasons - allowed_reasons:
            return False
        mapping_notes = list(det.get("mapping_notes") or [])
        if any(not str(note).startswith("near_") for note in mapping_notes):
            return False
        if det.get("assignable_to_slots") is False:
            return False

    if "near_slot_boundary" in combined_reasons and max_conf < 0.75:
        return False

    return True


def _build_slot_observations(
    slot_to_detections: dict[str, list[dict[str, Any]]],
    *,
    slot_mapping_method: str,
    obs_source: str,
    coco_untrusted: bool,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    slot_observations: dict[str, dict[str, Any]] = {}
    uncertainties_global: list[str] = []

    for slot in FLEX_SLOTS:
        dets = slot_to_detections.get(slot, [])
        if not dets:
            reasons: list[str] = []
            if slot_mapping_method not in {"deck_homography", "slot_centers_mesh"}:
                reasons.append("uniform_grid_fallback")
            if coco_untrusted:
                reasons.append("coco_fallback_not_labware_tuned")
            state = "uncertain" if reasons else "empty"
            slot_observations[slot] = {
                "state": state,
                "source": "grid_geometry" if state == "empty" else obs_source,
                "label": None,
                "confidence_band": "low" if reasons else "high",
                "reasons": reasons,
                "covered_by": [],
            }
            continue

        labels = sorted({d["label"] for d in dets})
        reasons = _unique(
            [reason for det in dets for reason in det.get("reasons", [])]
            + [reason for det in dets for reason in det.get("mapping_notes", [])]
        )
        covered_by = [det["detection_id"] for det in dets]
        max_conf = max(float(det["confidence"]) for det in dets)
        confidence_band = _confidence_band(max_conf)
        label = labels[0] if len(labels) == 1 else None
        state = "occupied"

        if len(labels) > 1:
            state = "uncertain"
            reasons = _unique(reasons + ["multiple_labels_in_slot"])
            confidence_band = "low"
            uncertainties_global.append(f"multiple_labels_in_{slot}")
        elif any(det.get("needs_human_review") for det in dets) or coco_untrusted:
            if _should_promote_reviewable_slot(
                dets,
                slot_mapping_method=slot_mapping_method,
                coco_untrusted=coco_untrusted,
            ):
                state = "occupied"
                reasons = _unique(reasons + ["promoted_from_reviewable_detection"])
            else:
                state = "uncertain"
                if coco_untrusted:
                    reasons = _unique(reasons + ["coco_fallback_not_labware_tuned"])
        elif slot_mapping_method not in {"deck_homography", "slot_centers_mesh"}:
            state = "uncertain"
            reasons = _unique(reasons + ["uniform_grid_fallback"])

        slot_observations[slot] = {
            "state": state,
            "source": obs_source,
            "label": label,
            "labels": labels if len(labels) > 1 else None,
            "confidence": round(max_conf, 4),
            "confidence_band": confidence_band,
            "reasons": reasons,
            "covered_by": covered_by,
            "detection_count": len(dets),
        }

    return slot_observations, uncertainties_global


def _compute_mismatches(
    expected_layout: dict[str, Any] | None,
    slot_observations: dict[str, dict[str, Any]],
    *,
    detection_slots: list[str] | None = None,
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if not expected_layout:
        return mismatches

    eval_slots = set(detection_slots or FLEX_SLOTS)

    for raw_slot, raw_exp in expected_layout.items():
        slot = _norm_expected_key(raw_slot)
        if slot not in FLEX_SLOTS or slot not in eval_slots:
            continue
        obs = slot_observations.get(slot, _build_empty_slot_observation())
        if obs.get("state") == "fixed":
            continue
        exp = _norm_expected_value(str(raw_exp))
        st = obs.get("state")
        obs_label = obs.get("label")
        obs_labels = obs.get("labels") or ([obs_label] if obs_label else [])
        if exp in {"", "empty"}:
            if st == "occupied":
                mismatches.append(
                    {
                        "slot": slot,
                        "expected": "empty",
                        "observed": obs_label,
                        "reason": "expected_empty_but_occupied",
                    }
                )
            elif st == "uncertain" and obs_labels:
                mismatches.append(
                    {
                        "slot": slot,
                        "expected": "empty",
                        "observed": obs_labels,
                        "reason": "expected_empty_but_uncertain",
                    }
                )
            continue

        if st == "empty":
            mismatches.append(
                {
                    "slot": slot,
                    "expected": exp,
                    "observed": None,
                    "reason": "expected_occupied_but_empty",
                }
            )
        elif st == "occupied" and obs_label and obs_label != exp:
            mismatches.append(
                {
                    "slot": slot,
                    "expected": exp,
                    "observed": obs_label,
                    "reason": "label_mismatch",
                }
            )
        elif st == "uncertain":
            mismatches.append(
                {
                    "slot": slot,
                    "expected": exp,
                    "observed": obs_labels or None,
                    "reason": "uncertain_slot",
                }
            )

    return mismatches


def _apply_mismatch_flags(
    slot_observations: dict[str, dict[str, Any]],
    mismatches: list[dict[str, Any]],
) -> None:
    for mismatch in mismatches:
        slot = mismatch["slot"]
        obs = slot_observations.get(slot)
        if not obs:
            continue
        obs["state"] = "uncertain"
        obs["confidence_band"] = "low"
        obs["reasons"] = _unique(list(obs.get("reasons") or []) + ["expected_layout_mismatch"])


def _build_summary(
    slot_observations: dict[str, dict[str, Any]],
    mismatches: list[dict[str, Any]],
    *,
    detection_slots: list[str] | None = None,
) -> str:
    slots = detection_slots or list(FLEX_SLOTS)
    relevant = {slot: slot_observations.get(slot, {}) for slot in slots}
    confident_slots = sum(
        1 for obs in relevant.values() if obs.get("state") in {"occupied", "empty"}
    )
    uncertain_slots = sum(1 for obs in relevant.values() if obs.get("state") == "uncertain")
    coverage_slots = sum(
        1
        for obs in relevant.values()
        if "coverage_spans_multiple_slots" in (obs.get("reasons") or [])
    )
    fixed_slots = sum(1 for obs in slot_observations.values() if obs.get("state") == "fixed")
    parts = [
        f"{confident_slots}/{len(slots)} detection slots confident",
        f"{coverage_slots} slots use coverage mapping",
        f"{uncertain_slots} detection slots need review",
    ]
    if fixed_slots:
        parts.append(f"{fixed_slots} fixed slots from layout policy")
    if mismatches:
        parts.append(f"{len(mismatches)} mismatches vs expected_layout")
    return "; ".join(parts) + "."


def _render_operator_overlay(
    image: Any,
    *,
    observed_items: list[dict[str, Any]],
    slot_observations: dict[str, dict[str, Any]],
    slot_mapping_meta: dict[str, Any],
    model_meta: dict[str, Any],
    mismatches: list[dict[str, Any]],
    uncertainties: list[str],
) -> Any:
    import cv2
    import numpy as np

    canvas = image.copy()
    h, w = canvas.shape[:2]
    mismatch_slots = {item["slot"] for item in mismatches}
    corners = slot_mapping_meta.get("deck_corners_norm")
    hmat_inv = None
    if isinstance(corners, list) and len(corners) == 4:
        src = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]], dtype=np.float32)
        dst = np.array(
            [[float(c[0]) * w, float(c[1]) * h] for c in corners],
            dtype=np.float32,
        )
        hmat_inv = cv2.getPerspectiveTransform(src, dst)

    for item in observed_items:
        x1, y1, x2, y2 = [int(round(v)) for v in item["bbox_xyxy"]]
        box_color = (255, 190, 0) if item.get("needs_human_review") else (255, 255, 255)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, 2)
        covered = ",".join(item.get("covered_slots") or [item.get("primary_slot") or "?"])
        label = f"{item['label']} {item['confidence']:.2f} [{covered}]"
        cv2.putText(
            canvas,
            label[:48],
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            box_color,
            2,
            cv2.LINE_AA,
        )

    for slot in FLEX_SLOTS:
        obs = slot_observations.get(slot, _build_empty_slot_observation())
        if slot in mismatch_slots:
            color = (0, 0, 255)
        elif obs.get("state") == "uncertain":
            color = (0, 215, 255)
        else:
            color = (0, 200, 0)

        if hmat_inv is None:
            x1n, y1n, x2n, y2n = _slot_rect(slot)
            pts = np.array(
                [
                    [int(round(x1n * w)), int(round(y1n * h))],
                    [int(round(x2n * w)), int(round(y1n * h))],
                    [int(round(x2n * w)), int(round(y2n * h))],
                    [int(round(x1n * w)), int(round(y2n * h))],
                ],
                dtype=np.int32,
            )
        else:
            deck_poly = np.array([_slot_polygon(slot)], dtype=np.float32)
            pts = cv2.perspectiveTransform(deck_poly, hmat_inv)[0].astype(np.int32)

        cv2.polylines(canvas, [pts], isClosed=True, color=color, thickness=2)
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        label = obs.get("label") or ("/".join(obs.get("labels") or []) if obs.get("labels") else obs.get("state"))
        cv2.putText(
            canvas,
            f"{slot}:{label}"[:28],
            (max(12, cx - 45), max(20, cy)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            2,
            cv2.LINE_AA,
        )

    if isinstance(corners, list) and len(corners) == 4:
        pts = np.array(
            [[int(round(float(c[0]) * w)), int(round(float(c[1]) * h))] for c in corners],
            dtype=np.int32,
        )
        cv2.polylines(canvas, [pts], isClosed=True, color=(0, 255, 255), thickness=3)
        for idx, point in enumerate(("A1", "A3", "D3", "D1")):
            x, y = int(pts[idx][0]), int(pts[idx][1])
            cv2.circle(canvas, (x, y), 6, (0, 255, 255), -1)
            cv2.putText(
                canvas,
                point,
                (x + 6, y - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

    legend_lines = [
        f"mapping={slot_mapping_meta.get('method')}",
        f"model={model_meta.get('family')} lab_tuned={model_meta.get('lab_tuned')}",
        f"review_reasons={','.join(_unique(uncertainties)[:3]) or 'none'}",
        "green=trusted yellow=uncertain red=mismatch",
    ]
    y = 24
    for line in legend_lines:
        cv2.putText(
            canvas,
            line[:72],
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += 24

    return canvas


def _run_model_predictions(
    *,
    weights: str,
    image_path: Path,
    use_text_prompts: bool | None,
    class_prompts: list[str],
) -> tuple[Any | None, Any | None, str, bool, bool, list[str], dict[str, Any] | None]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        return None, None, weights, False, False, [], {
            "summary": "ultralytics not installed in this Python environment.",
            "observed_items": [],
            "slot_observations": {},
            "mismatches": [],
            "uncertainties": [
                "install_vision_extra",
                "uv sync --extra vision (repo root) or pip install ultralytics",
            ],
            "needs_human_review": True,
            "annotated_image_path": None,
            "error": {"type": "ImportError", "detail": str(exc)},
        }

    use_prompts = _should_use_yoloe_prompts(weights, use_text_prompts)
    if _path_suggests_trained_deck(weights):
        use_prompts = False

    uncertainties_preflight: list[str] = []
    effective_weights = weights
    lab_tuned = False

    try:
        model = YOLO(weights)
        if use_prompts:
            try:
                model.set_classes(class_prompts)
            except Exception as exc:
                err_s = str(exc).lower()
                if "clip" in err_s or "yoloe" in (weights or "").lower():
                    use_prompts = False
                    fb = os.environ.get("OPENTRONS_VISION_FALLBACK_WEIGHTS")
                    if not fb:
                        bundled_fb = _VISION_WEIGHTS_DIR / "yolo11n.pt"
                        fb = str(bundled_fb.resolve()) if bundled_fb.is_file() else DEFAULT_COCO_FALLBACK_WEIGHTS
                    effective_weights = fb
                    model = YOLO(fb)
                    uncertainties_preflight.append(
                        f"yoloe_clip_unavailable: using_fallback_weights={fb} ({type(exc).__name__}: {exc})"
                    )
                else:
                    raise

        lab_tuned = (not use_prompts) and (
            _path_suggests_trained_deck(effective_weights) or _model_has_tiprack_family_names(model)
        )
        results = model.predict(str(image_path), verbose=False)
        return model, results, effective_weights, use_prompts, lab_tuned, uncertainties_preflight, None
    except Exception as exc:
        return None, None, effective_weights, use_prompts, lab_tuned, uncertainties_preflight, {
            "summary": f"Vision inference failed: {exc}",
            "observed_items": [],
            "slot_observations": {s: {"state": "unknown"} for s in FLEX_SLOTS},
            "mismatches": [],
            "uncertainties": ["inference_error"],
            "needs_human_review": True,
            "annotated_image_path": None,
            "error": {"type": type(exc).__name__, "detail": str(exc)},
        }


def run_deck(
    image_path: Path,
    *,
    weights: str,
    conf_threshold: float,
    expected_layout: dict[str, Any] | None,
    annotated_path: Path | None,
    use_text_prompts: bool | None = None,
    deck_corners_norm: list[Any] | None = None,
    slot_centers_norm: dict[str, Any] | None = None,
    load_labels_sidecar: bool = True,
    class_prompts: list[str] | None = None,
    canonical_labels: list[str] | None = None,
) -> dict[str, Any]:
    layout_policy = _load_deck_layout_policy()
    fixed_slots = _fixed_slot_names(layout_policy)
    detection_slots = _detection_slot_names(layout_policy)
    detection_classes = _detection_class_names(layout_policy)

    prompts_eff, canon_eff, prompt_err = _resolve_yoloe_prompt_lists(class_prompts, canonical_labels)
    if prompt_err is not None:
        return prompt_err

    (
        model,
        results,
        effective_weights,
        use_prompts,
        lab_tuned,
        uncertainties_preflight,
        error_result,
    ) = _run_model_predictions(
        weights=weights,
        image_path=image_path,
        use_text_prompts=use_text_prompts,
        class_prompts=prompts_eff,
    )
    if error_result is not None:
        return {"mode": "deck", **error_result}
    if not results:
        return {
            "mode": "deck",
            "summary": "No inference results from model.",
            "observed_items": [],
            "slot_observations": {s: {"state": "unknown"} for s in FLEX_SLOTS},
            "mismatches": [],
            "uncertainties": ["empty_model_output"],
            "needs_human_review": True,
            "annotated_image_path": None,
        }

    r0 = results[0]
    im = r0.orig_img
    h, w = im.shape[:2]

    corners_src: list[Any] | None = deck_corners_norm
    corners_from: str | None = None
    centers_src: dict[str, list[float]] | None = None
    centers_from: str | None = None
    if slot_centers_norm is not None:
        parsed = _parse_slot_centers_norm(slot_centers_norm)
        if parsed is not None:
            centers_src = parsed
            centers_from = "payload"
    if centers_src is None and load_labels_sidecar:
        loaded_centers = _load_sidecar_slot_centers(image_path)
        if loaded_centers is not None:
            centers_src = loaded_centers
            centers_from = "labels_sidecar"

    if corners_src is None and load_labels_sidecar:
        loaded = _load_sidecar_deck_corners(image_path)
        if loaded is not None:
            corners_src = loaded
            corners_from = "labels_sidecar"
    elif corners_src is not None and corners_from is None:
        corners_from = "payload"

    if corners_src is None:
        default_cal = _load_default_deck_calibration()
        loaded_corners = default_cal.get("optional_deck_corners_norm")
        if isinstance(loaded_corners, list) and len(loaded_corners) == 4:
            corners_src = loaded_corners
            corners_from = "deck_calibration.json"

    hmat: Any | None = None
    slot_polygons_mesh: dict[str, list[list[float]]] | None = None
    slot_mapping_meta: dict[str, Any] = {
        "method": "uniform_image_grid",
        "corner_order_doc": DECK_CORNER_ORDER_DOC,
        "deck_corners_norm": None,
        "corners_source": None,
        "slot_centers_norm": None,
        "centers_source": None,
    }
    if centers_src is not None:
        try:
            slot_polygons_mesh = _build_slot_polygons_from_centers_norm(centers_src)
            slot_mapping_meta["method"] = "slot_centers_mesh"
            slot_mapping_meta["slot_centers_norm"] = centers_src
            slot_mapping_meta["centers_source"] = centers_from
            if corners_src is not None:
                slot_mapping_meta["deck_corners_norm"] = corners_src
                slot_mapping_meta["corners_source"] = corners_from
        except ValueError as exc:
            uncertainties_preflight.append(f"slot_centers_mesh_failed:{exc}")
            slot_polygons_mesh = None

    if slot_polygons_mesh is None and corners_src is not None:
        hmat, homog_notes = _build_homography_from_corners_norm(corners_src, w, h)
        uncertainties_preflight.extend(homog_notes)
        if hmat is not None:
            slot_mapping_meta["method"] = "deck_homography"
            slot_mapping_meta["deck_corners_norm"] = corners_src
            slot_mapping_meta["corners_source"] = corners_from
        else:
            slot_mapping_meta["homography_failed_notes"] = homog_notes

    observed_items: list[dict[str, Any]] = []
    slot_to_detections: dict[str, list[dict[str, Any]]] = {s: [] for s in FLEX_SLOTS}
    boxes = getattr(r0, "boxes", None)
    obs_source = _slot_source(use_prompts, lab_tuned)
    coco_untrusted = (not use_prompts) and (not lab_tuned)

    if boxes is not None and len(boxes):
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        for i in range(len(xyxy)):
            x1, y1, x2, y2 = (float(xyxy[i][j]) for j in range(4))
            cls_id = int(clss[i])
            conf = float(confs[i])
            if conf < conf_threshold:
                continue
            name_raw = None
            if use_prompts:
                label = _canonical_for_class_id(cls_id, canon_eff)
                evidence = "yoloe_text_prompt_detection"
            else:
                names = getattr(r0, "names", None) or getattr(model, "names", None)
                raw_name = ""
                if isinstance(names, dict):
                    raw_name = str(names.get(cls_id, "") or "")
                elif isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
                    raw_name = str(names[cls_id] or "")
                if lab_tuned and detection_classes and raw_name and raw_name not in detection_classes:
                    continue
                if lab_tuned:
                    label, name_raw = _label_from_lab_class_name(raw_name)
                    evidence = "trained_yolo_detection"
                else:
                    label, name_raw = _label_from_coco_name(raw_name)
                    evidence = "coco_checkpoint_mapping"

            coverage = _build_slot_coverage(
                x1,
                y1,
                x2,
                y2,
                w,
                h,
                hmat,
                label=label,
                slot_polygons_mesh=slot_polygons_mesh,
                slot_centers_mesh=centers_src,
            )
            item_reasons = list(coverage["coverage_notes"])
            if conf < LOW_CONFIDENCE_THRESHOLD:
                item_reasons.append("low_confidence_detection")
            if coco_untrusted:
                item_reasons.append("coco_fallback_not_labware_tuned")

            mapping_notes = [note for note in coverage["coverage_notes"] if note.startswith("near_")]
            needs_human_review = bool(
                conf < LOW_CONFIDENCE_THRESHOLD
                or coco_untrusted
                or "small_projected_overlap" in item_reasons
                or "outside_deck_projection" in item_reasons
                or "uniform_grid_fallback" in item_reasons
                or "near_slot_boundary" in item_reasons
            )

            item = {
                "detection_id": i + 1,
                "slot": coverage["primary_slot"],
                "primary_slot": coverage["primary_slot"],
                "covered_slots": coverage["covered_slots"],
                "covered_slot_overlaps": coverage["covered_slot_overlaps"],
                "label": label,
                "confidence": round(conf, 4),
                "confidence_band": _confidence_band(conf),
                "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center_norm": coverage["center_norm"],
                "evidence": evidence,
                "reasons": _unique(item_reasons),
                "mapping_notes": mapping_notes,
                "needs_human_review": needs_human_review,
                "assignable_to_slots": coverage["assignable_to_slots"],
            }
            if use_prompts and 0 <= cls_id < len(prompts_eff):
                item["prompt_index"] = cls_id
                item["prompt_text"] = prompts_eff[cls_id]
            if "deck_plane_norm" in coverage:
                item["deck_plane_norm"] = coverage["deck_plane_norm"]
            item["coverage_polygon_norm"] = coverage["coverage_polygon_norm"]
            if name_raw is not None:
                item["class_name_raw"] = name_raw

            observed_items.append(item)
            if coverage["assignable_to_slots"]:
                for slot in coverage["covered_slots"]:
                    if slot in fixed_slots:
                        continue
                    slot_to_detections[slot].append(item)

    slot_observations, uncertainties_global = _build_slot_observations(
        slot_to_detections,
        slot_mapping_method=slot_mapping_meta["method"],
        obs_source=obs_source,
        coco_untrusted=coco_untrusted,
    )
    layout_policy_meta = _apply_layout_policy(slot_observations, layout_policy)
    uncertainties_global = _unique(uncertainties_preflight + uncertainties_global)

    mismatches = _compute_mismatches(
        expected_layout,
        slot_observations,
        detection_slots=detection_slots,
    )
    _apply_mismatch_flags(slot_observations, mismatches)
    if mismatches:
        uncertainties_global = _unique(uncertainties_global + ["expected_layout_mismatch"])

    needs_human_review = bool(
        mismatches
        or uncertainties_global
        or any(item.get("needs_human_review") for item in observed_items)
        or any(obs.get("state") == "uncertain" for obs in slot_observations.values())
    )

    model_meta = (
        {
            "family": "YOLOE",
            "weights_requested": weights,
            "weights_effective": effective_weights,
            "class_prompts": prompts_eff,
            "canonical_labels": canon_eff,
        }
        if use_prompts
        else {
            "family": "YOLO",
            "weights_requested": weights,
            "weights_effective": effective_weights,
            "lab_tuned": lab_tuned,
            **(
                {}
                if lab_tuned
                else {
                    "note": "COCO-class fallback mapping; install CLIP for YOLOE text prompts or provide lab-trained weights.",
                }
            ),
        }
    )
    summary = _build_summary(
        slot_observations,
        mismatches,
        detection_slots=detection_slots,
    )

    annotated_out: str | None = None
    if annotated_path:
        try:
            import cv2

            annotated = _render_operator_overlay(
                im,
                observed_items=observed_items,
                slot_observations=slot_observations,
                slot_mapping_meta=slot_mapping_meta,
                model_meta=model_meta,
                mismatches=mismatches,
                uncertainties=uncertainties_global,
            )
            annotated_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(annotated_path), annotated)
            annotated_out = str(annotated_path.resolve())
        except Exception as exc:
            uncertainties_global = _unique(uncertainties_global + [f"annotated_image_failed:{exc}"])
            needs_human_review = True

    return {
        "mode": "deck",
        "summary": summary,
        "layout_policy": layout_policy_meta,
        "slot_mapping": slot_mapping_meta,
        "model": model_meta,
        "observed_items": observed_items,
        "slot_observations": slot_observations,
        "mismatches": mismatches,
        "uncertainties": uncertainties_global,
        "needs_human_review": needs_human_review,
        "annotated_image_path": annotated_out,
    }


def run_tiprack_stub(
    image_path: Path,
    *,
    reference_image_path: Path | None,
    weights: str,
    annotated_path: Path | None,
    use_text_prompts: bool | None,
) -> dict[str, Any]:
    prompts_eff, _, prompt_err = _resolve_yoloe_prompt_lists(None, None)
    if prompt_err is not None:
        return prompt_err

    (
        model,
        results,
        effective_weights,
        use_prompts,
        lab_tuned,
        uncertainties_preflight,
        error_result,
    ) = _run_model_predictions(
        weights=weights,
        image_path=image_path,
        use_text_prompts=use_text_prompts,
        class_prompts=prompts_eff,
    )
    if error_result is not None:
        return {"mode": "tiprack", **error_result}

    judgment = "not_confident_tiprack_view"
    reasons = list(uncertainties_preflight)
    observed_items: list[dict[str, Any]] = []
    annotated_out: str | None = None

    if not results:
        reasons.append("empty_model_output")
    else:
        r0 = results[0]
        im = r0.orig_img
        h, w = im.shape[:2]
        boxes = getattr(r0, "boxes", None)
        names = getattr(r0, "names", None) or getattr(model, "names", None)

        if boxes is not None and len(boxes):
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)
            for i in range(len(xyxy)):
                x1, y1, x2, y2 = (float(xyxy[i][j]) for j in range(4))
                conf = float(confs[i])
                cls_id = int(clss[i])
                raw_name = ""
                if isinstance(names, dict):
                    raw_name = str(names.get(cls_id, "") or "")
                elif isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
                    raw_name = str(names[cls_id] or "")
                if use_prompts:
                    label = _canonical_for_class_id(cls_id, YOLOE_CANONICAL_LABELS)
                elif lab_tuned:
                    label, _ = _label_from_lab_class_name(raw_name)
                else:
                    label, _ = _label_from_coco_name(raw_name)
                if label != "tiprack":
                    continue
                area_ratio = ((x2 - x1) * (y2 - y1)) / float(max(1, w * h))
                touches_edge = (
                    x1 <= 0.03 * w or y1 <= 0.03 * h or x2 >= 0.97 * w or y2 >= 0.97 * h
                )
                observed_items.append(
                    {
                        "detection_id": i + 1,
                        "label": label,
                        "confidence": round(conf, 4),
                        "confidence_band": _confidence_band(conf),
                        "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                        "area_ratio": round(area_ratio, 4),
                        "touches_image_edge": touches_edge,
                    }
                )

        if not observed_items:
            reasons.append("no_tiprack_detected")
        elif len(observed_items) > 1:
            judgment = "not_confident_tiprack_view"
            reasons.extend(["multiple_tipracks_detected", "use_a_tighter_crop"])
        else:
            det = observed_items[0]
            if det["confidence"] >= 0.75 and det["area_ratio"] >= 0.2 and not det["touches_image_edge"]:
                judgment = "clear_tiprack_view"
            elif det["confidence"] >= 0.45 and det["area_ratio"] >= 0.08:
                judgment = "partial_or_occluded_tiprack"
                reasons.append("tiprack_not_large_or_centered_enough")
            else:
                judgment = "not_confident_tiprack_view"
                reasons.append("tiprack_confidence_or_scale_too_low")

        if annotated_path:
            try:
                import cv2

                canvas = im.copy()
                for det in observed_items:
                    x1, y1, x2, y2 = [int(round(v)) for v in det["bbox_xyxy"]]
                    color = (0, 200, 0) if judgment == "clear_tiprack_view" else (0, 215, 255)
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(
                        canvas,
                        f"tiprack {det['confidence']:.2f}",
                        (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                        cv2.LINE_AA,
                    )
                cv2.putText(
                    canvas,
                    f"judgment={judgment}",
                    (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                annotated_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(annotated_path), canvas)
                annotated_out = str(annotated_path.resolve())
            except Exception as exc:
                reasons.append(f"annotated_image_failed:{exc}")

    needs_human_review = judgment != "clear_tiprack_view"
    reasons = _unique(reasons)
    summary_map = {
        "clear_tiprack_view": "Tiprack view is usable for a follow-up close inspection.",
        "partial_or_occluded_tiprack": "Tiprack is visible but framing or occlusion still needs human review.",
        "not_confident_tiprack_view": "Tiprack view is not reliable enough; use a tighter crop or closer image.",
    }
    return {
        "mode": "tiprack",
        "summary": summary_map[judgment],
        "judgment": judgment,
        "observed_items": observed_items,
        "slot_observations": {},
        "mismatches": [],
        "uncertainties": reasons,
        "reasons": reasons,
        "needs_human_review": needs_human_review,
        "annotated_image_path": annotated_out,
        "reference_image_path": str(reference_image_path) if reference_image_path else None,
        "image_path": str(image_path.resolve()),
        "model": {
            "family": "YOLOE" if use_prompts else "YOLO",
            "weights_requested": weights,
            "weights_effective": effective_weights,
            "lab_tuned": lab_tuned,
        },
    }


def main() -> None:
    payload = json.load(sys.stdin)
    mode = str(payload.get("mode") or "deck").lower()
    image_path = Path(payload["image_path"]).expanduser().resolve()
    if not image_path.is_file():
        print(
            json.dumps(
                {
                    "error": {"type": "FileNotFound", "detail": str(image_path)},
                    "needs_human_review": True,
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    conf = float(payload.get("conf_threshold") or 0.25)
    weights_raw = payload.get("weights")
    if weights_raw is None or (isinstance(weights_raw, str) and not str(weights_raw).strip()):
        weights = _default_weights_chain()
    else:
        weights = str(weights_raw).strip()
    use_text_prompts = payload.get("use_text_prompts")
    if use_text_prompts is not None:
        use_text_prompts = bool(use_text_prompts)
    expected_layout = payload.get("expected_layout")
    if expected_layout is not None and not isinstance(expected_layout, dict):
        expected_layout = None

    deck_corners = payload.get("deck_corners_norm")
    if deck_corners is not None and not isinstance(deck_corners, list):
        deck_corners = None

    slot_centers = payload.get("slot_centers_norm")
    if slot_centers is not None and not isinstance(slot_centers, dict):
        slot_centers = None

    load_labels_sidecar = payload.get("load_labels_sidecar")
    if load_labels_sidecar is None:
        load_labels_sidecar = True
    else:
        load_labels_sidecar = bool(load_labels_sidecar)

    class_prompts = payload.get("class_prompts")
    if class_prompts is not None and not isinstance(class_prompts, list):
        class_prompts = None
    else:
        class_prompts = [str(x) for x in class_prompts] if class_prompts else None

    canonical_labels = payload.get("canonical_labels")
    if canonical_labels is not None and not isinstance(canonical_labels, list):
        canonical_labels = None
    else:
        canonical_labels = [str(x) for x in canonical_labels] if canonical_labels else None

    ref = payload.get("reference_image_path")
    ref_path = Path(ref).expanduser().resolve() if ref else None

    out_dir = payload.get("annotated_output_dir")
    annotated_path: Path | None = None
    if out_dir:
        annotated_path = Path(out_dir).expanduser().resolve() / f"{image_path.stem}-vision-{mode}.jpg"

    if mode == "tiprack":
        result = run_tiprack_stub(
            image_path,
            reference_image_path=ref_path,
            weights=weights,
            annotated_path=annotated_path,
            use_text_prompts=use_text_prompts,
        )
    else:
        result = run_deck(
            image_path,
            weights=weights,
            conf_threshold=conf,
            expected_layout=expected_layout,
            annotated_path=annotated_path,
            use_text_prompts=use_text_prompts,
            deck_corners_norm=deck_corners,
            slot_centers_norm=slot_centers,
            load_labels_sidecar=load_labels_sidecar,
            class_prompts=class_prompts,
            canonical_labels=canonical_labels,
        )

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
