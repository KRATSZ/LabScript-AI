"""Build a fake-robot command script from local Flex protocol source."""

from __future__ import annotations

import re
from typing import Any


SLOT = {"tip_rack": "B2", "reservoir": "C2", "plate": "D2"}


def _bootstrap() -> list[dict[str, Any]]:
    return [
        {"commandType": "home"},
        {
            "commandType": "loadLabware",
            "params": {
                "location": {"slotName": "B2"},
                "loadName": "opentrons_flex_96_tiprack_1000ul",
                "namespace": "opentrons",
                "version": 1,
            },
        },
        {
            "commandType": "loadLabware",
            "params": {
                "location": {"slotName": "C2"},
                "loadName": "nest_12_reservoir_15ml",
                "namespace": "opentrons",
                "version": 1,
            },
        },
        {
            "commandType": "loadLabware",
            "params": {
                "location": {"slotName": "D2"},
                "loadName": "nest_96_wellplate_200ul_flat",
                "namespace": "opentrons",
                "version": 1,
            },
        },
        {
            "commandType": "loadPipette",
            "params": {"pipetteName": "p1000_single_flex", "mount": "left"},
        },
    ]


def _parse_aliases(source: str) -> dict[str, tuple[str, str]]:
    aliases: dict[str, tuple[str, str]] = {}
    for m in re.finditer(
        r"""(?P<var>\w+)\s*=\s*(?P<lw>reservoir|plate|tip_rack)\s*\[\s*["'](?P<well>[A-H]\d+)["']\s*\]""",
        source,
    ):
        aliases[m.group("var")] = (SLOT[m.group("lw")], m.group("well"))

    # primary = reservoir[primary_well] with default primary_well="A1"
    if re.search(r"""\bprimary\s*=\s*reservoir\s*\[\s*primary_well\s*\]""", source):
        aliases["primary"] = ("C2", "A1")

    for m in re.finditer(
        r"""(?P<var>\w+)\s*=\s*\[(?P<body>[^\]]+)\]""",
        source,
    ):
        wells = re.findall(r"""plate\s*\[\s*["']([A-H]\d+)["']\s*\]""", m.group("body"))
        if not wells:
            continue
        aliases[m.group("var")] = ("D2", wells[0])
        for idx, well in enumerate(wells):
            aliases[f"{m.group('var')}[{idx}]"] = ("D2", well)
        aliases[f"__list__{m.group('var')}"] = wells  # type: ignore[assignment]
    return aliases


def _resolve(name: str, aliases: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    name = name.strip()
    if name in aliases and not name.startswith("__list__"):
        val = aliases[name]
        if isinstance(val, tuple):
            return val
    m = re.fullmatch(r"""(reservoir|plate)\s*\[\s*["']([A-H]\d+)["']\s*\]""", name)
    if m:
        return SLOT[m.group(1)], m.group(2)
    # additive.bottom(2) / sample.bottom(2)
    m = re.fullmatch(r"""(\w+)\.bottom\s*\(""", name)
    if m and m.group(1) in aliases:
        return aliases[m.group(1)]  # type: ignore[return-value]
    m = re.fullmatch(r"""(\w+)\.bottom\s*\(\s*\d+\s*\)""", name)
    if m and m.group(1) in aliases:
        return aliases[m.group(1)]  # type: ignore[return-value]
    return None


def _list_wells(name: str, aliases: dict) -> list[str]:
    key = f"__list__{name}"
    wells = aliases.get(key)
    return list(wells) if isinstance(wells, list) else []


def _run_body_lines(source: str) -> list[str]:
    """Return only lines inside ``def run(...)`` so helpers like finish_tip are ignored."""
    lines = source.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(r"def\s+run\s*\(", line):
            start = idx + 1
            break
    if start is None:
        return lines
    body: list[str] = []
    for line in lines[start:]:
        if line and not line[0].isspace() and not line.startswith("#"):
            # Next top-level def/class/assignment ends the run body.
            break
        body.append(line)
    return body


def build_script_from_protocol(source: str) -> list[dict[str, Any]]:
    aliases = _parse_aliases(source)
    script = _bootstrap()
    tip_wells = [f"{c}{r}" for r in range(1, 13) for c in "ABCDEFGH"]
    tip_idx = 0
    lines = _run_body_lines(source)
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        cm = re.search(r"""protocol\.comment\(\s*f?["'](.+?)["']""", stripped)
        if not cm:
            cm = re.search(r"""protocol\.comment\(\s*f?["'](.+?)["']""", "\n".join(lines[i : i + 3]))
        if cm and "protocol.comment" in stripped:
            script.append({"commandType": "comment", "params": {"message": cm.group(1)[:160]}})
            i += 1
            continue

        if "protocol.capture_image" in stripped:
            script.append({"commandType": "comment", "params": {"message": "capture_image"}})
            i += 1
            continue

        if re.search(r"""pipette\.pick_up_tip\s*\(""", stripped):
            # Leave well selection to the engine (matches OT tiprack next-tip behavior).
            tip_idx += 1
            script.append(
                {
                    "commandType": "pickUpTip",
                    "params": {"wellName": "auto", "slotName": "B2"},
                }
            )
            i += 1
            continue

        pm = re.search(
            r"""pipette\.require_liquid_presence\(\s*(?P<src>[\w\[\]"'\.]+)\s*\)""",
            stripped,
        )
        if pm:
            resolved = _resolve(pm.group("src"), aliases)
            if resolved:
                slot, well = resolved
                script.append(
                    {"commandType": "liquidProbe", "params": {"wellName": well, "slotName": slot}}
                )
            i += 1
            continue

        # aspirate(vol, location) / dispense(vol, location)
        am = re.search(
            r"""pipette\.(?P<op>aspirate|dispense)\(\s*(?P<vol>\d+)\s*,\s*(?P<loc>[\w\.]+(?:\([^)]*\))?)\s*\)""",
            stripped,
        )
        if am:
            resolved = _resolve(am.group("loc"), aliases)
            if resolved:
                slot, well = resolved
                ctype = "aspirate" if am.group("op") == "aspirate" else "dispense"
                script.append(
                    {
                        "commandType": ctype,
                        "params": {"wellName": well, "slotName": slot, "volume": int(am.group("vol"))},
                    }
                )
            i += 1
            continue

        if "transfer_with_liquid_class" in stripped or (
            i + 1 < len(lines) and "transfer_with_liquid_class" in lines[i + 1]
        ):
            block = "\n".join(lines[i : i + 10])
            tm = re.search(
                r"""volume\s*=\s*(?P<vol>\d+)[\s\S]*?source\s*=\s*(?P<source>\w+)[\s\S]*?dest\s*=\s*(?P<dest>\w+)""",
                block,
            )
            if tm:
                vol = int(tm.group("vol"))
                src = _resolve(tm.group("source"), aliases)
                dest_name = tm.group("dest")
                dest = _resolve(dest_name, aliases)
                window = "\n".join(lines[max(0, i - 10) : i + 1])
                fm = re.search(r"""for\s+(\w+)\s+in\s+(\w+)\s*:""", window)
                list_wells: list[str] = []
                if fm and fm.group(1) == dest_name:
                    list_wells = _list_wells(fm.group(2), aliases)
                if src and list_wells:
                    for well in list_wells:
                        script.append(
                            {
                                "commandType": "aspirate",
                                "params": {
                                    "wellName": src[1],
                                    "slotName": src[0],
                                    "volume": vol,
                                },
                            }
                        )
                        script.append(
                            {
                                "commandType": "dispense",
                                "params": {"wellName": well, "slotName": "D2", "volume": vol},
                            }
                        )
                elif src and dest:
                    script.append(
                        {
                            "commandType": "aspirate",
                            "params": {
                                "wellName": src[1],
                                "slotName": src[0],
                                "volume": vol,
                            },
                        }
                    )
                    script.append(
                        {
                            "commandType": "dispense",
                            "params": {
                                "wellName": dest[1],
                                "slotName": dest[0],
                                "volume": vol,
                            },
                        }
                    )
                while i < len(lines) and ")" not in lines[i]:
                    i += 1
                i += 1
                continue

        if re.search(r"""finish_tip\s*\(|pipette\.drop_tip\s*\(""", stripped):
            script.append({"commandType": "dropTip", "params": {"slotName": "A3"}})
            i += 1
            continue

        i += 1

    return script


def inject_scenario_failures(
    script: list[dict[str, Any]],
    scenario_id: str,
) -> list[dict[str, Any]]:
    from .scenarios import (
        _liquid_not_found_error,
        _tip_clog_error,
        _tip_error,
        _tip_not_attached_fail_run,
    )

    out = [dict(step, params=dict(step.get("params") or {})) for step in script]
    if scenario_id in {
        "tip_missing_budget_block",
        "tip_missing_recoverable",
        "tip_false_missing_already_attached",
    }:
        for step in out:
            if step.get("commandType") == "pickUpTip":
                # Force A1 so auto tip selection cannot skip the missing well.
                step.setdefault("params", {})["wellName"] = "A1"
                step["inject_error"] = _tip_error("A1")
                break
    elif scenario_id in {
        "liquid_not_found_with_reserve",
        "liquid_not_found_no_reserve",
        "liquid_reserve_volume_short",
    }:
        for step in out:
            params = step.get("params") or {}
            if (
                step.get("commandType") == "liquidProbe"
                and params.get("slotName") == "C2"
                and params.get("wellName") == "A1"
            ):
                step["inject_error"] = _liquid_not_found_error()
                break
        else:
            for step in out:
                if step.get("commandType") == "liquidProbe":
                    step["inject_error"] = _liquid_not_found_error()
                    break
    elif scenario_id == "tip_clog_on_waste_dispense":
        for step in out:
            params = step.get("params") or {}
            if step.get("commandType") == "dispense" and params.get("wellName") == "H12":
                step["inject_error"] = _tip_clog_error()
                break
        else:
            # Fallback: last dispense in script
            for step in reversed(out):
                if step.get("commandType") == "dispense":
                    step["inject_error"] = _tip_clog_error()
                    break
    elif scenario_id == "tip_clog_on_precious_aliquot":
        aspirate_a4 = 0
        for step in out:
            params = step.get("params") or {}
            if (
                step.get("commandType") == "aspirate"
                and params.get("slotName") == "C2"
                and params.get("wellName") == "A4"
            ):
                aspirate_a4 += 1
                if aspirate_a4 >= 2:
                    step["inject_error"] = _tip_clog_error()
                    break
    elif scenario_id == "pause_after_sample_probe":
        filtered: list[dict[str, Any]] = []
        for step in out:
            filtered.append(step)
            params = step.get("params") or {}
            if (
                step.get("commandType") == "liquidProbe"
                and params.get("slotName") == "D2"
                and params.get("wellName") == "A1"
            ):
                filtered.append({"commandType": "_pause", "params": {"reason": "sample_tip_hold"}})
                return filtered
        # If no D2 probe found, pause at end with tip still attached (drop tips removed).
        filtered = [s for s in out if s.get("commandType") not in {"dropTip", "dropTipInPlace"}]
        filtered.append({"commandType": "_pause", "params": {"reason": "sample_tip_hold"}})
        return filtered
    elif scenario_id == "pause_after_phase1":
        # Hold after first tip cycle completes (dropTip #1), before Phase 2 pickup.
        drop_count = 0
        filtered = []
        for step in out:
            filtered.append(step)
            if step.get("commandType") in {"dropTip", "dropTipInPlace"}:
                drop_count += 1
                if drop_count >= 1:
                    filtered.append({"commandType": "_pause", "params": {"reason": "phase1_hold"}})
                    return filtered
        filtered.append({"commandType": "_pause", "params": {"reason": "phase1_hold"}})
        return filtered
    elif scenario_id == "tip_not_attached_fail_run":
        filtered = []
        saw_probe = False
        for step in out:
            if step.get("commandType") == "pickUpTip" and not saw_probe:
                continue
            if step.get("commandType") == "liquidProbe" and not saw_probe:
                step = dict(step)
                step["inject_error"] = _tip_not_attached_fail_run()
                step["force_no_tip"] = True
                saw_probe = True
            filtered.append(step)
        return filtered
    return out
