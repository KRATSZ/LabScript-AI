"""Three-branch harness for Plan IR: PLR SimPass → virtual-deck LogicPass → llmreview."""

from __future__ import annotations

from typing import Any, Mapping

from labscriptai.planir.plr_sim import run_plr_sim
from labscriptai.planir.schema import PlanDocument, PlanError, load_plan
from labscriptai.planir.virtual_deck import evaluate_virtual_deck


def _public_sim(sim: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": bool(sim.get("ok"))}
    if sim.get("reason"):
        out["reason"] = sim["reason"]
    if sim.get("errors"):
        out["errors"] = list(sim["errors"])
    if sim.get("backend"):
        out["backend"] = sim["backend"]
    return out


def _skipped_logic(reason: str) -> dict[str, Any]:
    return {
        "outcome": "skipped",
        "logic_pass": False,
        "final_pass_v2": False,
        "issues": [],
        "reason": reason,
    }


def _unevaluable(reason: str) -> dict[str, Any]:
    return {
        "outcome": "unevaluable",
        "logic_pass": False,
        "final_pass_v2": False,
        "issues": [],
        "reason": reason,
    }


def _fab(sim: Mapping[str, Any], logicpass: Mapping[str, Any]) -> dict[str, bool]:
    lit = bool(
        sim.get("ok")
        and logicpass.get("outcome") == "pass"
        and logicpass.get("logic_pass") is True
        and logicpass.get("final_pass_v2") is True
    )
    return {"lit": lit}


def should_run_llmreview(sim: Mapping[str, Any], logicpass: Mapping[str, Any]) -> bool:
    if not sim.get("ok"):
        return False
    if logicpass.get("outcome") in {"skipped", "fail"}:
        return False
    if logicpass.get("reason") in {
        "logicpass_package_missing",
        "raise_only",
        "plr_unavailable",
    }:
        return False
    return logicpass.get("outcome") in {"pass", "unevaluable"}


def _review(
    *,
    user_intent: str,
    plan: PlanDocument,
    skip_review: bool,
    sim: Mapping[str, Any],
    logicpass: Mapping[str, Any],
) -> dict[str, Any] | None:
    if skip_review or not should_run_llmreview(sim, logicpass):
        return None
    try:
        from labscriptai.agent.llmreview import run_llmreview
    except ImportError:
        return {
            "match": False,
            "findings": [
                {
                    "severity": "error",
                    "claim": "reviewer_exception",
                    "evidence": "llmreview_package_missing",
                    "suggestion": "Install labscriptai.",
                }
            ],
            "reason": "llmreview_package_missing",
        }
    import json

    return run_llmreview(
        user_intent=user_intent,
        protocol_source=json.dumps(plan.to_public_dict(), ensure_ascii=False, indent=2),
        sim_error=None if sim.get("ok") else str(sim.get("reason") or "sim_failed"),
    )


def run_plan_checks(
    payload: Mapping[str, Any] | PlanDocument,
    *,
    user_intent: str = "",
    sim: Mapping[str, Any] | None = None,
    skip_review: bool = False,
) -> dict[str, Any]:
    """Return ``{sim, logicpass, llmreview?, fab}``. Same algebra as the OT Python path."""
    try:
        plan = load_plan(payload)
    except PlanError as exc:
        failed = {
            "ok": False,
            "reason": "invalid_plan",
            "errors": [str(exc)],
        }
        logic = _skipped_logic("invalid_plan")
        return {"sim": failed, "logicpass": logic, "fab": _fab(failed, logic)}

    sim_result = dict(sim) if sim is not None else run_plr_sim(plan)
    out: dict[str, Any] = {"sim": _public_sim(sim_result), "plan": plan.to_public_dict()}
    if not sim_result.get("ok"):
        logic = _skipped_logic(str(sim_result.get("reason") or "sim_failed"))
        out["logicpass"] = logic
        out["fab"] = _fab(out["sim"], logic)
        return out

    try:
        deck = evaluate_virtual_deck(plan)
    except Exception as exc:  # noqa: BLE001
        logic = _unevaluable(f"virtual_deck_error:{exc}")
        out["logicpass"] = logic
        out["fab"] = _fab(out["sim"], logic)
        return out

    logic = deck.to_logicpass()
    out["logicpass"] = logic
    if logic.get("outcome") != "fail":
        review = _review(
            user_intent=user_intent,
            plan=plan,
            skip_review=skip_review,
            sim=out["sim"],
            logicpass=logic,
        )
        if review is not None:
            out["llmreview"] = review
    out["fab"] = _fab(out["sim"], logic)
    return out
