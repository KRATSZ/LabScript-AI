#!/usr/bin/env python3
"""Plan IR → runnable PyLabRobot script (Hamilton Vantage). stdin JSON → stdout JSON."""

from __future__ import annotations

import json
import re
import sys
import traceback
from typing import Any

PLAN_SCHEMA_ID = "bpl.plan_ir.lh.v0"
LH = frozenset({"ASPIRATE", "DISPENSE", "MIX", "PICK_TIPS", "DROP_TIPS", "WAIT"})
STRIDE = 11
FACTORY = {
    "tiprack": ("hamilton_96_tiprack_300uL_filter", "hamilton"),
    "plate": ("Cor_96_wellplate_360ul_Fb", "resources"),
    "reservoir": ("nest_12_troughplate_15000uL_Vb", "resources"),
}


class CompileError(Exception):
    def __init__(self, stage: str, error: str, hint: str) -> None:
        super().__init__(error)
        self.stage, self.error, self.hint = stage, error, hint


def fail(stage: str, error: str, hint: str) -> dict[str, Any]:
    return {"ok": False, "stage": stage, "error": error, "hint": hint}


def fmt(n: float) -> str:
    return str(int(n)) if float(n) == int(n) else str(n)


def prim(raw: Any) -> str:
    return str(raw or "").strip().upper().replace("-", "_")



def parse_locs(value: Any, *, field: str, n: int) -> list[tuple[str, str]]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out: list[tuple[str, str]] = []
        for item in value:
            out.extend(parse_locs(item, field=field, n=n))
        return out
    out: list[tuple[str, str]] = []
    for part in [p.strip() for p in str(value).split(",") if p.strip()]:
        bits = part.split(":", 1)
        if len(bits) != 2 or not bits[0].strip() or not bits[1].strip():
            raise CompileError("mapping", f"Step {n} {field} {part!r} must look like plate:A1.", "Use resource_id:WELL (example: plate:A1).")
        out.append((bits[0].strip(), bits[1].strip().upper()))
    return out


def well_token(raw: Any) -> str:
    text = str(raw or "").strip()
    return (text.split(":", 1)[1] if ":" in text else text).strip().upper()


def py_name(raw: str, used: set[str]) -> str:
    name = re.sub(r"[^0-9A-Za-z_]", "_", (raw or "").strip()) or "res"
    if name[0].isdigit():
        name = "r_" + name
    base, i = name, 2
    while name in used:
        name = f"{base}_{i}"
        i += 1
    used.add(name)
    return name


def slot_key(slot: Any) -> tuple[int, int]:
    try:
        return (0, int(str(slot).strip()))
    except (TypeError, ValueError):
        return (1, 10**9)


class HamiltonCompiler:
    def __init__(self, plan: dict[str, Any], family: str = "vantage") -> None:
        self.plan = plan
        self.family = family if family in {"star", "vantage"} else "vantage"
        self.warnings: list[str] = []
        self.resources: dict[str, dict[str, Any]] = {}
        self.tipracks: dict[str, dict[str, Any]] = {}
        self.var_of: dict[str, str] = {}
        self.command_count = 0
        self.tips_on = 0

    def compile(self) -> dict[str, Any]:
        self._parse_resources()
        steps = self.plan.get("steps")
        if not isinstance(steps, list) or not steps:
            raise CompileError("mapping", "Plan has no steps — nothing to compile.", "Add at least PICK_TIPS → ASPIRATE → DISPENSE → DROP_TIPS.")
        body: list[str] = []
        for i, raw in enumerate(steps, start=1):
            if not isinstance(raw, dict):
                raise CompileError("mapping", f"Step {i} must be an object.", "Each steps[] entry needs primitive_type and the fields for that primitive.")
            p = prim(raw.get("primitive_type") or raw.get("type"))
            if p not in LH:
                raise CompileError("mapping", f"Step {i} has unknown primitive_type {p or '(missing)'!r}.", f"LH subset is {', '.join(sorted(LH))}.")
            body.extend(self._step(i, p, raw))
        return {"ok": True, "script": self._render(body), "command_count": self.command_count, "warnings": self.warnings}

    def _parse_resources(self) -> None:
        raw_list = self.plan.get("resources")
        if not isinstance(raw_list, list) or not raw_list:
            raise CompileError("mapping", "Plan has no resources.", "Add a tiprack plus a plate or reservoir in resources[].")
        used = {"deck", "lh", "backend", "trash"}
        for item in raw_list:
            if not isinstance(item, dict):
                raise CompileError("mapping", "Each resource must be an object with id and type.", 'Example: {"id": "plate", "type": "plate", "slot": "2"}.')
            rid = str(item.get("id") or "").strip()
            rtype = str(item.get("type") or "").strip().lower()
            if not rid:
                raise CompileError("mapping", "A resource is missing id.", "Give every resource a stable id (the left side of plate:A1).")
            factory = FACTORY.get(rtype)
            if factory is None:
                self.warnings.append(f"Resource {rid!r} has unknown type {rtype!r}; mapped to Cor_96_wellplate_360ul_Fb (conservative).")
                factory = FACTORY["plate"]
            rec = {**item, "id": rid, "type": rtype, "factory": factory}
            self.resources[rid] = rec
            self.var_of[rid] = py_name(rid, used)
            if rtype == "tiprack":
                self.tipracks[rid] = rec
        occupied: list[int] = []
        for _i, rec in sorted(enumerate(self.resources.values()), key=lambda p: (slot_key(p[1].get("slot")), p[0])):
            rails = 1
            while any(abs(rails - u) < STRIDE for u in occupied):
                rails += STRIDE
            occupied.append(rails)
            rec["rails"] = rails

    def _need(self, rid: str, n: int, action: str) -> dict[str, Any]:
        rec = self.resources.get(rid)
        if rec is None:
            raise CompileError("mapping", f"Step {n} {action} '{rid}', which is not in resources.", f"Add a resource with id '{rid}', or point the step at a declared plate.")
        return rec

    def _vol(self, raw: dict[str, Any], n: int, p: str) -> float:
        if raw.get("volume_ul") is None:
            raise CompileError("mapping", f"Step {n} {p} needs volume_ul.", "Set volume_ul to a number greater than 0.")
        try:
            volume = float(raw["volume_ul"])
        except (TypeError, ValueError) as exc:
            raise CompileError("mapping", f"Step {n} volume_ul must be a number.", 'Example: "volume_ul": 50.') from exc
        if volume <= 0:
            raise CompileError("mapping", f"Step {n} volume_ul must be > 0.", "Use a positive microlitre volume.")
        return volume

    def _spots(self, locs: list[tuple[str, str]], n: int, action: str) -> str:
        return " + ".join(f"{self.var_of[self._need(rid, n, action)['id']]}[{well!r}]" for rid, well in locs)

    def _vols(self, volume: float, n: int) -> str:
        return "[" + ", ".join([fmt(volume)] * n) + "]"

    def _step(self, n: int, p: str, raw: dict[str, Any]) -> list[str]:
        if p == "PICK_TIPS":
            return self._pick(n, raw)
        if p == "DROP_TIPS":
            if raw.get("to_waste") is False:
                trash = "STAR" if self.family == "star" else "Vantage"
                self.warnings.append(f"Step {n} DROP_TIPS to_waste=false; script still drops to {trash} trash.")
            self.command_count += 1
            n_tips = max(1, self.tips_on)
            self.tips_on = 0
            return [f"    await lh.drop_tips([deck.get_trash_area()] * {n_tips}, allow_nonzero_volume=True)"]
        if p == "WAIT":
            if raw.get("duration_s") is None:
                raise CompileError("mapping", f"Step {n} WAIT needs duration_s.", 'Example: "duration_s": 2.')
            try:
                seconds = float(raw["duration_s"])
            except (TypeError, ValueError) as exc:
                raise CompileError("mapping", f"Step {n} duration_s must be a number.", 'Example: "duration_s": 2.') from exc
            if seconds < 0:
                raise CompileError("mapping", f"Step {n} duration_s must be ≥ 0.", "Use a non-negative wait in seconds.")
            self.command_count += 1
            return [f"    await asyncio.sleep({fmt(seconds)})"]
        if p in {"ASPIRATE", "DISPENSE"}:
            field = "source" if p == "ASPIRATE" else "destination"
            action = "aspirates from" if p == "ASPIRATE" else "dispenses into"
            method = p.lower()
            locs = parse_locs(raw.get(field), field=field, n=n)
            if not locs:
                raise CompileError("mapping", f"Step {n} {p} needs {field} like plate:A1.", f'Set "{field}" to a declared resource well.')
            volume = self._vol(raw, n, p)
            self.command_count += 1
            return [f"    await lh.{method}({self._spots(locs, n, action)}, vols={self._vols(volume, len(locs))})"]
        locs = parse_locs(raw.get("location") or raw.get("source") or raw.get("destination"), field="location", n=n)
        if not locs:
            raise CompileError("mapping", f"Step {n} MIX needs location like plate:A1.", 'Set "location" to the well being mixed.')
        volume = self._vol(raw, n, "MIX")
        try:
            cycles = max(1, int(raw.get("cycles") or 3))
        except (TypeError, ValueError):
            cycles = 3
        spots, vols = self._spots(locs, n, "mixes"), self._vols(volume, len(locs))
        self.command_count += 2 * cycles
        return [f"    for _ in range({cycles}):", f"        await lh.aspirate({spots}, vols={vols})", f"        await lh.dispense({spots}, vols={vols})"]

    def _pick(self, n: int, raw: dict[str, Any]) -> list[str]:
        positions_raw = raw.get("tip_positions") or ()
        if isinstance(positions_raw, str):
            positions = [positions_raw]
        elif isinstance(positions_raw, (list, tuple)):
            positions = list(positions_raw)
        else:
            raise CompileError("mapping", f"Step {n} PICK_TIPS tip_positions must be a list.", 'Example: "tip_positions": ["A1"].')
        wells = [well_token(x) for x in positions if str(x).strip()]
        if not wells:
            raise CompileError("mapping", f"Step {n} PICK_TIPS needs tip_positions.", 'Example: "tip_positions": ["A1"].')
        rid = str(raw.get("tip_rack") or "").strip()
        if rid:
            rack = self.tipracks.get(rid) or self.resources.get(rid)
            if rack is None:
                raise CompileError("mapping", f"Step {n} PICK_TIPS tip_rack '{rid}' is not in resources.", "Point tip_rack at a declared tiprack id.")
            if rack.get("type") != "tiprack":
                raise CompileError("mapping", f"Step {n} PICK_TIPS tip_rack '{rid}' is type {rack.get('type')!r}, not tiprack.", "Use the tiprack resource id.")
        elif len(self.tipracks) == 1:
            rid = next(iter(self.tipracks))
        elif not self.tipracks:
            raise CompileError("mapping", f"Step {n} PICK_TIPS needs a tiprack resource.", 'Add {"id": "tips", "type": "tiprack", "slot": "1"}.')
        else:
            raise CompileError("mapping", f"Step {n} PICK_TIPS does not say which tip_rack to use.", "Set tip_rack to one of: " + ", ".join(sorted(self.tipracks)) + ".")
        self.command_count += 1
        self.tips_on = len(wells)
        return ["    await lh.pick_up_tips(" + " + ".join(f"{self.var_of[rid]}[{w!r}]" for w in wells) + ")"]

    def _render(self, body: list[str]) -> str:
        ham = sorted({r["factory"][0] for r in self.resources.values() if r["factory"][1] == "hamilton"})
        res = sorted({r["factory"][0] for r in self.resources.values() if r["factory"][1] == "resources"})
        layout = "; ".join(f"{r['id']} ({r['factory'][0]}) → rails {r['rails']}" for r in self.resources.values())
        plan_id = str(self.plan.get("plan_id") or self.plan.get("protocol_name") or "plan")
        if self.family == "star":
            ham_imp = ", ".join(["STARDeck", "TIP_CAR_480_A00", "PLT_CAR_L5AC_A00", *ham])
            live_backend = "STARBackend"
            deck_line = "    deck = STARDeck()"
            deck_note = "STARDeck with tip carrier (rails 1) and plate carrier (rails 8); trash is built-in."
            device_line = "Device: Hamilton STAR via PyLabRobot LiquidHandler."
            assigns = [
                "    tip_car = TIP_CAR_480_A00('tip_car')",
                "    plate_car = PLT_CAR_L5AC_A00('plate_car')",
            ]
            for r in self.resources.values():
                v = self.var_of[r["id"]]
                assigns.append(f"    {v} = {r['factory'][0]}({r['id']!r})")
                if r["type"] == "tiprack":
                    assigns.append(f"    tip_car[0] = {v}")
                elif r["type"] == "reservoir":
                    assigns.append(f"    deck.assign_child_resource({v}, rails=15)")
                else:
                    assigns.append(f"    plate_car[0] = {v}")
            assigns += [
                "    deck.assign_child_resource(tip_car, rails=1)",
                "    deck.assign_child_resource(plate_car, rails=8)",
            ]
        else:
            ham_imp = ", ".join(["VantageDeck", *ham])
            live_backend = "VantageBackend"
            deck_line = "    deck = VantageDeck(size=1.3)"
            deck_note = "Vantage 1.3 m; trash is built-in."
            device_line = "Device: Hamilton Vantage via PyLabRobot LiquidHandler."
            assigns = []
            for r in self.resources.values():
                v = self.var_of[r["id"]]
                assigns += [f"    {v} = {r['factory'][0]}({r['id']!r})", f"    deck.assign_child_resource({v}, rails={r['rails']})"]
        res_line = f"from pylabrobot.resources import {', '.join(res)}\n" if res else ""
        head = f'''\
"""LabscriptAI Plan IR → PyLabRobot (Hamilton STAR / Vantage).

{device_line}
THIS FILE DEFAULTS TO DRY-RUN (LiquidHandlerChatterboxBackend — no robot motion).
Live {self.family}: comment the ChatterboxBackend line, uncomment {live_backend}.

Run:
  pip install pylabrobot
  python this_file.py

Deck: {deck_note} Labware: {layout}.
Plan: {plan_id}
"""
from __future__ import annotations

import asyncio

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
# from pylabrobot.liquid_handling.backends import {live_backend}
from pylabrobot.resources.hamilton import {ham_imp}
{res_line}
async def main() -> None:
    backend = LiquidHandlerChatterboxBackend(num_channels=8)  # DRY-RUN
    # backend = {live_backend}()  # LIVE — robot will move
{deck_line}
'''
        tail = "\n".join(
            [*assigns, "    lh = LiquidHandler(backend=backend, deck=deck)", "    await lh.setup()", *body, "    await lh.stop()", "", "", 'if __name__ == "__main__":', "    asyncio.run(main())", ""]
        )
        return head + tail


def load_plan(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text or "")
    except json.JSONDecodeError as exc:
        raise CompileError("mapping", "Input is not valid JSON.", "Pass a Plan IR object on stdin (schema bpl.plan_ir.lh.v0).") from exc
    if not isinstance(payload, dict):
        raise CompileError("mapping", "Plan IR must be a JSON object.", "Top level needs schema, resources[], and steps[].")
    schema = str(payload.get("schema") or PLAN_SCHEMA_ID).strip()
    if schema != PLAN_SCHEMA_ID:
        raise CompileError("mapping", f"Unknown schema {schema!r}; expected {PLAN_SCHEMA_ID}.", f'Set "schema": "{PLAN_SCHEMA_ID}".')
    return payload


def parse_family(argv: list[str]) -> str:
    family = "vantage"
    i = 1
    while i < len(argv):
        if argv[i] == "--family" and i + 1 < len(argv):
            family = argv[i + 1].strip().lower()
            i += 2
            continue
        i += 1
    return family if family in {"star", "vantage"} else "vantage"


def compile_text(raw_text: str, family: str = "vantage") -> dict[str, Any]:
    return HamiltonCompiler(load_plan(raw_text), family).compile()


def main() -> int:
    family = parse_family(sys.argv)
    try:
        result = compile_text(sys.stdin.read(), family)
    except CompileError as exc:
        result = fail(exc.stage, exc.error, exc.hint)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        result = fail("internal", "Compiler crashed.", "See stderr traceback; this is a compiler bug.")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
