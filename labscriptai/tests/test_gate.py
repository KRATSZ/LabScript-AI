"""Gate unit tests for the lean agent."""

from __future__ import annotations

from pathlib import Path

import pytest

from labscriptai.agent.gate import SAFE_ACTION_TYPES, evaluate, infer_context


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
