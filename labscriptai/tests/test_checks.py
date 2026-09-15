"""Offline authoring-check, discovery, and reviewer tests (no API key)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import types

import pytest

from labscriptai.agent.checks import run_authoring_checks, sim_error_class
from labscriptai.agent.gate import evaluate
from labscriptai.agent.llmreview import REVIEW_SYSTEM_PROMPT, run_llmreview
from labscriptai.agent.loop import SessionState, run_turn
from labscriptai.tests.fixtures.protocols import (
    PROTOCOL_EMPTY_SOURCE,
    PROTOCOL_VOLUME_MISMATCH,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
ANALYZE_EMPTY = json.loads(
    (_FIXTURES / "analyze_empty_source.json").read_text(encoding="utf-8")
)


class _CountingLLM:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payload = payload or {
            "final": {
                "message": json.dumps(
                    {
                        "match": False,
                        "findings": [
                            {
                                "severity": "error",
                                "claim": "volume mismatch",
                                "evidence": "intent 10 µL vs aspirate 100",
                                "suggestion": "use 10 µL",
                            }
                        ],
                    }
                )
            }
        }

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls.append({"messages": messages, "tools": tools})
        return self.payload


def test_review_prompt_forbids_motion_and_uses_no_tools() -> None:
    client = _CountingLLM()
    run_llmreview(
        user_intent="transfer 10 µL A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        client=client,
    )
    assert client.calls
    assert client.calls[0]["tools"] is None
    prompt = "\n".join(
        str(m.get("content") or "") for m in client.calls[0]["messages"]
    )
    assert "Never play/resume" in prompt
    assert "Never play/resume" in REVIEW_SYSTEM_PROMPT
    assert "No tools" in REVIEW_SYSTEM_PROMPT
    assert "not syntax" in REVIEW_SYSTEM_PROMPT
    assert "SimPass error" in REVIEW_SYSTEM_PROMPT
    assert "liha_1000" in REVIEW_SYSTEM_PROMPT
    assert "200 µL DiTi" in REVIEW_SYSTEM_PROMPT
    for name in ("bash", "edit", "memory", "skill"):
        assert f'"{name}"' not in REVIEW_SYSTEM_PROMPT
    assert "TOOLS_SCHEMA" not in REVIEW_SYSTEM_PROMPT


def test_logicpass_fail_skips_reviewer(tmp_path: Path) -> None:
    from labscriptai.agent.checks import _import_logicpass

    evaluate_logicpass, load_analyze_json = _import_logicpass()
    if evaluate_logicpass is None or load_analyze_json is None:
        pytest.skip("LogicPass package not importable (Dev-A not landed)")
    client = _CountingLLM()
    path = tmp_path / "empty_source.py"
    path.write_text(PROTOCOL_EMPTY_SOURCE, encoding="utf-8")
    result = run_authoring_checks(
        path,
        user_intent="aspirate remaining volume without emptying the well",
        protocol_source=PROTOCOL_EMPTY_SOURCE,
        review_client=client,
        sim={"ok": True},
        analyze_payload=ANALYZE_EMPTY,
    )
    assert result["sim"]["ok"] is True
    assert result["logicpass"]["outcome"] == "fail"
    assert "llmreview" not in result
    assert client.calls == []


def test_sim_fail_skips_logicpass_and_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _CountingLLM()
    path = tmp_path / "proto.py"
    path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
    monkeypatch.setattr(
        "labscriptai.agent.checks._import_logicpass",
        lambda: (_ for _ in ()).throw(AssertionError("LP must not run")),
    )
    result = run_authoring_checks(
        path,
        user_intent="write A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        review_client=client,
        sim={
            "ok": False,
            "reason": "sim_failed",
            "errors": ["missing apiLevel"],
            "analyze": {"commands": ["DO_NOT_DUMP"], "errors": ["missing apiLevel"]},
        },
    )
    assert result["sim"]["ok"] is False
    assert result["sim"]["reason"] == "sim_failed"
    assert result["sim"]["errors"] == ["missing apiLevel"]
    assert "analyze" not in result["sim"]
    assert "DO_NOT_DUMP" not in json.dumps(result)
    assert "logicpass" not in result
    assert "llmreview" not in result
    assert client.calls == []


def test_sim_error_class_ignores_line_numbers() -> None:
    klass = sim_error_class(
        {
            "ok": False,
            "errors": [
                "IncompatibleAddressableAreaError [line 17]: Error 4000 "
                "GENERAL_ERROR (IncompatibleAddressableAreaError): Cannot use "
                "Waste Chute ... Slot D3"
            ],
        }
    )
    assert klass == "IncompatibleAddressableAreaError"
    assert sim_error_class({"ok": False, "reason": "sim_failed"}) == "sim_failed"


def test_stuck_review_on_sim_fail(tmp_path: Path) -> None:
    client = _CountingLLM()
    path = tmp_path / "proto.py"
    path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
    result = run_authoring_checks(
        path,
        user_intent="write A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        review_client=client,
        sim={
            "ok": False,
            "reason": "sim_failed",
            "errors": [
                "IncompatibleAddressableAreaError [line 12]: Slot D3 vs waste chute"
            ],
            "analyze": {"commands": ["DO_NOT_DUMP"]},
        },
        stuck_review=True,
    )
    assert result["sim"]["ok"] is False
    assert "logicpass" not in result
    assert result["llmreview"]["match"] is False
    assert len(client.calls) == 1
    blob = "\n".join(str(m.get("content") or "") for m in client.calls[0]["messages"])
    assert "Slot D3" in blob
    assert "DO_NOT_DUMP" not in blob
    assert client.calls[0]["tools"] is None


def test_review_exception_does_not_look_like_sim_fail() -> None:
    class _Boom:
        def complete(self, messages: list, tools: list | None = None) -> dict:
            raise ValueError("model response content is empty; finish_reason=length")

    payload = run_llmreview(
        user_intent="write A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        client=_Boom(),
    )
    assert payload["match"] is False
    claims = [f.get("claim") for f in payload.get("findings") or []]
    assert "reviewer_exception" in claims
    assert "sim_failed" not in json.dumps(payload)


def test_missing_logicpass_package_skips_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _CountingLLM()
    path = tmp_path / "proto.py"
    path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
    monkeypatch.setattr("labscriptai.agent.checks._import_logicpass", lambda: (None, None))
    result = run_authoring_checks(
        path,
        user_intent="100 µL A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        review_client=client,
        sim={"ok": True, "analyze": {"commands": []}},
    )
    assert result["logicpass"]["reason"] == "logicpass_package_missing"
    assert result["logicpass"]["outcome"] == "unevaluable"
    assert "llmreview" not in result
    assert client.calls == []


def test_logicpass_pass_runs_reviewer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _CountingLLM(
        {
            "final": {
                "message": json.dumps({"match": True, "findings": []}),
            }
        }
    )

    class _LP:
        outcome = "pass"
        logic_pass = True

        def to_dict(self) -> dict[str, Any]:
            return {"outcome": "pass", "logic_pass": True, "issues": [], "sim_pass": True}

    monkeypatch.setattr(
        "labscriptai.agent.checks._import_logicpass",
        lambda: (lambda **_k: _LP(), lambda **_k: types.SimpleNamespace(commands=())),
    )

    path = tmp_path / "proto.py"
    path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
    result = run_authoring_checks(
        path,
        user_intent="100 µL A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        review_client=client,
        sim={"ok": True},
        analyze_payload={"commands": []},
    )
    assert result["logicpass"]["outcome"] == "pass"
    assert result["llmreview"]["match"] is True
    assert len(client.calls) == 1
    assert client.calls[0]["tools"] is None


def test_skip_review_omits_flash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _CountingLLM()

    class _LP:
        outcome = "pass"
        logic_pass = True

        def to_dict(self) -> dict[str, Any]:
            return {"outcome": "pass", "logic_pass": True, "issues": [], "sim_pass": True}

    monkeypatch.setattr(
        "labscriptai.agent.checks._import_logicpass",
        lambda: (lambda **_k: _LP(), lambda **_k: types.SimpleNamespace(commands=())),
    )
    path = tmp_path / "proto.py"
    path.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
    result = run_authoring_checks(
        path,
        user_intent="100 µL A1 to B1",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        review_client=client,
        sim={"ok": True},
        analyze_payload={"commands": []},
        skip_review=True,
    )
    assert result["sim"]["ok"] is True
    assert result["logicpass"]["outcome"] == "pass"
    assert "llmreview" not in result
    assert client.calls == []


def test_review_strips_play_resume() -> None:
    client = _CountingLLM(
        {
            "final": {
                "message": json.dumps(
                    {
                        "match": False,
                        "findings": [
                            {
                                "severity": "warning",
                                "claim": "then resume_run / play the robot",
                                "evidence": "control_run play",
                                "suggestion": "play after fix",
                            }
                        ],
                    }
                )
            }
        }
    )
    payload = run_llmreview(
        user_intent="帮我通过好上机",
        protocol_source=PROTOCOL_VOLUME_MISMATCH,
        client=client,
    )
    blob = json.dumps(payload, ensure_ascii=False).lower()
    assert "resume_run" not in blob
    assert "control_run" not in blob
    assert "play" not in blob or "[redacted]" in blob
    assert payload["match"] is False


def test_author_context_allows_pressure_and_simulate() -> None:
    for action in ("run_pressure_trace", "analyze_pressure_trace", "simulate_protocol"):
        d = evaluate(
            "robot",
            {"op": "act", "action_type": action},
            context="author",
            interactive=True,
        )
        assert d.status == "allow", action
    paused = evaluate(
        "robot",
        {"op": "act", "action_type": "pause_run"},
        context="author",
        interactive=True,
    )
    assert paused.status == "suspend"


def test_pressure_without_robot_ip_is_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from labscriptai.agent import tools as tools_mod

    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_call_tool(name: str, args: dict, **kwargs: Any) -> dict:
        calls.append((name, dict(args)))
        return {"ok": True, "data": {"observation_only": True}}

    monkeypatch.setattr(tools_mod, "call_tool", fake_call_tool)
    out = tools_mod.execute(
        "robot",
        {"op": "act", "action_type": "analyze_pressure_trace", "csv_path": "/tmp/x.csv"},
        workspace=tmp_path,
        robot_ip=None,
        session={},
    )
    assert out.get("error") != "robot_ip_missing"
    assert calls and calls[0][0] == "analyze_pressure_trace"
    assert "robot_ip" not in calls[0][1]

    live = tools_mod.execute(
        "robot",
        {"op": "act", "action_type": "run_pressure_trace", "execute_on_robot": True},
        workspace=tmp_path,
        robot_ip=None,
        session={},
    )
    assert live.get("error") == "robot_ip_missing"

    sim_only = tools_mod.execute(
        "robot",
        {
            "op": "act",
            "action_type": "run_pressure_trace",
            "args": {"execute_on_robot": False, "well": "A1"},
        },
        workspace=tmp_path,
        robot_ip=None,
        session={},
    )
    assert sim_only.get("error") != "robot_ip_missing"


def test_edit_protocol_merges_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict[str, Any]] = []

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        path = tmp_path / str(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(args.get("content") or ""), encoding="utf-8")
        return {"ok": True, "path": args["path"]}

    def fake_checks(path: Path, **kwargs: Any) -> dict:
        captured.append({"path": str(path), **kwargs})
        return {
            "sim": {"ok": True},
            "logicpass": {"outcome": "pass", "logic_pass": True},
            "llmreview": {"match": True, "findings": []},
        }

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    monkeypatch.setattr("labscriptai.agent.checks.run_authoring_checks", fake_checks)

    class _Scripted:
        def __init__(self) -> None:
            self.n = 0

        def complete(self, messages: list, tools: list | None = None) -> dict:
            self.n += 1
            if self.n == 1:
                return {
                    "tool_calls": [
                        {
                            "id": "1",
                            "name": "edit",
                            "arguments": {
                                "op": "write",
                                "path": "local/demo.py",
                                "content": PROTOCOL_VOLUME_MISMATCH,
                            },
                        }
                    ]
                }
            return {"final": {"message": "drafted", "completed": True}}

    session = SessionState(workspace=tmp_path, interactive=True)
    text = run_turn("写 A1→B1 100µL", session=session, llm=_Scripted(), interactive=True)
    assert text == "drafted"
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    payload = json.loads(tool_msgs[0]["content"])
    assert "checks" in payload
    assert payload["checks"]["logicpass"]["outcome"] == "pass"
    assert captured


def test_bash_write_protocol_merges_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict[str, Any]] = []

    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        dest = tmp_path / "via_bash.py"
        dest.write_text(PROTOCOL_VOLUME_MISMATCH, encoding="utf-8")
        return {"stdout": "", "stderr": "", "rc": 0}

    def fake_checks(path: Path, **kwargs: Any) -> dict:
        captured.append({"path": str(path)})
        return {
            "sim": {"ok": True},
            "logicpass": {"outcome": "pass", "logic_pass": True},
            "llmreview": {"match": True, "findings": []},
        }

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    monkeypatch.setattr("labscriptai.agent.checks.run_authoring_checks", fake_checks)

    class _Scripted:
        def __init__(self) -> None:
            self.n = 0

        def complete(self, messages: list, tools: list | None = None) -> dict:
            self.n += 1
            if self.n == 1:
                return {
                    "tool_calls": [
                        {
                            "id": "1",
                            "name": "bash",
                            "arguments": {
                                "command": "cat > via_bash.py <<'EOF'\nfrom opentrons import protocol_api\nEOF"
                            },
                        }
                    ]
                }
            return {"final": {"message": "wrote via bash", "completed": True}}

    session = SessionState(workspace=tmp_path, interactive=True)
    run_turn("写协议", session=session, llm=_Scripted(), interactive=True)
    payload = json.loads(
        [m for m in session.messages if m.get("role") == "tool"][0]["content"]
    )
    assert "checks" in payload
    assert payload["checks"]["logicpass"]["outcome"] == "pass"
    assert captured
    assert captured[0]["path"].endswith("via_bash.py")


def test_bash_read_py_does_not_attach_checks() -> None:
    from labscriptai.agent.loop import _protocol_path_from_bash_command

    assert _protocol_path_from_bash_command("cat via_bash.py", Path("/tmp")) is None
    assert _protocol_path_from_bash_command("ls *.py", Path("/tmp")) is None


def test_run_context_skips_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(name: str, args: dict, **kwargs: Any) -> dict:
        path = tmp_path / str(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(args.get("content") or ""), encoding="utf-8")
        return {"ok": True, "path": args["path"]}

    monkeypatch.setattr("labscriptai.agent.loop.execute", fake_execute)
    monkeypatch.setattr(
        "labscriptai.agent.checks.run_authoring_checks",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("checks in run context")),
    )

    class _Scripted:
        def __init__(self) -> None:
            self.n = 0

        def complete(self, messages: list, tools: list | None = None) -> dict:
            self.n += 1
            if self.n == 1:
                return {
                    "tool_calls": [
                        {
                            "id": "1",
                            "name": "edit",
                            "arguments": {
                                "op": "write",
                                "path": "p.py",
                                "content": PROTOCOL_VOLUME_MISMATCH,
                            },
                        }
                    ]
                }
            return {"final": {"message": "ok", "completed": True}}

    session = SessionState(
        workspace=tmp_path,
        robot_ip="10.0.0.1",
        robot_connected=True,
        active_run_id="run-1",
        interactive=True,
    )
    run_turn("edit", session=session, llm=_Scripted(), interactive=True)
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    payload = json.loads(tool_msgs[0]["content"])
    assert "checks" not in payload


def test_skill_empty_list_still_works() -> None:
    from labscriptai.agent.tools import execute

    out = execute("skill", {"name": ""}, workspace=Path("."), robot_ip=None, session={})
    assert out.get("op") == "list"
    assert "pressure-trace" in out.get("skills", [])
    assert "recovery-playbooks" in out.get("skills", [])
    assert "authoring-guide" in out.get("skills", [])


def test_review_config_defaults_flash(monkeypatch: pytest.MonkeyPatch) -> None:
    from labscriptai.agent.llm import OpenAICompatibleConfig

    monkeypatch.setenv("DEEPSEEK_REVIEW_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_REVIEW_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-author")
    review = OpenAICompatibleConfig.from_env(
        prefix="DEEPSEEK_REVIEW",
        default_model="deepseek-v4-flash",
        fallback_prefix="DEEPSEEK",
        require_key=True,
    )
    author = OpenAICompatibleConfig.from_env(
        prefix="DEEPSEEK",
        default_model="deepseek-v4-pro",
        require_key=True,
    )
    assert review.model == "deepseek-v4-flash"
    assert author.model == "deepseek-v4-pro"
    assert author.model != review.model or True
