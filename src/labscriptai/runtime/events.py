"""Runtime event classification for polling-driven run monitoring."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .state import RuntimeState


@dataclass(frozen=True)
class RuntimeEvent:
    run_id: str
    kind: str
    severity: str
    source: str
    message: str
    snapshot_summary: Mapping[str, Any] = field(default_factory=dict)
    diff: Mapping[str, Any] = field(default_factory=dict)
    should_wake_model: bool = False
    suggested_prompt: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "kind": self.kind,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "snapshot_summary": dict(self.snapshot_summary),
            "diff": dict(self.diff),
            "should_wake_model": self.should_wake_model,
            "suggested_prompt": self.suggested_prompt,
        }


class RuntimeEventClassifier:
    """Classify cheap HTTP polling observations before waking the model."""

    def __init__(
        self,
        *,
        now: Callable[[], float] | None = None,
        robot_unreachable_threshold: int = 3,
        wake_cooldown_sec: float = 60.0,
    ) -> None:
        self.now = now or time.monotonic
        self.robot_unreachable_threshold = robot_unreachable_threshold
        self.wake_cooldown_sec = wake_cooldown_sec
        self._consecutive_poll_errors = 0
        self._last_wake_by_key: dict[tuple[str, str], float] = {}

    def classify(
        self,
        previous_snapshot: Mapping[str, Any] | None,
        current_snapshot: Mapping[str, Any],
        previous_state: RuntimeState | None,
        current_state: RuntimeState,
    ) -> list[RuntimeEvent]:
        if _snapshot_has_error(current_snapshot):
            return self.classify_poll_error(
                current_snapshot,
                run_id=current_state.run_id,
                current_state=current_state,
            )
        self._consecutive_poll_errors = 0
        if previous_snapshot is None or previous_state is None:
            return []

        events: list[RuntimeEvent] = []
        previous_status = _status(previous_snapshot, previous_state)
        current_status = _status(current_snapshot, current_state)
        summary = _snapshot_summary(current_snapshot, current_state)
        diff = {
            "previous_status": previous_status,
            "current_status": current_status,
            "previous_completed_count": len(previous_state.completed_commands),
            "current_completed_count": len(current_state.completed_commands),
            "previous_failed_count": len(previous_state.failed_commands),
            "current_failed_count": len(current_state.failed_commands),
        }

        new_failed = _new_failed_commands(previous_state, current_state)
        if new_failed:
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="command_failed",
                    severity="error",
                    source="robot_http",
                    message="A new failed robot command was detected.",
                    summary=summary,
                    diff={**diff, "failed_commands": new_failed},
                    wake=True,
                )
            )

        if current_status == "awaiting-recovery":
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="awaiting_recovery",
                    severity="error",
                    source="robot_http",
                    message="The run is awaiting recovery.",
                    summary=summary,
                    diff=diff,
                    wake=True,
                )
            )
        elif current_status == "failed":
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="unknown_anomaly",
                    severity="error",
                    source="robot_http",
                    message="The run failed.",
                    summary=summary,
                    diff=diff,
                    wake=True,
                )
            )
        elif previous_status != current_status and current_status == "succeeded":
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="run_completed",
                    severity="info",
                    source="robot_http",
                    message="The run completed successfully.",
                    summary=summary,
                    diff=diff,
                    wake=False,
                )
            )
        elif previous_status != current_status:
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="run_status_changed",
                    severity="info",
                    source="robot_http",
                    message=f"Run status changed from {previous_status or 'unknown'} to {current_status or 'unknown'}.",
                    summary=summary,
                    diff=diff,
                    wake=False,
                )
            )
        elif len(current_state.completed_commands) > len(previous_state.completed_commands):
            events.append(
                self._event(
                    run_id=current_state.run_id,
                    kind="normal_progress",
                    severity="info",
                    source="robot_http",
                    message="The run made normal command progress.",
                    summary=summary,
                    diff=diff,
                    wake=False,
                )
            )
        return events

    def classify_poll_error(
        self,
        error_payload: Mapping[str, Any] | Exception,
        *,
        run_id: str,
        current_state: RuntimeState | None = None,
    ) -> list[RuntimeEvent]:
        self._consecutive_poll_errors += 1
        if self._consecutive_poll_errors < self.robot_unreachable_threshold:
            return []
        state = current_state or RuntimeState(run_id=run_id, phase="preflight")
        return [
            self._event(
                run_id=run_id,
                kind="robot_unreachable",
                severity="error",
                source="robot_http",
                message="Robot HTTP polling failed repeatedly.",
                summary={"run_id": run_id, "phase": state.phase},
                diff={"consecutive_poll_errors": self._consecutive_poll_errors, "error": str(error_payload)},
                wake=True,
            )
        ]

    def mark_wake_allowed(self, event: RuntimeEvent) -> RuntimeEvent:
        if not event.should_wake_model:
            return event
        key = (event.kind, str(event.diff))
        now = self.now()
        last = self._last_wake_by_key.get(key)
        if last is not None and now - last < self.wake_cooldown_sec:
            return RuntimeEvent(
                run_id=event.run_id,
                kind=event.kind,
                severity=event.severity,
                source=event.source,
                message=event.message,
                snapshot_summary=event.snapshot_summary,
                diff=event.diff,
                should_wake_model=False,
                suggested_prompt=event.suggested_prompt,
                event_id=event.event_id,
            )
        self._last_wake_by_key[key] = now
        return event

    def _event(
        self,
        *,
        run_id: str,
        kind: str,
        severity: str,
        source: str,
        message: str,
        summary: Mapping[str, Any],
        diff: Mapping[str, Any],
        wake: bool,
    ) -> RuntimeEvent:
        prompt = ""
        if wake:
            prompt = (
                "Runtime event detected:\n"
                f"kind={kind}\n"
                f"severity={severity}\n"
                f"run_id={run_id}\n"
                f"summary={dict(summary)}\n"
                f"diff={dict(diff)}\n"
                "Please inspect status, explain the issue, and propose the safest next step.\n"
                "Do not execute recovery unless allowed by gatekeeper and operator confirmation rules."
            )
        return RuntimeEvent(
            run_id=run_id,
            kind=kind,
            severity=severity,
            source=source,
            message=message,
            snapshot_summary=summary,
            diff=diff,
            should_wake_model=wake,
            suggested_prompt=prompt,
        )


def _snapshot_has_error(snapshot: Mapping[str, Any]) -> bool:
    if snapshot.get("poll_error"):
        return True
    health = snapshot.get("robot_health")
    return isinstance(health, Mapping) and bool(health.get("error"))


def _status(snapshot: Mapping[str, Any], state: RuntimeState) -> str:
    history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), Mapping) else {}
    value = history.get("status") if isinstance(history, Mapping) else None
    return str(value or state.phase or "")


def _snapshot_summary(snapshot: Mapping[str, Any], state: RuntimeState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "phase": state.phase,
        "robot": state.robot.get("id") or state.robot.get("serial") or state.robot.get("host"),
        "status": _status(snapshot, state),
        "completed_count": len(state.completed_commands),
        "failed_count": len(state.failed_commands),
    }


def _new_failed_commands(previous_state: RuntimeState, current_state: RuntimeState) -> list[dict[str, Any]]:
    previous_ids = {_command_key(command) for command in previous_state.failed_commands}
    return [
        dict(command)
        for command in current_state.failed_commands
        if _command_key(command) not in previous_ids
    ]


def _command_key(command: Mapping[str, Any]) -> str:
    return str(command.get("id") or command.get("key") or command)
