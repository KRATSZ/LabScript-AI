"""Plan IR schema + virtual-deck LogicPass + harness. No live robot."""

from __future__ import annotations

import pytest

from labscriptai.planir import (
    PLAN_SCHEMA_ID,
    PlanError,
    list_skills,
    load_plan,
    read_skill,
    run_plan_checks,
)
from labscriptai.planir.virtual_deck import evaluate_virtual_deck
from labscriptai.planir.plr_sim import pylabrobot_available, run_plr_sim

DEMO = {
    "schema": PLAN_SCHEMA_ID,
    "plan_id": "demo-transfer",
    "backend": "serializing",
    "resources": [
        {"id": "tips", "type": "tiprack", "slot": "1"},
        {"id": "plate", "type": "plate", "slot": "2", "max_volume_ul": 200},
    ],
    "initial_volumes_ul": {"plate:A1": 100, "plate:B1": 0},
    "steps": [
        {
            "step_id": "1",
            "primitive_type": "PICK_TIPS",
            "tip_rack": "tips",
            "tip_positions": ["A1"],
            "dependencies": [],
        },
        {
            "step_id": "2",
            "primitive_type": "ASPIRATE",
            "source": "plate:A1",
            "volume_ul": 50,
            "dependencies": ["1"],
        },
        {
            "step_id": "3",
            "primitive_type": "DISPENSE",
            "destination": "plate:B1",
            "volume_ul": 50,
            "dependencies": ["2"],
        },
        {
            "step_id": "4",
            "primitive_type": "DROP_TIPS",
            "to_waste": True,
            "dependencies": ["3"],
        },
    ],
}


def _ok_sim(_plan) -> dict:
    return {"ok": True, "backend": "test"}


def test_load_plan_accepts_demo() -> None:
    plan = load_plan(DEMO)
    assert plan.schema == PLAN_SCHEMA_ID
    assert [step.primitive_type for step in plan.ordered_steps()] == [
        "PICK_TIPS",
        "ASPIRATE",
        "DISPENSE",
        "DROP_TIPS",
    ]


def test_load_plan_rejects_unknown_schema() -> None:
    with pytest.raises(PlanError, match="unknown schema"):
        load_plan({**DEMO, "schema": "invented.ir.v0"})


def test_load_plan_rejects_bad_primitive() -> None:
    bad = {**DEMO, "steps": [{**DEMO["steps"][0], "primitive_type": "CENTRIFUGE"}]}
    with pytest.raises(PlanError, match="unsupported primitive"):
        load_plan(bad)


def test_virtual_deck_overflow() -> None:
    payload = {
        **DEMO,
        "initial_volumes_ul": {"plate:A1": 50, "plate:B1": 180},
        "steps": [
            DEMO["steps"][0],
            {**DEMO["steps"][1], "volume_ul": 50},
            {**DEMO["steps"][2], "volume_ul": 50},
            DEMO["steps"][3],
        ],
    }
    deck = evaluate_virtual_deck(load_plan(payload))
    assert deck.ok is False
    assert deck.issues[0].code == "LP-OVERFLOW"


def test_virtual_deck_empty() -> None:
    payload = {**DEMO, "initial_volumes_ul": {"plate:A1": 10, "plate:B1": 0}}
    payload = {
        **payload,
        "steps": [
            DEMO["steps"][0],
            {**DEMO["steps"][1], "volume_ul": 50},
            DEMO["steps"][2],
            DEMO["steps"][3],
        ],
    }
    deck = evaluate_virtual_deck(load_plan(payload))
    assert deck.ok is False
    assert deck.issues[0].code == "LP-EMPTY"


def test_sim_fail_skips_logicpass() -> None:
    out = run_plan_checks(
        DEMO,
        sim={"ok": False, "reason": "sim_failed", "errors": ["boom"]},
        skip_review=True,
    )
    assert out["sim"]["ok"] is False
    assert out["logicpass"]["outcome"] == "skipped"
    assert out["fab"]["lit"] is False
    assert "llmreview" not in out


def test_injected_sim_pass_then_logicpass() -> None:
    out = run_plan_checks(DEMO, sim=_ok_sim(None), skip_review=True)
    assert out["sim"]["ok"] is True
    assert out["logicpass"]["outcome"] == "pass"
    assert out["logicpass"]["logic_pass"] is True
    assert out["logicpass"]["final_pass_v2"] is True
    assert out["fab"]["lit"] is True
    assert "llmreview" not in out


def test_plr_sim_injected_runner() -> None:
    out = run_plr_sim(load_plan(DEMO), runner=_ok_sim)
    assert out["ok"] is True
    assert out["backend"] == "test"


@pytest.mark.skipif(not pylabrobot_available(), reason="pylabrobot not installed")
def test_plr_sim_demo_transfer_actually_runs() -> None:
    out = run_plr_sim(load_plan(DEMO))
    assert out["ok"] is True, out
    assert str(out.get("backend", "")).startswith("pylabrobot:")


def test_overflow_does_not_light_fab() -> None:
    payload = {
        **DEMO,
        "initial_volumes_ul": {"plate:A1": 50, "plate:B1": 180},
    }
    out = run_plan_checks(payload, sim=_ok_sim(None), skip_review=True)
    assert out["logicpass"]["outcome"] == "fail"
    assert out["fab"]["lit"] is False
    assert "llmreview" not in out


def test_skills_are_read_only() -> None:
    names = {item["name"] for item in list_skills()}
    assert "authoring-guide" in names
    assert "error-taxonomy" in names
    live = read_skill("safety-brief")
    assert "documentation only" in live.get("note", "").lower() or live.get("kind") == "live_docs_only"
    guide = read_skill("authoring-guide")
    assert guide.get("error") is None
    assert "authoring-guide" in guide.get("name", "")
    assert guide.get("text")
