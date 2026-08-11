"""Gate unit tests for the lean agent."""

from __future__ import annotations

from pathlib import Path

import pytest

from labscriptai.agent.gate import (
    RESUME_BLOCKED_RUN_STATUSES,
    ROBOT_ACT_ALIASES,
    SAFE_ACTION_TYPES,
    evaluate,
    infer_context,
    is_resume_play_request,
    resolve_robot_act_label,
    robot_act_allow_candidates,
)


def test_coerce_path_strips_mistaken_parent_prefix(tmp_path: Path) -> None:
    from labscriptai.agent.gate import coerce_path_into_workspace, evaluate

    (tmp_path / "local").mkdir()
    target = tmp_path / "local" / "protocol.py"
    target.write_text("# ok\n", encoding="utf-8")

    coerced = coerce_path_into_workspace("../local/protocol.py", tmp_path)
    assert coerced == "local/protocol.py"

    import os

    os.environ["LABSCRIPTAI_WORKSPACE"] = str(tmp_path)
    try:
        d = evaluate(
            "edit",
            {"op": "read", "path": "../local/protocol.py"},
            context="run",
            interactive=True,
        )
        assert d.status == "allow"
    finally:
        os.environ.pop("LABSCRIPTAI_WORKSPACE", None)


def test_coerce_path_leaves_true_escape(tmp_path: Path) -> None:
    from labscriptai.agent.gate import coerce_path_into_workspace

    # Outside path that does not exist under workspace after stripping
    out = coerce_path_into_workspace("../../etc/passwd", tmp_path)
    assert out == "../../etc/passwd"


def test_infer_context_run_when_robot_connected() -> None:
    assert infer_context(robot_connected=True, active_run=False) == "run"
    assert infer_context(robot_connected=True, active_run=True) == "run"


def test_skill_and_memory_allow() -> None:
    for name, args in (
        ("skill", {"op": "load", "name": "deck"}),
        ("memory", {"op": "read", "query": "tip"}),
        ("memory", {"op": "write", "title": "t", "body": "b"}),
    ):
        d = evaluate(name, args, context="author", interactive=True)
        assert d.status == "allow", (name, d)


def test_edit_inside_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LABSCRIPTAI_WORKSPACE", str(tmp_path))
    target = tmp_path / "protocol.py"
    target.write_text("# x\n", encoding="utf-8")
    d = evaluate("edit", {"path": str(target)}, context="author", interactive=True)
    assert d.status == "allow"
    rel = evaluate("edit", {"path": "protocol.py"}, context="author", interactive=True)
    assert rel.status == "allow"


def test_edit_outside_workspace_ask_or_suspend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LABSCRIPTAI_WORKSPACE", str(tmp_path))
    outside = Path("/tmp/labscriptai-gate-outside-test.py")
    d = evaluate("edit", {"path": str(outside)}, context="author", interactive=True)
    assert d.status == "ask"
    d2 = evaluate("edit", {"path": str(outside)}, context="author", interactive=False)
    assert d2.status == "suspend"


def test_bash_destructive_and_network() -> None:
    d = evaluate("bash", {"command": "rm -rf /tmp/x"}, context="author", interactive=True)
    assert d.status == "ask"
    d2 = evaluate("bash", {"command": ["curl", "https://example.com"]}, context="author", interactive=True)
    assert d2.status == "ask"
    d3 = evaluate("bash", {"command": "ls -la"}, context="author", interactive=True)
    assert d3.status == "allow"


def test_bash_robot_port_suspends() -> None:
    d = evaluate(
        "bash",
        {"command": "curl http://192.168.1.10:31950/runs"},
        context="run",
        interactive=True,
    )
    assert d.status == "suspend"
    assert any("robot" in r.lower() for r in d.reasons)


def test_bash_robot_ip_from_env_suspends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENTRONS_ROBOT_IP", "10.0.0.42")
    d = evaluate(
        "bash",
        {"command": "curl http://10.0.0.42/health"},
        context="run",
        interactive=True,
    )
    assert d.status == "suspend"


def test_robot_status_allow_act_author_suspend() -> None:
    assert evaluate("robot", {"op": "status"}, context="author", interactive=True).status == "allow"
    assert evaluate("robot", {"op": "watch"}, context="run", interactive=True).status == "allow"
    act = evaluate(
        "robot",
        {"op": "act", "action_type": "pause_run"},
        context="author",
        interactive=True,
    )
    assert act.status == "suspend"


def test_robot_act_run_safe_and_preauthorized() -> None:
    safe = next(iter(SAFE_ACTION_TYPES))
    d = evaluate(
        "robot",
        {"op": "act", "action_type": safe},
        context="run",
        interactive=True,
    )
    assert d.status == "allow"
    d2 = evaluate(
        "robot",
        {"op": "act", "action_type": "custom_wipe"},
        context="run",
        interactive=True,
        preauthorized={"custom_wipe"},
    )
    assert d2.status == "allow"
    d3 = evaluate(
        "robot",
        {"op": "act", "action_type": "custom_wipe"},
        context="run",
        interactive=True,
    )
    assert d3.status == "ask"


def test_daemon_upgrades_ask_to_suspend() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action_type": "not_safe"},
        context="run",
        interactive=False,
    )
    assert d.status == "suspend"
    assert any("upgraded" in r for r in d.reasons)


def test_robot_act_recovery_aliases_allowed_in_run_context() -> None:
    for args in (
        {"op": "act", "action": "execute_protocol_recovery", "recovery_branch": "drop_tip_left"},
        {"op": "act", "action": "drop_tip", "args": {"mount": "left"}},
        {"op": "act", "action_type": "recover_tip_pickup"},
        {"op": "act", "recovery_branch": "retry_pick_up_tip_with_next_candidate"},
        {"op": "act", "action": "recover_liquid_source_substitution"},
        {"op": "act", "action": "run_protocol"},
    ):
        d = evaluate("robot", args, context="run", interactive=True)
        assert d.status == "allow", (args, d)


def test_resolve_robot_act_label_from_recovery_branch_only() -> None:
    assert (
        resolve_robot_act_label({"recovery_branch": "retry_pick_up_tip_with_next_candidate"})
        == "execute_protocol_recovery"
    )


def test_robot_act_alias_maps_to_canonical() -> None:
    assert ROBOT_ACT_ALIASES["drop_tip"] == "drop_attached_tip"
    assert ROBOT_ACT_ALIASES["stop_run"] == "control_run"
    assert "drop_attached_tip" in SAFE_ACTION_TYPES
    assert "execute_protocol_recovery" in SAFE_ACTION_TYPES
    candidates = robot_act_allow_candidates("drop_tip")
    assert "drop_attached_tip" in candidates


def test_is_resume_play_request() -> None:
    assert is_resume_play_request({"op": "act", "action": "resume_run"}) is True
    assert is_resume_play_request({"op": "act", "action": "play_run"}) is True
    assert is_resume_play_request({"op": "act", "action": "pause_run"}) is False
    assert (
        is_resume_play_request({"op": "act", "action": "control_run", "args": {"action": "play"}})
        is True
    )


def test_resume_run_blocked_when_awaiting_recovery() -> None:
    for status in RESUME_BLOCKED_RUN_STATUSES:
        d = evaluate(
            "robot",
            {"op": "act", "action": "resume_run", "run_id": "abc"},
            context="run",
            interactive=True,
            active_run_status=status,
        )
        assert d.status == "suspend", (status, d)
        assert any("resume_run blocked" in r for r in d.reasons)


def test_resume_run_allowed_when_succeeded() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "resume_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="succeeded",
    )
    assert d.status == "allow"


def test_time_window_missing_does_not_block_resume() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "resume_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        time_window=None,
    )
    assert d.status == "allow"


def test_time_window_not_expired_allows_resume() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "play_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        time_window={
            "declared": True,
            "window_minutes": 5,
            "elapsed_minutes": 2,
            "expired": False,
        },
    )
    assert d.status == "allow"


def test_time_window_expired_blocks_play_resume() -> None:
    for args in (
        {"op": "act", "action": "resume_run", "run_id": "abc"},
        {"op": "act", "action": "play_run", "run_id": "abc"},
        {"op": "act", "action": "control_run", "args": {"action": "play"}},
    ):
        d = evaluate(
            "robot",
            args,
            context="run",
            interactive=True,
            active_run_status="paused",
            time_window={"declared": True, "expired": True, "elapsed_minutes": 20},
        )
        assert d.status == "suspend", (args, d)
        assert any("time window has expired" in r for r in d.reasons)
        assert any("abort" in r.lower() or "stop" in r.lower() for r in d.reasons)


def test_time_window_expired_does_not_block_abort() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "abort_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        time_window={"expired": True},
    )
    assert d.status == "allow"


def test_contamination_fields_missing_no_behavior_change() -> None:
    args = {
        "op": "act",
        "action": "probe_wells",
        "args": {"well": "C2:A1"},
    }
    d = evaluate("robot", args, context="run", interactive=True)
    assert d.status == "allow"
    d2 = evaluate(
        "robot",
        args,
        context="run",
        interactive=True,
        instruments_summary=[{"mount": "left", "contact_class": "sample", "has_tip": True}],
        well_roles=None,
    )
    assert d2.status == "allow"


def test_contamination_sample_tip_blocks_common_stock_probe() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"well": "C2:A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[{"mount": "left", "contact_class": "sample", "has_tip": True}],
        well_roles={"C2:A1": "common_stock"},
    )
    assert d.status == "suspend"
    assert any("drop tip" in r.lower() for r in d.reasons)


def test_contamination_clean_tip_allows_common_stock() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"well": "C2:A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[{"mount": "left", "contact_class": "clean", "has_tip": True}],
        well_roles={"C2:A1": "common_stock"},
    )
    assert d.status == "allow"


def test_contamination_sample_tip_allows_sample_well() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"well": "D2:A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[{"mount": "left", "contact_class": "sample", "has_tip": True}],
        well_roles={"D2:A1": "sample", "C2:A1": "common_stock"},
    )
    assert d.status == "allow"


def test_contamination_blocks_even_when_action_preauthorized() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "aspirate",
            "args": {"well": "C2:A1"},
        },
        context="run",
        interactive=True,
        preauthorized={"aspirate"},
        instruments_summary=[{"mount": "left", "contact_class": "sample", "has_tip": True}],
        well_roles={"C2:A1": "common_stock"},
    )
    assert d.status == "suspend"


def test_legacy_source_role_is_not_common_stock() -> None:
    """liquid_tracking legacy role='source' must not trigger contamination gate."""
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"well": "C2:A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[{"mount": "left", "contact_class": "sample", "has_tip": True}],
        well_roles={"C2:A1": "source"},
    )
    assert d.status == "allow"


def test_tip_budget_insufficient_blocks_recover_tip_pickup() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_tip_pickup"},
        context="run",
        interactive=True,
        tip_budget={
            "enforced": True,
            "sufficient": False,
            "basis": "live_scan",
            "available_tips": 0,
        },
    )
    assert d.status == "suspend"
    assert any("insufficient" in r.lower() for r in d.reasons)


def test_tip_budget_insufficient_blocks_tip_recovery_branch() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "execute_protocol_recovery",
            "recovery_branch": "retry_pick_up_tip_with_next_candidate",
        },
        context="run",
        interactive=True,
        tip_budget={"enforced": True, "sufficient": False, "basis": "live_scan"},
    )
    assert d.status == "suspend"


def test_tip_budget_basis_none_does_not_block() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_tip_pickup"},
        context="run",
        interactive=True,
        tip_budget={
            "enforced": False,
            "sufficient": False,
            "basis": "none",
        },
    )
    assert d.status == "allow"


def test_tip_budget_missing_does_not_block() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_tip_pickup"},
        context="run",
        interactive=True,
        tip_budget=None,
    )
    assert d.status == "allow"


def test_tip_budget_insufficient_blocks_play() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "play_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        tip_budget={
            "enforced": True,
            "sufficient": False,
            "basis": "live_scan",
            "available_tips": 0,
        },
    )
    assert d.status == "suspend"
    assert any("insufficient" in r.lower() for r in d.reasons)
    assert any("play" in r.lower() or "resume" in r.lower() for r in d.reasons)


def test_tip_budget_insufficient_allows_abort_and_stop() -> None:
    tip_budget = {
        "enforced": True,
        "sufficient": False,
        "basis": "live_scan",
    }
    for action in ("abort_run", "stop_run"):
        d = evaluate(
            "robot",
            {"op": "act", "action": action, "run_id": "abc"},
            context="run",
            interactive=True,
            active_run_status="paused",
            tip_budget=tip_budget,
        )
        assert d.status == "allow", (action, d)


def test_tip_budget_basis_none_allows_play() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "play_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        tip_budget={
            "enforced": False,
            "sufficient": False,
            "basis": "none",
        },
    )
    assert d.status == "allow"


def test_tip_budget_missing_allows_play() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "resume_run", "run_id": "abc"},
        context="run",
        interactive=True,
        active_run_status="paused",
        tip_budget=None,
    )
    assert d.status == "allow"


def test_volume_check_declared_insufficient_blocks_substitution() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        volume_check={
            "required_ul": 100,
            "usable_ul": 40,
            "sufficient": False,
            "basis": "declared_source_map",
        },
    )
    assert d.status == "suspend"
    assert any("insufficient" in r.lower() for r in d.reasons)


def test_volume_blocked_reason_blocks_substitution() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        blocked_reason="substitute_volume_insufficient",
    )
    assert d.status == "suspend"


def test_reserve_lpd_failed_blocks_substitution() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        blocked_reason="substitute_reserve_lpd_failed",
    )
    assert d.status == "suspend"


def test_approximate_lpd_height_insufficient_blocks_substitution() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        volume_check={
            "required_ul": 360,
            "usable_ul": 0,
            "sufficient": False,
            "basis": "approximate_lpd_height",
            "blocked_reason": "substitute_reserve_volume_insufficient",
        },
    )
    assert d.status == "suspend"


def test_volume_insufficient_data_does_not_block() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        volume_check={
            "sufficient": False,
            "basis": "insufficient_data",
        },
    )
    assert d.status == "allow"


def test_volume_check_missing_does_not_block() -> None:
    d = evaluate(
        "robot",
        {"op": "act", "action": "recover_liquid_source_substitution"},
        context="run",
        interactive=True,
        volume_check=None,
    )
    assert d.status == "allow"


def test_mcp_dot_keys_block_contamination_after_sample_probe() -> None:
    """08 shape: MCP wells_summary keys are SLOT.WELL; tip_detected not has_tip."""
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"slot_name": "C2", "well_name": "A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[
            {
                "mount": "left",
                "instrument_name": "p1000_single_flex",
                "tip_detected": True,
                "contact_class": "sample",
            }
        ],
        well_roles={
            "D2.A1": "sample",
            "C2.A1": "common_stock",
            "D2.*": "sample",
            "C2.*": "common_stock",
        },
    )
    assert d.status == "suspend"


def test_mcp_slot_wildcard_blocks_common_stock() -> None:
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"key": "C2.A3"},
        },
        context="run",
        interactive=True,
        instruments_summary=[
            {"mount": "left", "tip_detected": True, "contact_class": "sample"}
        ],
        well_roles={"C2.*": "common_stock", "D2.*": "sample"},
    )
    assert d.status == "suspend"


def test_case07_same_reagent_path_not_blocked() -> None:
    """07 FIX: tip only contacted common_stock (reservoir probe); dispense to plate
    does not set contact_class=sample, so re-probe of C2.A1 must remain allowed.
    """
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "probe_wells",
            "args": {"slot_name": "C2", "well_name": "A1"},
        },
        context="run",
        interactive=True,
        instruments_summary=[
            {
                "mount": "left",
                "tip_detected": True,
                # After reservoir aspirate/probe MCP marks stock/clean — not sample.
                "contact_class": "stock",
            }
        ],
        well_roles={
            "C2.A1": "common_stock",
            "D2.A1": "sample",
            "C2.*": "common_stock",
            "D2.*": "sample",
        },
    )
    assert d.status == "allow"


def test_case08_after_sample_probe_blocks_stock() -> None:
    """08 STOP: liquidProbe on sample plate marks tip sample; next stock move blocked."""
    d = evaluate(
        "robot",
        {
            "op": "act",
            "action": "aspirate",
            "args": {"key": "C2.A1"},
        },
        context="run",
        interactive=True,
        preauthorized={"aspirate"},
        instruments_summary=[
            {"mount": "left", "tip_detected": True, "contact_class": "sample"}
        ],
        well_roles={"C2.A1": "common_stock", "D2.A1": "sample"},
    )
    assert d.status == "suspend"

