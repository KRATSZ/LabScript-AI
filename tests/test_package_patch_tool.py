from __future__ import annotations

import json
from pathlib import Path

from labscriptai.agent.registry import build_default_registry
from labscriptai.agent.state import AgentState, PackageRef, TaskSpec
from labscriptai.agent.tools import ToolCall
from labscriptai.authoring.task_state import AuthoringTaskState
from labscriptai.authoring.tools.registry import AuthoringToolRegistry
from labscriptai.web.streamer import (
    SSE_CONTENT_TYPE,
    format_sse_event,
    stream_trace_events,
    trace_event_to_sse,
)
from labscriptai.runtime.trace import TraceEvent, TraceWriter


def test_apply_patch_legacy_name_maps_to_package_patch() -> None:
    call = ToolCall.from_model(
        {
            "name": "apply_patch",
            "arguments": {
                "path": "protocol.py",
                "diff": "------- SEARCH\nold()\n=======\nnew()\n+++++++ REPLACE\n",
            },
        }
    )
    assert call.name == "package.patch"
    assert call.arguments["path"] == "protocol.py"


def test_authoring_registry_apply_patch_updates_file(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    protocol_path = package_dir / "protocol.py"
    protocol_path.write_text("alpha\nold()\nomega\n", encoding="utf-8")
    registry = AuthoringToolRegistry(
        package_dir=package_dir,
        state=AuthoringTaskState(run_id="run-1", task_id="T001"),
    )

    result = registry.call(
        "apply_patch",
        {
            "path": "protocol.py",
            "diff": "------- SEARCH\nold()\n=======\nnew()\n+++++++ REPLACE\n",
            "reason": "repair simulation failure",
        },
    )

    assert result.ok
    assert protocol_path.read_text(encoding="utf-8") == "alpha\nnew()\nomega\n"
    assert result.content["applied_count"] == 1
    log_entries = [
        json.loads(line)
        for line in (package_dir / "authoring_patch_log.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert log_entries[-1]["tool"] == "apply_patch"


def test_unified_registry_package_patch(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    protocol_path = package_dir / "protocol.py"
    protocol_path.write_text("alpha\nold()\nomega\n", encoding="utf-8")
    state = AgentState(
        run_id="run-1",
        mode="author",
        phase="drafting",
        task_spec=TaskSpec(task_id="T001", prompt="repair"),
        package=PackageRef.from_dir(package_dir),
        trace_path=tmp_path / "trace.jsonl",
        trace=TraceWriter(tmp_path / "trace.jsonl"),
        permissions=frozenset({"package.read_write"}),
    )
    registry = build_default_registry(tool_profile="edit", skill_mode="off")
    result = registry.call_with_gating(
        ToolCall(
            name="package.patch",
            arguments={
                "path": "protocol.py",
                "diff": "------- SEARCH\nold()\n=======\nnew()\n+++++++ REPLACE\n",
            },
        ),
        state,
    )

    assert result.ok
    assert protocol_path.read_text(encoding="utf-8") == "alpha\nnew()\nomega\n"


def test_author_mode_tool_specs_expose_apply_patch_not_str_replace() -> None:
    registry = build_default_registry(tool_profile="edit", skill_mode="off")
    names = {spec["name"] for spec in registry.list_specs(mode="author")}

    assert "apply_patch" in names
    assert "str_replace" not in names


def test_trace_event_to_sse_formats_state_update_and_tool_result() -> None:
    state_event = TraceEvent(
        run_id="run-1",
        event_type="state_update",
        actor="system",
        payload={"phase": "drafting"},
    )
    tool_event = TraceEvent(
        run_id="run-1",
        event_type="tool_result",
        actor="tool",
        payload={"name": "package.patch", "ok": True},
    )

    state_sse = trace_event_to_sse(state_event)
    tool_sse = trace_event_to_sse(tool_event)

    assert "event: state_update\n" in state_sse
    assert '"event_type": "state_update"' in state_sse
    assert f"id: {state_event.event_id}\n" in state_sse
    assert "event: tool_result\n" in tool_sse
    assert '"name": "package.patch"' in tool_sse


def test_stream_trace_events_yields_multiple_frames() -> None:
    events = [
        TraceEvent(run_id="run-1", event_type="state_update", actor="system", payload={"step": 1}),
        TraceEvent(run_id="run-1", event_type="tool_result", actor="tool", payload={"ok": True}),
    ]
    frames = list(stream_trace_events(iter(events)))

    assert len(frames) == 2
    assert all(frame.endswith("\n\n") for frame in frames)


def test_format_sse_event_contract() -> None:
    frame = format_sse_event(event="state_update", data={"hello": "world"}, event_id="evt-1")

    assert frame.startswith("id: evt-1\n")
    assert "event: state_update\n" in frame
    assert 'data: {"hello": "world"}' in frame
    assert SSE_CONTENT_TYPE == "text/event-stream"
