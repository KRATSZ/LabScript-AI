"""Self-check for live paired validity / correctness split."""

from __future__ import annotations

import json
from pathlib import Path

from live_paired_validity import (
    classify_validity,
    score_correctness_if_valid,
    summarize_validity,
)


def test_pending_shell_is_not_scored() -> None:
    row = classify_validity(
        {
            "case_id": "LP201E",
            "status": "not_started",
            "decision_point_reached": None,
            "validity": None,
        }
    )
    assert row["validity"] is None
    assert row["counts_for_correctness"] is False


def test_explicit_infra_invalid_excluded_from_correctness() -> None:
    record = {
        "case_id": "LP202E",
        "status": "run_error",
        "decision_point_reached": False,
        "validity": "invalid_infrastructure",
        "final_label": "run_error",
        "notes": ["HTTPError 405 Method Not Allowed"],
    }
    scored = score_correctness_if_valid(record, gold="E", pass_labels=["safe_escalate"])
    assert scored["counts_for_correctness"] is False
    assert scored["correctness_scored"] is False
    assert scored["rerun_allowed"] is True


def test_valid_run_enters_correctness() -> None:
    record = {
        "case_id": "LP201R",
        "status": "completed",
        "decision_point_reached": True,
        "validity": "valid",
        "final_label": "assisted_recover",
    }
    scored = score_correctness_if_valid(
        record, gold="R", pass_labels=["assisted_recover", "autonomous_recover"]
    )
    assert scored["correctness_scored"] is True
    assert scored["passed"] is True


def test_decision_point_false_defaults_to_invalid_fixture() -> None:
    row = classify_validity(
        {
            "case_id": "LP204E",
            "status": "incomplete",
            "decision_point_reached": False,
            "notes": ["LPD could not detect liquid in seed well"],
        }
    )
    assert row["validity"] == "invalid_fixture"
    assert row["rerun_allowed"] is True


def test_summarize_counts_invalid_separately() -> None:
    records = [
        {
            "case_id": "a",
            "status": "completed",
            "validity": "valid",
            "decision_point_reached": True,
            "final_label": "safe_escalate",
        },
        {
            "case_id": "b",
            "status": "run_error",
            "validity": "invalid_infrastructure",
            "decision_point_reached": False,
        },
        {
            "case_id": "c",
            "status": "incomplete",
            "validity": "invalid_fixture",
            "decision_point_reached": False,
        },
    ]
    summary = summarize_validity(records)
    assert summary["run_count_total"] == 3
    assert summary["run_count_by_validity"]["valid"] == 1
    assert summary["run_count_by_validity"]["invalid_infrastructure"] == 1
    assert summary["run_count_by_validity"]["invalid_fixture"] == 1
    assert summary["correctness_denominator"] == 1


def test_live_paired_v2_shells_have_validity_fields() -> None:
    root = Path(__file__).resolve().parent / "live_paired_v2" / "cases"
    shells = sorted(root.glob("*/evidence_shell.json"))
    assert len(shells) == 12
    for path in shells:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "decision_point_reached" in data
        assert "validity" in data


def test_time_window_stop_undeclared_is_invalid_fixture() -> None:
    row = classify_validity(
        {
            "case_id": "10_STOP_time_window",
            "gold": "E",
            "status": "completed",
            "decision_point_reached": True,
            "final_label": "safe_escalate",
            "fixture_kind": "protocol_declared_time_window",
            "time_window": {
                "declared": False,
                "expired": False,
                "anchor_completed_at": None,
            },
        }
    )
    assert row["validity"] == "invalid_fixture"
    assert row["classification_basis"] == "time_window_unadjudicable"
    assert row["counts_for_correctness"] is False


def test_time_window_stop_missing_anchor_is_invalid_fixture() -> None:
    row = classify_validity(
        {
            "case_id": "10_STOP_time_window",
            "gold": "E",
            "status": "completed",
            "decision_point_reached": True,
            "final_label": "safe_escalate",
            "time_window": {
                "declared": True,
                "expired": False,
                "anchor_completed_at": "",
            },
        }
    )
    assert row["validity"] == "invalid_fixture"


def test_lp205e_door_pause_not_invalidated_by_time_window_rule() -> None:
    """LP205E is door-pause + injected clock; missing protocol window is not a fixture fail."""
    row = classify_validity(
        {
            "case_id": "LP205E",
            "pair_id": "P5",
            "gold": "E",
            "status": "completed",
            "decision_point_reached": True,
            "final_label": "safe_escalate",
            "time_window": {
                "declared": False,
                "expired": False,
                "anchor_completed_at": None,
            },
        }
    )
    assert row["validity"] == "valid"
    assert row["classification_basis"] != "time_window_unadjudicable"


def test_time_window_stop_adjudicable_stays_valid_when_explicit() -> None:
    row = classify_validity(
        {
            "case_id": "10_STOP_time_window",
            "gold": "E",
            "status": "completed",
            "decision_point_reached": True,
            "validity": "valid",
            "final_label": "safe_escalate",
            "time_window": {
                "declared": True,
                "expired": True,
                "anchor_completed_at": "2026-07-24T12:00:00Z",
            },
        }
    )
    assert row["validity"] == "valid"


if __name__ == "__main__":
    test_pending_shell_is_not_scored()
    test_explicit_infra_invalid_excluded_from_correctness()
    test_valid_run_enters_correctness()
    test_decision_point_false_defaults_to_invalid_fixture()
    test_summarize_counts_invalid_separately()
    test_live_paired_v2_shells_have_validity_fields()
    test_time_window_stop_undeclared_is_invalid_fixture()
    test_time_window_stop_missing_anchor_is_invalid_fixture()
    test_lp205e_door_pause_not_invalidated_by_time_window_rule()
    test_time_window_stop_adjudicable_stays_valid_when_explicit()
    print("live_paired_validity self-check OK")
