from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

from labscriptai.agent.facade import _author_permissions
from labscriptai.agent.loop import LabscriptAgentLoop
from labscriptai.agent.registry import build_default_registry
from labscriptai.agent.state import AgentState, PackageRef, TaskSpec
from labscriptai.agent.tools import ToolResult
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.runtime.state import RuntimeState
from labscriptai.runtime.trace import TraceWriter
from tests.test_package_validator import write_valid_package


class ScriptedClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(self, messages, tools):
        del messages, tools
        self.input_tokens += 1
        self.output_tokens += 1
        self.total_tokens += 2
        return next(self.responses)


def _author_task() -> AuthoringTask:
    return AuthoringTask(
        task_id="T999",
        source="test",
        difficulty="Easy",
        holdout=False,
        output_contract="execution_package",
        prompt="Create a simple package.",
    )


def test_author_smoke_validates_and_simulates(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    write_valid_package(package_dir)
    state = AgentState.for_author(
        task=_author_task(),
        package_dir=package_dir,
        trace_path=tmp_path / "trace.jsonl",
        permissions=_author_permissions("light", "kb"),
    )
    client = ScriptedClient(
        [
            {
                "tool_calls": [
                    {"name": "validate_package", "arguments": {"simulation_pass": True}},
                    {"name": "run_simulate", "arguments": {}},
                ]
            },
            {"final": {"package_ready": True}},
        ]
    )
    registry = build_default_registry(tool_profile="kb", simulation_timeout_sec=1)
    with patch(
        "labscriptai.authoring.tools.registry.AuthoringToolRegistry._run_simulate",
        return_value=ToolResult(True, "package.simulate", {"returncode": 0}),
    ):
        result = LabscriptAgentLoop(client=client, registry=registry, max_steps=3).run(state)

    events = [
        json.loads(line)
        for line in (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    tool_results = [event for event in events if event["event_type"] == "tool_result"]
    assert result.completed is True
    assert result.final_state.package_ready is True
    assert [event["payload"]["name"] for event in tool_results] == [
        "package.validate",
        "package.simulate",
    ]


class FakeRobotAdapter:
    def __init__(self, *, host: str, port=None) -> None:
        self.host = host
        self.port = port

    def snapshot(self, *, run_id=None):
        return {"robot_health": {"robot_serial": "FLX-1"}, "run_history": {"status": "running"}}

    def state_from_snapshot(self, *, run_id: str, snapshot):
        return RuntimeState(
            run_id=run_id,
            phase="running",
            robot={"host": self.host, "id": "FLX-1"},
            observed=snapshot,
        )


def test_run_smoke_inspect_and_parse(tmp_path: Path) -> None:
    state = AgentState(
        run_id="run-1",
        mode="run",
        phase="preflight",
        task_spec=TaskSpec(task_id="R001", prompt="inspect"),
        package=PackageRef.from_dir(tmp_path / "package"),
        trace_path=tmp_path / "trace.jsonl",
        trace=TraceWriter(tmp_path / "trace.jsonl"),
        permissions=frozenset(),
        robot_status={"host": "127.0.0.1"},
    )
    client = ScriptedClient(
        [
            {
                "tool_calls": [
                    {"name": "robot.inspect", "arguments": {"source": "http", "host": "127.0.0.1"}},
                    {"name": "error.parse", "arguments": {"raw_error": "missing tip"}},
                ]
            },
            {"final": {"completed": False}},
        ]
    )
    registry = build_default_registry(robot_adapter_factory=FakeRobotAdapter)
    result = LabscriptAgentLoop(client=client, registry=registry, max_steps=2).run(state)

    assert result.final_state.robot_status["id"] == "FLX-1"
    assert result.final_state.latest_error is not None
    assert result.final_state.latest_error.raw == "missing tip"


def test_gatekeeper_blocks_run_control_in_author_mode(tmp_path: Path) -> None:
    state = AgentState.for_author(
        task=_author_task(),
        package_dir=tmp_path / "package",
        trace_path=tmp_path / "trace.jsonl",
        permissions=_author_permissions("light", "kb"),
    )
    invoked = Mock()
    client = ScriptedClient(
        [
            {
                "tool_calls": [
                    {
                        "name": "run.control",
                        "reason": "abort from author mode",
                        "arguments": {"action_type": "abort_run"},
                    }
                ]
            }
        ]
    )
    registry = build_default_registry()
    registry._handlers["run.control"] = invoked
    loop = LabscriptAgentLoop(client=client, registry=registry, max_steps=1)
    result = loop.run(state)

    assert loop.last_tool_results[-1].ok is False
    assert loop.last_tool_results[-1].decision is not None
    assert loop.last_tool_results[-1].decision.blocked is True
    invoked.assert_not_called()
    assert result.completed is False


def test_trace_dump_complete(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    write_valid_package(package_dir)
    state = AgentState.for_author(
        task=_author_task(),
        package_dir=package_dir,
        trace_path=tmp_path / "trace.jsonl",
        permissions=_author_permissions("light", "kb"),
    )
    client = ScriptedClient(
        [
            {"tool_calls": [{"name": "validate_package", "arguments": {"simulation_pass": True}}]},
            {"final": {"package_ready": True}},
        ]
    )
    result = LabscriptAgentLoop(
        client=client,
        registry=build_default_registry(tool_profile="kb"),
        max_steps=2,
    ).run(state)

    assert result.completed is True
    path = tmp_path / "trace.jsonl"
    assert path.exists()
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    event_types = {event["event_type"] for event in events}
    assert {
        "state_update",
        "candidate_tool_call",
        "gatekeeper_decision",
        "tool_result",
        "summary",
    }.issubset(event_types)
