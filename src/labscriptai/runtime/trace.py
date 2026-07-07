"""Trace event writer for LabscriptAI runtime evidence."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .state import RuntimeState

TRACE_EVENT_TYPES = frozenset(
    {
        "observation",
        "state_update",
        "memory_retrieval",
        "candidate_action",
        "candidate_tool_call",
        "gatekeeper_decision",
        "tool_call",
        "tool_result",
        "runtime_event",
        "recovery",
        "escalation",
        "summary",
    }
)

TRACE_ACTORS = frozenset(
    {"system", "model", "gatekeeper", "tool", "human", "Planner", "Coder", "Reviewer"}
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TraceEvent:
    run_id: str
    event_type: str
    actor: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state_hash: str | None = None

    def __post_init__(self) -> None:
        if self.event_type not in TRACE_EVENT_TYPES:
            raise ValueError(f"invalid trace event type: {self.event_type}")
        if self.actor not in TRACE_ACTORS:
            raise ValueError(f"invalid trace actor: {self.actor}")
        if not self.run_id:
            raise ValueError("trace event run_id is required")

    @classmethod
    def for_state(
        cls,
        state: RuntimeState,
        *,
        event_type: str,
        actor: str,
        payload: Mapping[str, Any] | None = None,
    ) -> "TraceEvent":
        return cls(
            run_id=state.run_id,
            event_type=event_type,
            actor=actor,
            payload=payload or {},
            state_hash=state.stable_hash(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "payload": dict(self.payload),
            "state_hash": self.state_hash,
        }


class TraceWriter:
    """Append-only JSONL trace writer."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, event: TraceEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def read_events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
