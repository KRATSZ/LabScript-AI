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


def _pipette_range_terminal_issue(detail_text: str) -> dict[str, Any]:
    """LogicIssue-shaped evidence for a gate that could not run."""
    return {
        "code": "LP-PIPETTE-UNKNOWN",
        "step_index": None,
        "well": None,
        "detail_text": detail_text,
        "severity": "terminal",
        "labware": None,
        "command_id": None,
        "hint": None,
        "provenance": "pipette_range",
    }


def _load_pipette_range_evaluator() -> Any:
    try:
        from pipette_range import evaluate_pipette_ranges
    except ImportError:
        from labscriptai.webdemo.python.pipette_range import evaluate_pipette_ranges
    return evaluate_pipette_ranges


def apply_pipette_range_gate(
    payload: dict[str, Any], analyze_json: dict[str, Any]
) -> dict[str, Any]:
    """Overlay the bounded pipette working-range gate on a LogicPass payload.

    Existing failures stay failures and gain range evidence.  A range failure
    overrides a pass/unevaluable result.  An unevaluable range check only
    changes an existing pass (to unevaluable); it never turns a failure into a
    pass.  ``final_pass_v2`` can only remain true when both layers pass.
    """

    try:
        evaluate = _load_pipette_range_evaluator()
        range_result = evaluate(analyze_json)
        if not isinstance(range_result, dict):
            raise TypeError("pipette range gate returned a non-object")
        gate_outcome = range_result.get("outcome")
        if gate_outcome not in {"pass", "fail", "unevaluable"}:
            raise ValueError(f"pipette range gate returned {gate_outcome!r}")
        gate_issues = range_result.get("issues")
        if not isinstance(gate_issues, list):
            gate_issues = []
        gate_reason = range_result.get("reason")
    except Exception as exc:
        gate_outcome = "unevaluable"
        gate_issues = [
            _pipette_range_terminal_issue(
                "Pipette working-range gate could not run "
                f"({type(exc).__name__}: {exc}); this check cannot verify "
                "the commanded volumes."
            )
        ]
        gate_reason = f"pipette_range_error:{type(exc).__name__}"

    old_outcome = payload.get("outcome")
    if gate_outcome == "fail":
        new_outcome = "fail"
    elif gate_outcome == "unevaluable":
        new_outcome = "fail" if old_outcome == "fail" else "unevaluable"
    else:
        new_outcome = old_outcome

    if gate_outcome != "pass":
        existing_issues = payload.get("issues")
        if not isinstance(existing_issues, list):
            existing_issues = [] if existing_issues is None else list(existing_issues)
        payload["issues"] = existing_issues + gate_issues

    payload["outcome"] = new_outcome
    payload["logic_pass"] = bool(
        new_outcome == "pass" and payload.get("logic_pass", False)
    )
    payload["final_pass_v2"] = bool(
        new_outcome == "pass" and payload.get("final_pass_v2", False)
    )

    if new_outcome == "unevaluable" and old_outcome != "unevaluable":
        payload["reason"] = gate_reason or "pipette_range_unevaluable"
    elif new_outcome == "fail" and old_outcome != "fail":
        # Do not leave an unevaluable/error reason on a deterministic failure.
        payload["reason"] = None

    return payload


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
            payload.setdefault("final_pass_v2", False)
            apply_pipette_range_gate(payload, analyze_json)
            payload["statepass"] = project_statepass(payload, result)
        print(json.dumps(payload, default=str))
    except Exception as exc:
        print(json.dumps(unevaluable(f"logicpass_error:{exc}")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
