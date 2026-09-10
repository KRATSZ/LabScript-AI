#!/usr/bin/env python3
"""Thin CLI: analyze JSON in → FinalPass_v2 dict + statepass. Do not rewrite rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def unevaluable(reason: str) -> dict[str, Any]:
    return {
        "sim_pass": True,
        "outcome": "unevaluable",
        "logic_pass": False,
        "final_pass_v2": False,
        "issues": [],
        "coverage": {},
        "input_conflicts": [],
        "provenance": None,
        "reason": reason,
        "statepass": {
            "issues": [],
            "coverage": {},
            "input_conflicts": [],
            "ledger_event_count": 0,
            "ledger_well_count": 0,
            "ledger_tip_count": 0,
            "ledger_reagent_count": 0,
            "reason": reason,
        },
    }


def project_statepass(payload: dict[str, Any], result: Any) -> dict[str, Any]:
    ledger = getattr(result, "ledger", None)
    return {
        "issues": payload.get("issues") or [],
        "coverage": payload.get("coverage") or {},
        "input_conflicts": payload.get("input_conflicts") or [],
        "ledger_event_count": len(getattr(ledger, "events", []) or []) if ledger else 0,
        "ledger_well_count": len(getattr(ledger, "wells", {}) or {}) if ledger else 0,
        "ledger_tip_count": len(getattr(ledger, "tips", {}) or {}) if ledger else 0,
        "ledger_reagent_count": len(getattr(ledger, "reagents", {}) or {}) if ledger else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", default="", help="Analyze JSON path (default: stdin)")
    parser.add_argument("--protocol", default="", help="Protocol .py path")
    parser.add_argument("--sim-pass", default="true")
    args = parser.parse_args()

    try:
        raw = (
            Path(args.analyze).read_text(encoding="utf-8")
            if args.analyze
            else sys.stdin.read()
        )
        analyze_json = json.loads(raw or "{}")
        if not isinstance(analyze_json, dict):
            raise ValueError("analyze JSON was not an object")
    except Exception:
        print(json.dumps(unevaluable("invalid_analyze_json")))
        return 0

    try:
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json
    except ImportError:
        print(json.dumps(unevaluable("logicpass_package_missing")))
        return 0

    sim_pass = str(args.sim_pass).lower() not in {"0", "false", "no"}
    protocol_path = args.protocol or None
    try:
        adapter = load_analyze_json(payload=analyze_json, protocol_path=protocol_path)
        result = evaluate_logicpass(sim_pass=sim_pass, adapter=adapter)
        payload = result.to_dict() if hasattr(result, "to_dict") else {}
        if not isinstance(payload, dict):
            payload = unevaluable("logicpass_bad_result")
        else:
            payload["statepass"] = project_statepass(payload, result)
            payload.setdefault("final_pass_v2", False)
        print(json.dumps(payload, default=str))
    except Exception as exc:
        print(json.dumps(unevaluable(f"logicpass_error:{exc}")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
