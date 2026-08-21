#!/usr/bin/env python3
"""
Post-hoc pressure-trace feature extraction (advisory / observation-only).

Supports canonical LabscriptAI / DNA pressure CSV columns:
  site, well, phase, step_index, z_offset_from_top_mm,
  pressure_pa, capacitance_pf, elapsed_ms

Also accepts legacy two-column CSVs: t_ms,pressure_pa.

Contract: stdin JSON → stdout JSON. Always observation_only / no resume authority.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any


CANONICAL_FIELDS = [
    "site",
    "well",
    "phase",
    "step_index",
    "z_offset_from_top_mm",
    "pressure_pa",
    "capacitance_pf",
    "elapsed_ms",
]


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("samples"), list) and payload["samples"]:
        return [row for row in payload["samples"] if isinstance(row, dict)]

    text = payload.get("csv_text")
    if not text and payload.get("csv_path"):
        path = Path(str(payload["csv_path"])).expanduser().resolve()
        text = path.read_text(encoding="utf-8")
    if not text:
        return []

    reader = csv.DictReader(io.StringIO(str(text)))
    fieldnames = [f.strip() for f in (reader.fieldnames or [])]
    rows: list[dict[str, Any]] = []

    # Legacy: t_ms,pressure_pa without header names matching DictReader fields
    if not fieldnames or (
        len(fieldnames) >= 2
        and fieldnames[0].lower() == "t_ms"
        and "pressure_pa" in fieldnames[1].lower()
        and "phase" not in [f.lower() for f in fieldnames]
    ):
        # Re-parse as simple two-column
        for line in str(text).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.lower().startswith("t_ms"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            t_ms = _as_float(parts[0])
            pressure = _as_float(parts[1])
            if t_ms is None or pressure is None:
                continue
            rows.append(
                {
                    "elapsed_ms": t_ms,
                    "pressure_pa": pressure,
                    "phase": "legacy",
                    "step_index": len(rows),
                    "z_offset_from_top_mm": None,
                    "site": None,
                    "well": None,
                    "capacitance_pf": None,
                }
            )
        return rows

    for raw in reader:
        pressure = _as_float(raw.get("pressure_pa"))
        if pressure is None:
            continue
        rows.append(
            {
                "site": raw.get("site") or None,
                "well": raw.get("well") or None,
                "phase": raw.get("phase") or "unknown",
                "step_index": _as_float(raw.get("step_index")),
                "z_offset_from_top_mm": _as_float(raw.get("z_offset_from_top_mm")),
                "pressure_pa": pressure,
                "capacitance_pf": _as_float(raw.get("capacitance_pf")),
                "elapsed_ms": _as_float(raw.get("elapsed_ms")),
            }
        )
    return rows


def _moving_average(values: list[float], window: int) -> list[float]:
    if window <= 1 or not values:
        return list(values)
    w = min(window, len(values))
    out: list[float] = []
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= w:
            acc -= values[i - w]
            out.append(acc / w)
        else:
            out.append(acc / (i + 1))
    return out


def _phase_slice(rows: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [r for r in rows if str(r.get("phase") or "") == phase]


def _series_features(rows: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    usable = [r for r in rows if r.get("pressure_pa") is not None]
    if not usable:
        return None
    pressures = [float(r["pressure_pa"]) for r in usable]
    times = [float(r["elapsed_ms"]) if r.get("elapsed_ms") is not None else float(i) for i, r in enumerate(usable)]
    zs = [r.get("z_offset_from_top_mm") for r in usable]
    n = len(pressures)
    mean_p = sum(pressures) / n
    min_p = min(pressures)
    max_p = max(pressures)
    peak_idx = pressures.index(max_p)

    deltas = [abs(pressures[i] - pressures[i - 1]) for i in range(1, n)]
    median_delta = sorted(deltas)[len(deltas) // 2] if deltas else 0.0
    threshold = max(median_delta * 3.0, (max_p - min_p) * 0.05, 1.0)
    contact_idx = None
    for i, d in enumerate(deltas, start=1):
        if d >= threshold:
            contact_idx = i
            break

    contact = None
    if contact_idx is not None:
        contact = {
            "elapsed_ms": times[contact_idx],
            "pressure_pa": pressures[contact_idx],
            "z_offset_from_top_mm": zs[contact_idx],
            "index": contact_idx,
            "phase": usable[contact_idx].get("phase"),
        }

    return {
        "label": label,
        "sample_count": n,
        "mean_pressure_pa": mean_p,
        "min_pressure_pa": min_p,
        "max_pressure_pa": max_p,
        "duration_ms": (times[-1] - times[0]) if n > 1 else 0.0,
        "peak": {
            "elapsed_ms": times[peak_idx],
            "pressure_pa": max_p,
            "z_offset_from_top_mm": zs[peak_idx],
            "index": peak_idx,
        },
        "contact_point": contact,
        "first_z_mm": zs[0],
        "last_z_mm": zs[-1],
    }


def _extract_features(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    if not rows:
        return (
            {
                "sample_count": 0,
                "phases": {},
                "contact_point": None,
                "peak": None,
            },
            "low",
        )

    # Optional smoothing on pressure only
    pressures = [float(r["pressure_pa"]) for r in rows]
    # caller may already smooth; keep raw here

    overall = _series_features(rows, "all")
    phases = sorted({str(r.get("phase") or "unknown") for r in rows})
    by_phase = {}
    for phase in phases:
        feat = _series_features(_phase_slice(rows, phase), phase)
        if feat:
            by_phase[phase] = feat

    # Prefer collision_z / during_probe for contact heuristics
    preferred = None
    for key in ("collision_z", "during_probe", "after_probe", "deck_hover", "legacy"):
        if key in by_phase:
            preferred = by_phase[key]
            break
    if preferred is None:
        preferred = overall

    features = {
        "sample_count": len(rows),
        "wells": sorted({str(r.get("well")) for r in rows if r.get("well")}),
        "sites": sorted({str(r.get("site")) for r in rows if r.get("site")}),
        "phases": by_phase,
        "overall": overall,
        "contact_point": (preferred or {}).get("contact_point"),
        "peak": (preferred or {}).get("peak"),
        "units": {"pressure": "Pa", "z": "mm", "t": "ms"},
        "schema": "canonical_v1",
        "raw_pressure_mean_pa": sum(pressures) / len(pressures),
    }

    n = len(rows)
    if n >= 20 and features.get("contact_point"):
        band = "medium"
    elif n >= 8:
        band = "low"
    else:
        band = "low"
    return features, band


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        json.dump(
            {
                "summary": f"invalid stdin JSON: {exc}",
                "observation_only": True,
                "advisory": True,
                "resume_authority": False,
                "advisory_features": {},
                "confidence_band": "low",
                "needs_human_review": True,
            },
            sys.stdout,
        )
        sys.exit(1)

    if not isinstance(payload, dict):
        json.dump(
            {
                "summary": "stdin JSON must be an object",
                "observation_only": True,
                "advisory": True,
                "resume_authority": False,
                "advisory_features": {},
                "confidence_band": "low",
                "needs_human_review": True,
            },
            sys.stdout,
        )
        sys.exit(1)

    try:
        rows = _load_rows(payload)
    except OSError as exc:
        json.dump(
            {
                "summary": f"failed to read csv: {exc}",
                "observation_only": True,
                "advisory": True,
                "resume_authority": False,
                "advisory_features": {},
                "confidence_band": "low",
                "needs_human_review": True,
            },
            sys.stdout,
        )
        sys.exit(1)

    window = int(payload.get("moving_average_window") or 5)
    if window > 1 and rows:
        pressures = [float(r["pressure_pa"]) for r in rows]
        smoothed = _moving_average(pressures, window)
        for i, r in enumerate(rows):
            r = dict(r)
            r["pressure_pa"] = smoothed[i]
            rows[i] = r

    features, band = _extract_features(rows)
    result = {
        "summary": (
            f"Advisory pressure features from {features.get('sample_count', 0)} sample(s); "
            "observation-only, cannot override controller or Gatekeeper."
        ),
        "observation_only": True,
        "advisory": True,
        "resume_authority": False,
        "advisory_features": features,
        "confidence_band": band,
        "needs_human_review": features.get("sample_count", 0) < 8,
        "filter": {"moving_average_window": window},
        "canonical_fields": CANONICAL_FIELDS,
    }
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
