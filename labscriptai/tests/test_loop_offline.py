"""Offline unit tests for the lean agent loop (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from labscriptai.agent.loop import (
    SessionState,
    append_outbox,
    build_system_prompt,
    run_turn,
)


class _ScriptedLLM:
    """Return a canned sequence of complete() payloads."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[list[dict[str, Any]], list[dict[str, Any]] | None]] = []

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((list(messages), tools))
        if not self.responses:
            return {"final": {"message": "empty script", "completed": True}}
        return self.responses.pop(0)


def test_system_prompt_length_and_no_mode(tmp_path: Path) -> None:
    session = SessionState(workspace=tmp_path, robot_ip=None, robot_connected=False)
    prompt = build_system_prompt(session)
    lines = [ln for ln in prompt.splitlines() if ln.strip()]
    # Discovery line for run_pressure_trace is required; cap raised from 12 to 16.
    assert 8 <= len(lines) <= 16
    lowered = prompt.lower()
    # mode is gate-only — must not appear as a model-facing switch
    assert "mode=" not in lowered
    assert "author mode" not in lowered and "run mode" not in lowered
    assert "bash" in lowered and "robot" in lowered and "skill" in lowered
    assert "only through robot" in lowered
    assert "run_pressure_trace" in prompt
    assert "edit a .py" in prompt
    assert "checks.sim.ok" in prompt
    assert "robotType" in prompt and "Flex" in prompt
    assert "load_waste_chute()" in prompt
    assert "apiLevel" in prompt
    assert "flex_1channel_50" in prompt
    assert "flex_1channel_1000" in prompt
    assert "no flex_1channel_200" in prompt or "no 200" in prompt
    assert "temperatureModuleV2" in prompt
    assert "magneticBlockV1" in prompt
    assert "not metadata" in prompt
    assert "tip_racks" in prompt
    assert "D3" in prompt
    assert ">50" in prompt


def test_run_turn_final_message(tmp_path: Path) -> None:
    llm = _ScriptedLLM([{"final": {"message": "hello from stub", "completed": False}}])
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("hi", session=session, llm=llm, interactive=True)
    assert text == "hello from stub"
    assert session.messages[0]["role"] == "system"
    assert session.messages[-1]["role"] == "assistant"


def test_run_turn_allow_executes_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        calls.append((name, dict(args)))
        return {"ok": True, "echo": args}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)

    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "skill",
                        "arguments": {"name": "safety-brief"},
                    }
                ]
            },
            {"final": {"message": "loaded skill", "completed": True}},
        ]
    )
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("load skill", session=session, llm=llm, interactive=True)
    assert text == "loaded skill"
    assert calls == [("skill", {"name": "safety-brief"})]
    assert any(m.get("role") == "tool" for m in session.messages)


def test_run_turn_emits_progress_before_final(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        del name, args, kwargs
        return {
            "ok": True,
            "checks": {
                "sim": {"ok": False, "reason": "sim_failed", "errors": ["missing apiLevel"]},
            },
        }

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "edit",
                        "arguments": {"op": "write", "path": "p.py"},
                    }
                ]
            },
            {"final": {"message": "drafted", "completed": True}},
        ]
    )
    events: list[str] = []
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn(
        "write protocol",
        session=session,
        llm=llm,
        interactive=True,
        on_event=events.append,
    )
    assert text == "drafted"
    assert events[0] == "thinking"
    assert "edit write p.py" in events
    assert any(e.startswith("checks sim=red") for e in events)
    assert events.count("thinking") >= 2


def test_run_turn_ask_interactive_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        executed.append(name)
        return {"ok": True}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)

    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "bash",
                        "arguments": {"command": "rm -rf /tmp/x"},
                    }
                ]
            },
            {"final": {"message": "understood, skipped", "completed": True}},
        ]
    )
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn(
        "clean",
        session=session,
        llm=llm,
        interactive=True,
        confirm=lambda _p: False,
    )
    assert text == "understood, skipped"
    assert executed == []
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    assert tool_msgs
    payload = json.loads(tool_msgs[0]["content"])
    assert payload["status"] == "denied"


def test_run_turn_suspend_writes_outbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "labscriptai.agent.loop.execute",
        lambda *a, **k: {"should_not": "run"},
    )
    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "robot",
                        "arguments": {"op": "act", "action_type": "unknown_danger"},
                    }
                ]
            },
            {"final": {"message": "waiting on human", "completed": False}},
        ]
    )
    session = SessionState(
        workspace=tmp_path,
        robot_ip="10.0.0.1",
        robot_connected=True,
        active_run_id="run-1",
        interactive=False,
    )
    text = run_turn("fix it", session=session, llm=llm, interactive=False)
    assert "waiting" in text
    outbox = tmp_path / ".labscriptai" / "outbox"
    assert outbox.is_dir()
    files = list(outbox.glob("suspend_*.json"))
    assert files
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["kind"] == "gate_suspend"
    assert payload["tool"] == "robot"


def test_append_outbox_wake_jsonl(tmp_path: Path) -> None:
    path = append_outbox(tmp_path, {"kind": "test", "n": 1})
    assert path.is_file()
    wake = tmp_path / ".labscriptai" / "outbox" / "wake.jsonl"
    assert wake.is_file()
    assert "test" in wake.read_text(encoding="utf-8")


def test_tools_schema_is_five() -> None:
    from labscriptai.agent.loop import TOOLS_SCHEMA

    assert len(TOOLS_SCHEMA) == 5
    names = {
        (t.get("function") or {}).get("name") if t.get("type") == "function" else t.get("name")
        for t in TOOLS_SCHEMA
    }
    assert names == {"bash", "edit", "robot", "memory", "skill"}
    robot = next(t for t in TOOLS_SCHEMA if (t.get("function") or {}).get("name") == "robot")
    desc = str((robot.get("function") or {}).get("description") or "")
    assert "run_pressure_trace" in desc


def test_run_turn_tool_exception_becomes_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(name: str, args: dict, **kwargs: Any) -> dict:
        raise RuntimeError("HTTPError 405 Method Not Allowed")

    monkeypatch.setattr("labscriptai.agent.loop.execute", boom)

    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "skill",
                        "arguments": {"name": "safety-brief"},
                    }
                ]
            },
            {"final": {"message": "saw the error and continued", "completed": True}},
        ]
    )
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("load skill", session=session, llm=llm, interactive=True)
    assert text == "saw the error and continued"
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    assert tool_msgs
    payload = json.loads(tool_msgs[0]["content"])
    assert payload["status"] == "error"
    assert payload["error"]["type"] == "RuntimeError"
    assert "405" in payload["error"]["message"]


def test_run_turn_suspend_still_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: gate suspend must not be swallowed by the exception path."""
    executed: list[str] = []

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        executed.append(name)
        return {"ok": True}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "robot",
                        "arguments": {"op": "act", "action": "resume_run", "run_id": "r1"},
                    }
                ]
            },
            {"final": {"message": "stopped after suspend", "completed": True}},
        ]
    )
    session = SessionState(
        workspace=tmp_path,
        robot_ip="10.0.0.1",
        robot_connected=True,
        active_run_id="r1",
        active_run_status="awaiting-recovery",
        interactive=True,
    )
    text = run_turn("resume", session=session, llm=llm, interactive=True)
    assert "stopped" in text
    assert executed == []
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    payload = json.loads(tool_msgs[0]["content"])
    assert payload["status"] == "suspended"


def test_sync_session_runtime_fields(tmp_path: Path) -> None:
    from labscriptai.agent.loop import _sync_session_run_status

    session = SessionState(workspace=tmp_path, robot_connected=True, active_run_id="r1")
    _sync_session_run_status(
        session,
        {
            "robot_status": {
                "data": {
                    "status": "paused",
                    "time_window": {"declared": True, "expired": False, "window_minutes": 5},
                    "instruments_summary": [
                        {
                            "mount": "left",
                            "tip_detected": True,
                            "contact_class": "sample",
                        }
                    ],
                    "wells_summary": [
                        {
                            "key": "C2.A1",
                            "slot_name": "C2",
                            "well_name": "A1",
                            "role": "common_stock",
                        },
                        {
                            "key": "D2.A1",
                            "slot_name": "D2",
                            "well_name": "A1",
                            "role": "sample",
                        },
                    ],
                    "well_roles": {"C2.A1": "waste", "C2.*": "common_stock"},
                }
            },
            "tip_budget": {
                "enforced": True,
                "sufficient": False,
                "basis": "live_scan",
            },
            "volume_check": {
                "basis": "declared_source_map",
                "sufficient": False,
                "required_ul": 100,
                "usable_ul": 40,
            },
            "blocked_reason": "substitute_volume_insufficient",
        },
    )
    assert session.active_run_status == "paused"
    assert session.time_window and session.time_window.get("expired") is False
    assert session.instruments_summary[0]["contact_class"] == "sample"
    assert session.well_roles["C2.A1"] == "common_stock"
    assert session.well_roles["D2.A1"] == "sample"
    assert session.tip_budget and session.tip_budget["enforced"] is True
    assert session.volume_check and session.volume_check["sufficient"] is False
    assert session.blocked_reason == "substitute_volume_insufficient"

    # Non-live payload without gate fields keeps prior values.
    _sync_session_run_status(session, {"ok": True})
    assert session.tip_budget and session.tip_budget["sufficient"] is False
    assert session.well_roles["C2.A1"] == "common_stock"

    # Fresh live-state without tip_budget clears sticky tip/volume blocks.
    _sync_session_run_status(
        session,
        {
            "robot_status": {
                "data": {
                    "status": "running",
                    "instruments_summary": [
                        {"mount": "left", "tip_detected": True, "contact_class": "clean"}
                    ],
                    "wells_summary": [
                        {"key": "C2.A1", "slot_name": "C2", "well_name": "A1", "role": "common_stock"}
                    ],
                }
            }
        },
    )
    assert session.tip_budget is None
    assert session.volume_check is None
    assert session.blocked_reason is None


def test_sync_ignores_legacy_source_role(tmp_path: Path) -> None:
    from labscriptai.agent.loop import _sync_session_run_status

    session = SessionState(workspace=tmp_path, robot_connected=True, active_run_id="r1")
    _sync_session_run_status(
        session,
        {
            "robot_status": {
                "data": {
                    "wells": [{"key": "C2.A1", "role": "source"}],
                }
            }
        },
    )
    assert session.well_roles == {}


def test_sync_clears_gates_on_terminal_status(tmp_path: Path) -> None:
    from labscriptai.agent.loop import _sync_session_run_status

    session = SessionState(
        workspace=tmp_path,
        tip_budget={"enforced": True, "sufficient": False},
        volume_check={"sufficient": False, "basis": "declared_source_map"},
        blocked_reason="substitute_volume_insufficient",
    )
    _sync_session_run_status(session, {"active_run_status": "succeeded"})
    assert session.tip_budget is None
    assert session.volume_check is None
    assert session.blocked_reason is None


def test_robot_status_attaches_protocol_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from labscriptai.agent import tools as tools_mod

    calls: list[tuple[str, dict]] = []

    def fake_call_tool(name: str, args: dict, **kwargs: Any) -> dict:
        calls.append((name, dict(args)))
        if name == "robot_status":
            return {"data": {"status": "idle"}}
        return {"data": {}}

    proto = tmp_path / "local" / "demo.py"
    proto.parent.mkdir(parents=True)
    proto.write_text("metadata = {'protocolName': 'demo'}\n", encoding="utf-8")

    monkeypatch.setattr(tools_mod, "call_tool", fake_call_tool)
    monkeypatch.setattr(tools_mod, "_attach_active_run_status", lambda *a, **k: None)
    monkeypatch.setattr(tools_mod, "_is_error_payload", lambda _p: False)

    tools_mod._robot_status(
        host="10.0.0.1",
        base="http://10.0.0.1:31950",
        run_id=None,
        session_id=None,
        include_modules=False,
        workspace=tmp_path,
    )
    assert calls
    status_args = calls[0][1]
    assert status_args.get("file_path") or status_args.get("protocol_path")
    assert calls[0][0] == "robot_status"


def test_requirements_json_does_not_eat_prose() -> None:
    from labscriptai.agent.llm import _parse_completion_message
    from labscriptai.agent.loop import _final_text

    blob = (
        'The protocol is written and simulates cleanly.\n'
        '{"robotType": "Flex", "apiLevel": "2.20"}'
    )
    parsed = _parse_completion_message(
        {"choices": [{"message": {"content": blob}}]}
    )
    text = _final_text(parsed)
    assert "simulates cleanly" in text
    assert text != '{"robotType": "Flex", "apiLevel": "2.20"}'


def test_bare_requirements_json_is_not_structured_final() -> None:
    from labscriptai.agent.llm import _parse_completion_message
    from labscriptai.agent.loop import _final_text

    parsed = _parse_completion_message(
        {
            "choices": [
                {
                    "message": {
                        "content": '{"robotType": "Flex", "apiLevel": "2.20"}'
                    }
                }
            ]
        }
    )
    assert parsed["final"].get("robotType") is None
    assert parsed["final"]["message"].startswith("{")


def test_second_green_edit_skips_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from labscriptai.tests.fixtures.protocols import PROTOCOL_VOLUME_MISMATCH

    skip_flags: list[bool] = []

    def fake_checks(*_a: Any, skip_review: bool = False, **_k: Any) -> dict[str, Any]:
        skip_flags.append(skip_review)
        out: dict[str, Any] = {
            "sim": {"ok": True},
            "logicpass": {"outcome": "pass", "logic_pass": True},
        }
        if not skip_review:
            out["llmreview"] = {"match": True, "findings": []}
        return out

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        del name, kwargs
        path = tmp_path / str(args.get("path") or "p.py")
        path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
        return {"ok": True, "op": args.get("op")}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    monkeypatch.setattr(
        "labscriptai.agent.checks.run_authoring_checks", fake_checks
    )
    llm = _ScriptedLLM(
        [
            {
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "edit",
                        "arguments": {"op": "write", "path": "a.py"},
                    }
                ]
            },
            {
                "tool_calls": [
                    {
                        "id": "2",
                        "name": "edit",
                        "arguments": {"op": "str_replace", "path": "a.py"},
                    }
                ]
            },
            {"final": {"message": "done", "completed": True}},
        ]
    )
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("write", session=session, llm=llm, interactive=True)
    assert text == "done"
    assert skip_flags == [False, True]


def test_same_sim_class_reviews_on_third_not_green_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from labscriptai.tests.fixtures.protocols import PROTOCOL_VOLUME_MISMATCH

    reds_left = {"n": 4}
    stuck_calls: list[str] = []
    skip_flags: list[bool] = []

    def fake_checks(*_a: Any, skip_review: bool = False, **_k: Any) -> dict[str, Any]:
        skip_flags.append(skip_review)
        if reds_left["n"] > 0:
            reds_left["n"] -= 1
            return {
                "sim": {
                    "ok": False,
                    "errors": [
                        f"IncompatibleAddressableAreaError [line {reds_left['n']}]: Slot D3"
                    ],
                }
            }
        out: dict[str, Any] = {
            "sim": {"ok": True},
            "logicpass": {"outcome": "pass", "logic_pass": True},
        }
        if not skip_review:
            out["llmreview"] = {"match": True, "findings": []}
        return out

    def fake_stuck(**kwargs: Any) -> dict[str, Any]:
        stuck_calls.append(str(kwargs.get("sim_error") or kwargs.get("sim") or ""))
        return {
            "match": False,
            "findings": [{"severity": "error", "claim": "move off D3", "evidence": "", "suggestion": ""}],
        }

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        del name, kwargs
        path = tmp_path / str(args.get("path") or "a.py")
        path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
        return {"ok": True, "op": args.get("op")}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    monkeypatch.setattr("labscriptai.agent.checks.run_authoring_checks", fake_checks)
    monkeypatch.setattr("labscriptai.agent.checks.stuck_llmreview", fake_stuck)

    def _edit(n: str) -> dict[str, Any]:
        return {
            "tool_calls": [
                {"id": n, "name": "edit", "arguments": {"op": "write", "path": "a.py"}}
            ]
        }

    llm = _ScriptedLLM(
        [_edit("1"), _edit("2"), _edit("3"), _edit("4"), _edit("5"), {"final": {"message": "done", "completed": True}}]
    )
    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("write", session=session, llm=llm, interactive=True)
    assert text == "done"
    assert len(stuck_calls) == 1
    assert session.llmreview_ran is True
    assert skip_flags == [False, False, False, False, False]
    reviews = []
    for message in session.messages:
        if message.get("role") != "tool":
            continue
        payload = json.loads(str(message.get("content") or ""))
        if isinstance(payload, dict) and isinstance(payload.get("checks"), dict):
            reviews.append("llmreview" in payload["checks"])
    assert reviews == [False, False, True, False, True]
