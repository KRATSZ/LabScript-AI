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
    assert 8 <= len(lines) <= 12
    lowered = prompt.lower()
    # mode is gate-only — must not appear as a model-facing switch
    assert "mode=" not in lowered
    assert "author mode" not in lowered and "run mode" not in lowered
    assert "bash" in lowered and "robot" in lowered and "skill" in lowered
    assert "only through robot" in lowered


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
