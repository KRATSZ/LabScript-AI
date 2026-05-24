"""HTTP polling watcher for runtime events."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .chat_controller import ChatResponse
from .events import RuntimeEvent, RuntimeEventClassifier
from .state import RuntimeState
from .trace import TraceEvent, TraceWriter

WakeHandler = Callable[[str, str], ChatResponse]


@dataclass(frozen=True)
class PollResult:
    events: tuple[RuntimeEvent, ...]
    responses: tuple[ChatResponse, ...] = ()


class RuntimePoller:
    def __init__(
        self,
        *,
        adapter: Any,
        run_id: str,
        trace_path: str,
        classifier: RuntimeEventClassifier | None = None,
        wake_handler: WakeHandler | None = None,
        initial_state: RuntimeState | None = None,
    ) -> None:
        self.adapter = adapter
        self.run_id = run_id
        self.writer = TraceWriter(trace_path)
        self.classifier = classifier or RuntimeEventClassifier()
        self.wake_handler = wake_handler
        self.previous_snapshot: Mapping[str, Any] | None = None
        self.previous_state: RuntimeState | None = initial_state
        self.state: RuntimeState = initial_state or RuntimeState(run_id=run_id, phase="preflight")
        self.last_responses: tuple[ChatResponse, ...] = ()

    def poll_once(self) -> list[RuntimeEvent]:
        return list(self.poll_and_wake().events)

    def poll_and_wake(self) -> PollResult:
        try:
            snapshot = self.adapter.snapshot(run_id=self.run_id)
            current_state = self.adapter.state_from_snapshot(run_id=self.run_id, snapshot=snapshot)
        except Exception as exc:  # pragma: no cover - defensive live boundary
            events = self.classifier.classify_poll_error(exc, run_id=self.run_id, current_state=self.state)
            events = [self.classifier.mark_wake_allowed(event) for event in events]
            self._write_events(events, state=self.state)
            responses = self._wake(events)
            self.last_responses = tuple(responses)
            return PollResult(tuple(events), tuple(responses))

        self.writer.append(
            TraceEvent.for_state(
                current_state,
                event_type="observation",
                actor="system",
                payload={"source": "robot_http_poll", "snapshot": _summarize_snapshot(snapshot)},
            )
        )
        events = self.classifier.classify(
            self.previous_snapshot,
            snapshot,
            self.previous_state,
            current_state,
        )
        events = [self.classifier.mark_wake_allowed(event) for event in events]
        self._write_events(events, state=current_state)
        responses = self._wake(events)
        self.previous_snapshot = snapshot
        self.previous_state = current_state
        self.state = current_state
        self.last_responses = tuple(responses)
        return PollResult(tuple(events), tuple(responses))

    def consume_responses(self) -> tuple[ChatResponse, ...]:
        responses = self.last_responses
        self.last_responses = ()
        return responses

    def interval_sec(self) -> float:
        if self.state.phase in {"running"}:
            return 10.0
        if self.state.phase in {"recovering", "failed"}:
            return 5.0
        return 60.0

    def _write_events(self, events: list[RuntimeEvent], *, state: RuntimeState) -> None:
        for event in events:
            self.writer.append(
                TraceEvent.for_state(
                    state,
                    event_type="runtime_event",
                    actor="system",
                    payload=event.to_dict(),
                )
            )

    def _wake(self, events: list[RuntimeEvent]) -> list[ChatResponse]:
        if self.wake_handler is None:
            return []
        for event in events:
            if event.should_wake_model and event.suggested_prompt:
                return [self.wake_handler(event.suggested_prompt, "en")]
        return []


def _summarize_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), Mapping) else {}
    health = snapshot.get("robot_health") if isinstance(snapshot.get("robot_health"), Mapping) else {}
    return {
        "robot": health.get("robot_serial") or health.get("robotSerial") or health.get("error"),
        "run_id": history.get("run_id"),
        "status": history.get("status"),
        "awaiting_recovery": history.get("awaiting_recovery"),
        "completed_count": len(history.get("completed_commands") or ()),
        "failed_count": len(history.get("failed_commands") or ()),
    }
