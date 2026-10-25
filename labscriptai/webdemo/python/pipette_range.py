"""Gate Analyze liquid moves using installed official pipette data and mode.

No volume/hardware correction is performed. Unknown data stays unevaluable.
This software check does not establish accuracy, calibration or liquid behavior.
"""
from __future__ import annotations

import math
from typing import Any


def official_ranges(name: str) -> dict[str, tuple[float, float]]:
    from opentrons_shared_data.pipette import name_config
    from opentrons_shared_data.pipette.types import PIPETTE_API_NAMES_MAP
    canonical = PIPETTE_API_NAMES_MAP.get(name, name)
    canonical = getattr(canonical, "value", canonical)
    spec = name_config()[canonical]  # Unknown names fail closed.
    if canonical.endswith("_flex"):
        from opentrons_shared_data.pipette.load_data import load_definition
        from opentrons_shared_data.pipette.pipette_load_name_conversions import convert_pipette_name
        model = convert_pipette_name(canonical)
        definition = load_definition(model.pipette_type, model.pipette_channels, model.pipette_version, model.oem_type)
        return {key.name: (value.min_volume, value.max_volume)
                for key, value in definition.liquid_properties.items()}
    return {"default": (float(spec["minVolume"]), float(spec["maxVolume"]))}


def evaluate_pipette_ranges(analyze: dict[str, Any]) -> dict[str, Any]:
    pipettes = {p.get("id"): p.get("pipetteName") for p in analyze.get("pipettes", []) if isinstance(p, dict)}
    modes: dict[str, str | None] = {}
    ranges: dict[str, dict[str, tuple[float, float]]] = {}
    issues: list[dict[str, Any]] = []
    checked = 0
    commands = analyze.get("commands")
    if not isinstance(commands, list):
        return {"outcome": "unevaluable", "issues": [], "reason": "missing_commands"}

    def issue(index: int, detail: str, unknown: bool = False) -> None:
        issues.append({"code": "LP-PIPETTE-UNKNOWN" if unknown else "LP-PIPETTE-RANGE",
                       "step_index": index, "detail_text": detail,
                       "severity": "terminal" if unknown else "error"})

    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            issue(index, "Cannot verify a malformed command.", True)
            continue
        kind = command.get("commandType")
        if kind not in {"aspirate", "dispense", "mix", "configureForVolume"}:
            continue
        params = command.get("params") or {}
        volume = params.get("volume")
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not math.isfinite(volume):
            issue(index, "Cannot verify a missing or non-finite liquid volume.", True)
            continue
        if volume < 0:
            issue(index, f"Negative liquid volume {volume:g} µL is invalid.")
            continue
        if volume == 0 and kind != "configureForVolume":
            continue
        pid = params.get("pipetteId")
        name = pipettes.get(pid)
        try:
            if not name:
                raise ValueError("missing pipette")
            if name not in ranges:
                ranges[name] = official_ranges(name)
            available = ranges[name]
            mode = modes.get(pid, "default")
            if kind == "configureForVolume":
                mode = "lowVolumeDefault" if volume < available["default"][0] and "lowVolumeDefault" in available else "default"
                modes[pid] = mode
                continue
            if mode is None:
                raise ValueError("unverified volume configuration")
            minimum, maximum = available[mode]
        except Exception as exc:
            if kind == "configureForVolume":
                modes[pid] = None
            issue(index, f"Cannot verify {name or pid or 'unnamed pipette'} working range ({type(exc).__name__}); do not treat this as passed.", True)
            continue
        checked += 1
        if not minimum <= volume <= maximum:
            issue(index, f"{kind} {volume:g} µL with {name} is outside its official {mode} working range {minimum:g}–{maximum:g} µL. A compatible pipette/mode requires hardware confirmation; do not change the requested volume.")
    outcome = "fail" if any(i["severity"] == "error" for i in issues) else "unevaluable" if issues else "pass"
    return {"outcome": outcome, "issues": issues, "checked_moves": checked,
            "reason": "pipette_range_unverified" if outcome == "unevaluable" else None}
