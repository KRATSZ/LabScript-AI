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


def test_infer_context_author_without_robot_or_run() -> None:
    assert infer_context(robot_connected=False, active_run=False) == "author"
    assert infer_context(robot_connected=True, active_run=False) == "author"
    assert infer_context(robot_connected=False, active_run=True) == "author"


def test_infer_context_run_when_connected_and_active() -> None:
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
