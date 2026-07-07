"""Persistent recovery attempt queue with idempotency and retry budgets."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _coerce_utc(value: datetime | str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = value
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utc_now(now: datetime | str | None = None) -> str:
    return _coerce_utc(now).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RecoveryAttempt:
    attempt_id: str
    run_id: str
    failed_command_id: str
    error_leaf: str
    branch: str
    idempotency_key: str
    status: str = "queued"
    started_at: str = field(default_factory=_utc_now)
    finished_at: str | None = None
    gatekeeper_status: str = ""
    result: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "run_id": self.run_id,
            "failed_command_id": self.failed_command_id,
            "error_leaf": self.error_leaf,
            "branch": self.branch,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "gatekeeper_status": self.gatekeeper_status,
            "result": dict(self.result),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RecoveryAttempt:
        return cls(
            attempt_id=str(payload["attempt_id"]),
            run_id=str(payload["run_id"]),
            failed_command_id=str(payload.get("failed_command_id") or ""),
            error_leaf=str(payload.get("error_leaf") or "UNKNOWN_NEEDS_HUMAN"),
            branch=str(payload.get("branch") or ""),
            idempotency_key=str(payload["idempotency_key"]),
            status=str(payload.get("status") or "queued"),
            started_at=str(payload.get("started_at") or _utc_now()),
            finished_at=payload.get("finished_at"),
            gatekeeper_status=str(payload.get("gatekeeper_status") or ""),
            result=dict(payload.get("result") or {}),
        )


@dataclass
class RecoveryQueue:
    checkpoint_path: Path
    max_attempts_per_failed_command: int = 3
    stale_running_after_sec: int = 1800
    attempts: list[RecoveryAttempt] = field(default_factory=list)

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        max_attempts_per_failed_command: int = 3,
        stale_running_after_sec: int = 1800,
    ) -> RecoveryQueue:
        if not path.exists():
            return cls(
                path,
                max_attempts_per_failed_command=max_attempts_per_failed_command,
                stale_running_after_sec=stale_running_after_sec,
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            checkpoint_path=path,
            max_attempts_per_failed_command=max_attempts_per_failed_command,
            stale_running_after_sec=stale_running_after_sec,
            attempts=[RecoveryAttempt.from_mapping(item) for item in payload.get("attempts", [])],
        )

    def save(self) -> None:
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.write_text(
            json.dumps(
                {"schema_version": "0.1", "attempts": [attempt.to_dict() for attempt in self.attempts]},
                indent=2,
            ),
            encoding="utf-8",
        )

    def reap_stale(self, *, now: datetime | str | None = None) -> list[RecoveryAttempt]:
        now_dt = _coerce_utc(now)
        stale_after = max(0, self.stale_running_after_sec)
        updated: list[RecoveryAttempt] = []
        reaped: list[RecoveryAttempt] = []
        for attempt in self.attempts:
            if attempt.status == "running":
                try:
                    started_at = _coerce_utc(attempt.started_at)
                except ValueError:
                    started_at = now_dt
                if (now_dt - started_at).total_seconds() >= stale_after:
                    attempt = RecoveryAttempt(
                        **{
                            **attempt.to_dict(),
                            "status": "failed",
                            "finished_at": _utc_now(now_dt),
                            "result": {"result": "stale_running_reaped"},
                        }
                    )
                    reaped.append(attempt)
            updated.append(attempt)
        if reaped:
            self.attempts = updated
            self.save()
        return reaped

    def can_attempt(
        self,
        *,
        run_id: str,
        failed_command_id: str,
        branch: str,
        now: datetime | str | None = None,
    ) -> tuple[bool, tuple[str, ...]]:
        self.reap_stale(now=now)
        matching = [
            attempt
            for attempt in self.attempts
            if attempt.run_id == run_id
            and attempt.failed_command_id == failed_command_id
            and attempt.branch == branch
        ]
        if len(matching) >= self.max_attempts_per_failed_command:
            return False, (f"retry budget exhausted for {failed_command_id}:{branch}",)
        if any(attempt.status == "running" for attempt in matching):
            return False, (f"attempt already running for {failed_command_id}:{branch}",)
        return True, ()

    def begin_attempt(
        self,
        *,
        run_id: str,
        failed_command_id: str,
        error_leaf: str,
        branch: str,
        gatekeeper_status: str,
    ) -> RecoveryAttempt:
        index = (
            sum(
                1
                for attempt in self.attempts
                if attempt.run_id == run_id
                and attempt.failed_command_id == failed_command_id
                and attempt.branch == branch
            )
            + 1
        )
        raw_key = f"{run_id}:{failed_command_id}:{branch}:{index}"
        attempt = RecoveryAttempt(
            attempt_id=str(uuid.uuid4()),
            run_id=run_id,
            failed_command_id=failed_command_id,
            error_leaf=error_leaf,
            branch=branch,
            idempotency_key=hashlib.sha256(raw_key.encode()).hexdigest()[:24],
            status="running",
            gatekeeper_status=gatekeeper_status,
        )
        self.attempts.append(attempt)
        self.save()
        return attempt

    def finish_attempt(self, attempt_id: str, *, status: str, result: Mapping[str, Any]) -> None:
        updated: list[RecoveryAttempt] = []
        for attempt in self.attempts:
            if attempt.attempt_id == attempt_id:
                attempt = RecoveryAttempt(
                    **{
                        **attempt.to_dict(),
                        "status": status,
                        "finished_at": _utc_now(),
                        "result": dict(result),
                    }
                )
            updated.append(attempt)
        self.attempts = updated
        self.save()
