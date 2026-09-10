"""Infer well max volume (µL) from Opentrons labware name hints."""

from __future__ import annotations

import re
from typing import Any, Mapping

_ML_RE = re.compile(r"(\d+)\s*ml", re.IGNORECASE)
_UL_RE = re.compile(r"(\d+)\s*ul", re.IGNORECASE)


def infer_max_volume_ul_from_labware_name(name: str | None) -> float | None:
    """Return max well volume in µL when *name* encodes a capacity hint.

    Examples: ``nest_96_wellplate_200ul_flat`` → 200, ``nest_12_reservoir_15ml`` →
    15000. Returns ``None`` when no ``NNul`` / ``NNml`` token is present.
    """

    if not name or not str(name).strip():
        return None
    text = str(name).strip()
    ul_match = _UL_RE.search(text)
    if ul_match:
        return float(ul_match.group(1))
    ml_match = _ML_RE.search(text)
    if ml_match:
        return float(ml_match.group(1)) * 1000.0
    return None


def infer_max_volume_ul_from_labware_record(record: Mapping[str, Any]) -> float | None:
    """Infer capacity from ``loadName``, ``definitionUri``, or ``displayName``."""

    for key in ("loadName", "definitionUri", "displayName"):
        raw = record.get(key)
        if raw is None:
            continue
        inferred = infer_max_volume_ul_from_labware_name(str(raw))
        if inferred is not None:
            return inferred
    return None


def labware_max_ul_from_analyze_labware(
    labware: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
) -> dict[str, float]:
    """Map analyze ``labware[]`` ids to inferred per-well max µL."""

    out: dict[str, float] = {}
    for item in labware:
        if not isinstance(item, Mapping):
            continue
        labware_id = item.get("id")
        if labware_id is None:
            continue
        max_ul = infer_max_volume_ul_from_labware_record(item)
        if max_ul is not None:
            out[str(labware_id)] = max_ul
    return out
