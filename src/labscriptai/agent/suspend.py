"""HITL suspend/resume snapshots for LabscriptAgentLoop."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.state import AgentState, Counters, ErrorRef, PackageRef, TaskSpec
from labscriptai.agent.tools import ToolCall
from labscriptai.runtime.memory import MemoryHit
from labscriptai.runtime.state import RuntimeRisk
from labscriptai.runtime.trace import TraceWriter


@dataclass(frozen=True)
class SuspendedLoopSnapshot:
    suspend_id: str
    state_payload: Mapping[str, Any]
    messages: list[dict[str, Any]]
    pending_call: Mapping[str, Any]
    steps_remaining: int
    initial_messages: list[dict[str, Any]] | None = None
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "suspend_id": self.suspend_id,
            "state_payload": dict(self.state_payload),
            "messages": list(self.messages),
            "pending_call": dict(self.pending_call),
            "steps_remaining": self.steps_remaining,
            "initial_messages": list(self.initial_messages) if self.initial_messages is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SuspendedLoopSnapshot":
        initial = payload.get("initial_messages")
        return cls(
            suspend_id=str(payload["suspend_id"]),
            state_payload=dict(payload["state_payload"]),
            messages=[dict(item) for item in payload.get("messages") or []],
            pending_call=dict(payload["pending_call"]),
            steps_remaining=int(payload["steps_remaining"]),
            initial_messages=[dict(item) for item in initial] if isinstance(initial, list) else None,
            schema_version=str(payload.get("schema_version", "1.0")),
        )


class SuspendStore:
    """In-memory suspend registry with optional JSON persistence."""

    def __init__(self) -> None:
        self._by_id: dict[str, SuspendedLoopSnapshot] = {}

    def save(self, snapshot: SuspendedLoopSnapshot, *, persist_dir: Path | None = None) -> str:
        self._by_id[snapshot.suspend_id] = snapshot
        if persist_dir is not None:
            persist_dir.mkdir(parents=True, exist_ok=True)
            path = persist_dir / f"{snapshot.suspend_id}.json"
            path.write_text(
                json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        return snapshot.suspend_id

    def load(self, suspend_id: str, *, persist_dir: Path | None = None) -> SuspendedLoopSnapshot:
        cached = self._by_id.get(suspend_id)
        if cached is not None:
            return cached
        if persist_dir is not None:
            path = persist_dir / f"{suspend_id}.json"
            if path.exists():
                snapshot = SuspendedLoopSnapshot.from_dict(
                    json.loads(path.read_text(encoding="utf-8"))
                )
                self._by_id[suspend_id] = snapshot
                return snapshot
        raise KeyError(f"suspended loop not found: {suspend_id}")

    def pop(self, suspend_id: str, *, persist_dir: Path | None = None) -> SuspendedLoopSnapshot:
        snapshot = self.load(suspend_id, persist_dir=persist_dir)
        self._by_id.pop(suspend_id, None)
        if persist_dir is not None:
            path = persist_dir / f"{suspend_id}.json"
            if path.exists():
                path.unlink()
        return snapshot


def new_suspend_id(*, run_id: str) -> str:
    return f"{run_id}-suspend-{uuid.uuid4().hex[:12]}"


def serialize_agent_state(state: AgentState) -> dict[str, Any]:
    return state.to_dict()


def deserialize_agent_state(payload: Mapping[str, Any]) -> AgentState:
    task_spec_payload = dict(payload.get("task_spec") or {})
    package_payload = dict(payload.get("package") or {})
    counters_payload = dict(payload.get("counters") or {})
    latest_error_payload = payload.get("latest_error")
    trace_path = Path(str(payload.get("trace_path") or "trace.jsonl"))
    memory_hits = tuple(
        MemoryHit(
            path=Path(str(item.get("path", ""))),
            title=str(item.get("title", "")),
            score=int(item.get("score", 0)),
            preview=str(item.get("preview", "")),
        )
        for item in payload.get("memory_hits") or ()
    )
    return AgentState(
        run_id=str(payload["run_id"]),
        mode=str(payload["mode"]),  # type: ignore[arg-type]
        task_spec=TaskSpec(
            task_id=str(task_spec_payload.get("task_id", payload.get("task_id", ""))),
            prompt=str(task_spec_payload.get("prompt", "")),
            difficulty=task_spec_payload.get("difficulty"),
            required_files=tuple(str(name) for name in task_spec_payload.get("required_files") or ()),
            budget=dict(task_spec_payload.get("budget") or {}),
            autonomy_mode=str(task_spec_payload.get("autonomy_mode", "conservative")),
        ),
        package=PackageRef(
            dir=Path(str(package_payload.get("dir", "."))),
            files_present=tuple(str(name) for name in package_payload.get("files_present") or ()),
            manifest_digest=package_payload.get("manifest_digest"),
            last_validation=package_payload.get("last_validation"),
        ),
        trace_path=trace_path,
        trace=TraceWriter(trace_path),
        schema_version=str(payload.get("schema_version", "1.0")),
        phase=str(payload.get("phase", "preflight")),
        package_ready=bool(payload.get("package_ready", False)),
        robot_status=dict(payload.get("robot_status") or {}),
        run_status=dict(payload.get("run_status") or {}),
        latest_error=(
            ErrorRef(
                category=str(latest_error_payload.get("category", "")),
                code=latest_error_payload.get("code"),
                raw=latest_error_payload.get("raw"),
                parsed=latest_error_payload.get("parsed"),
                source=latest_error_payload.get("source", "tool"),  # type: ignore[arg-type]
            )
            if isinstance(latest_error_payload, Mapping)
            else None
        ),
        loaded_skills=tuple(str(name) for name in payload.get("loaded_skills") or ()),
        memory_hits=memory_hits,
        permissions=frozenset(str(item) for item in payload.get("permissions") or ()),
        risks=tuple(RuntimeRisk.from_mapping(item) for item in payload.get("risks") or ()),
        counters=Counters(**{name: int(counters_payload.get(name, 0)) for name in Counters.__dataclass_fields__}),
    )


def serialize_tool_call(call: ToolCall) -> dict[str, Any]:
    return call.to_dict()


def deserialize_tool_call(payload: Mapping[str, Any]) -> ToolCall:
    return ToolCall(
        name=payload["name"],  # type: ignore[arg-type]
        arguments=dict(payload.get("arguments") or {}),
        reason=str(payload.get("reason", "")),
        proposed_by=str(payload.get("proposed_by", "model")),
        call_id=payload.get("call_id"),
    )
