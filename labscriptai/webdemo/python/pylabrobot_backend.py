"""Software-only PyLabRobot helpers ported from the main-wizard Tecan sim path.

Maps display names (Tecan Freedom EVO, Hamilton Vantage) onto stable ids so a
Tecan label never silently becomes a Hamilton deck. Volume gates reject transfers
above robot / tip limits because Chatterbox does not model spill.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_ROBOT_MODEL_RE = re.compile(r"robot_model\s*[:=]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
LH_PRIMS = frozenset({"ASPIRATE", "DISPENSE", "MIX"})

ROBOT_MAX_UL = {
    "tecan_evo": 1000.0,
    "tecan_fluent": 1000.0,
    "hamilton_star": 1000.0,
    "hamilton_vantage": 1000.0,
    "ot2": 300.0,
    "flex": 1000.0,
}

TIP_MAX_UL = {
    "tecan_evo": 200.0,
    "tecan_fluent": 200.0,
    "hamilton_star": 300.0,
    "hamilton_vantage": 300.0,
    "ot2": 300.0,
    "flex": 1000.0,
}


def normalize_robot_model(raw: Optional[str]) -> str:
    """Map UI labels like 'Tecan Freedom EVO' onto profile ids like tecan_evo."""
    slug = re.sub(r"[^a-z0-9]+", "_", (raw or "").strip().strip("'\"").lower()).strip("_")
    if not slug:
        return ""
    if "fluent" in slug or slug == "tecan":
        return "tecan_fluent"
    if "tecan" in slug or "freedom_evo" in slug:
        return "tecan_evo"
    if "vantage" in slug:
        return "hamilton_vantage"
    if "hamilton" in slug or slug in {"star", "starlet"}:
        return "hamilton_star"
    if slug in {"ot2", "ot_2", "ot-2"} or "ot2" in slug:
        return "ot2"
    if "flex" in slug or "opentrons" in slug:
        return "flex" if "flex" in slug else "ot2"
    aliases = {
        "tecan_evo": "tecan_evo",
        "tecan_fluent": "tecan_fluent",
        "hamilton_star": "hamilton_star",
        "hamilton_vantage": "hamilton_vantage",
        "ot2": "ot2",
        "flex": "flex",
    }
    return aliases.get(slug, slug)


def robot_model_from_yaml(text: str) -> str:
    match = _ROBOT_MODEL_RE.search(text or "")
    if not match:
        return ""
    return normalize_robot_model(match.group(1).split("#", 1)[0])


def _step_volumes(plan: dict[str, Any]) -> list[float]:
    volumes: list[float] = []
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list):
        return volumes
    for raw in steps:
        if not isinstance(raw, dict):
            continue
        prim = str(raw.get("primitive_type") or raw.get("type") or "").strip().upper().replace("-", "_")
        if prim not in LH_PRIMS:
            continue
        try:
            volumes.append(float(raw["volume_ul"]))
        except (KeyError, TypeError, ValueError):
            continue
    return volumes


def plan_volume_error(plan: dict[str, Any], robot: str | None = None) -> Optional[str]:
    """Reject Plan IR transfers above robot or assumed-tip capacity."""
    volumes = _step_volumes(plan)
    if not volumes:
        return None
    max_vol = max(volumes)
    model = normalize_robot_model(robot)
    robot_max = ROBOT_MAX_UL.get(model)
    if robot_max is not None and max_vol > robot_max:
        return f"Volume {max_vol:g} µL exceeds the robot max of {robot_max:g} µL"
    tip_max = TIP_MAX_UL.get(model)
    if tip_max is not None and max_vol > tip_max:
        return f"Volume {max_vol:g} µL exceeds tip capacity {tip_max:g} µL"
    return None
