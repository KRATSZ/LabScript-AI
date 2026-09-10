#!/usr/bin/env python3
"""Plan IR → {sim, logicpass, llmreview?, fab}. stdin JSON."""

from __future__ import annotations

import json
import sys
from typing import Any


SKIP_DECK_REASONS = frozenset({"invalid_plan", "invalid_plan_json", "planir_package_missing"})


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


def attach_virtual_deck_if_sim_failed(result: dict[str, Any], plan: Any) -> dict[str, Any]:
    """webdemo-only: run virtual_deck when PLR fails so overflow is not swallowed.

    planir.run_plan_checks still skips LogicPass on sim fail (manuscript CLI unchanged).
    Overlay only fail/unevaluable; a passing deck keeps the skipped outcome so
    plr_unavailable stays cannot-verify instead of a fake fail.
    """
    sim = result.get("sim") if isinstance(result.get("sim"), dict) else {}
    logic = result.get("logicpass") if isinstance(result.get("logicpass"), dict) else {}
    if sim.get("ok") or logic.get("outcome") != "skipped":
        return result
    if str(sim.get("reason") or "") in SKIP_DECK_REASONS:
        return result
    try:
        from labscriptai.planir.schema import PlanError, load_plan
        from labscriptai.planir.virtual_deck import evaluate_virtual_deck

        deck = evaluate_virtual_deck(load_plan(plan))
        logicpass = deck.to_logicpass()
    except PlanError:
        return result
    except Exception as exc:  # noqa: BLE001
        logicpass = {
            "outcome": "unevaluable",
            "logic_pass": False,
            "final_pass_v2": False,
            "issues": [],
            "reason": f"virtual_deck_error:{exc}",
        }
    if logicpass.get("outcome") not in {"fail", "unevaluable"}:
        return result
    out = dict(result)
    out["logicpass"] = logicpass
    out["fab"] = {"lit": False}
    return out


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
    result = attach_virtual_deck_if_sim_failed(result, plan)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
