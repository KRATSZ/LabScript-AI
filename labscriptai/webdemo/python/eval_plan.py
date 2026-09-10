#!/usr/bin/env python3
"""Plan IR → {sim, logicpass, llmreview?, fab}. stdin JSON."""

from __future__ import annotations

import json
import sys
from typing import Any


def fail(reason: str, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "sim": {"ok": False, "reason": reason, "errors": errors or [reason]},
        "logicpass": {
            "outcome": "skipped",
            "logic_pass": False,
            "final_pass_v2": False,
            "issues": [],
            "reason": reason,
        },
        "fab": {"lit": False},
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ValueError("payload was not an object")
    except Exception as exc:
        print(json.dumps(fail("invalid_plan_json", [str(exc)])))
        return 0

    try:
        from labscriptai.planir import run_plan_checks
    except ImportError:
        print(json.dumps(fail("planir_package_missing")))
        return 0

    plan = payload.get("plan") if isinstance(payload.get("plan"), dict) else payload
    if payload.get("validate_only"):
        try:
            from labscriptai.planir.schema import PlanError, load_plan

            loaded = load_plan(plan)
            print(json.dumps({"ok": True, "plan": loaded.to_public_dict()}, ensure_ascii=False))
        except PlanError as exc:
            print(json.dumps({"ok": False, "errors": [str(exc)]}))
        except Exception as exc:
            print(json.dumps({"ok": False, "errors": [str(exc)]}))
        return 0

    result = run_plan_checks(
        plan,
        user_intent=str(payload.get("user_intent") or ""),
        skip_review=True,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
