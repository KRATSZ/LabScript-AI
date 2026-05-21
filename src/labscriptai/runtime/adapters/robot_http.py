"""Read-only Opentrons robot HTTP adapter for runtime state snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..continuation import build_ledger_from_run_history
from ..state import RuntimeState


@dataclass(frozen=True)
class RobotHttpConfig:
    host: str
    port: int | None = None
    token: str | None = None
    timeout_sec: float = 10.0

    @property
    def base_url(self) -> str:
        host = self.host
        if host.startswith("http://") or host.startswith("https://"):
            base = host.rstrip("/")
        else:
            base = f"http://{host}"
        if self.port is not None and ":" not in base.rsplit("/", 1)[-1]:
            base = f"{base}:{self.port}"
        return base


class RobotHttpReadOnlyAdapter:
    """Small HTTP client that only reads robot state."""

    def __init__(self, config: RobotHttpConfig) -> None:
        self.config = config

    def snapshot(self, *, run_id: str | None = None) -> dict[str, Any]:
        health = self._get("/health")
        modules = self._get("/modules")
        runs = self._get("/runs", {"pageLength": 20})
        selected_run_id = run_id or _first_run_id(runs)
        run = self._get(f"/runs/{selected_run_id}") if selected_run_id else {}
        commands = (
            self._get(f"/runs/{selected_run_id}/commands", {"pageLength": 500})
            if selected_run_id
            else {}
        )
        return {
            "robot_health": _unwrap(health),
            "modules": _unwrap(modules),
            "runs": _unwrap(runs),
            "run": _unwrap(run),
            "commands": _unwrap(commands),
            "run_history": _run_history(_unwrap(run), _unwrap(commands)),
        }

    def list_runs(self, *, page_length: int = 20) -> list[dict[str, Any]]:
        runs = _unwrap(self._get("/runs", {"pageLength": page_length}))
        if not isinstance(runs, list):
            return []
        return [dict(run) for run in runs if isinstance(run, Mapping)]

    def state_from_snapshot(self, *, run_id: str, snapshot: Mapping[str, Any]) -> RuntimeState:
        robot_health = snapshot.get("robot_health") if isinstance(snapshot.get("robot_health"), Mapping) else {}
        run_history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), Mapping) else {}
        ledger = build_ledger_from_run_history(run_history)
        phase = _phase_from_run_status(str(run_history.get("status") or "preflight"))
        return RuntimeState(
            run_id=run_id,
            phase=phase,
            robot={
                "host": self.config.host,
                "id": robot_health.get("robot_serial") or robot_health.get("robotSerial"),
                "model": robot_health.get("robot_model") or robot_health.get("robotModel"),
            },
            observed=dict(snapshot),
            completed_commands=tuple(ledger["completed_commands"]),
            failed_commands=tuple(ledger["failed_commands"]),
            remaining_plan=tuple(ledger["remaining_plan"]),
        )

    def _get(self, path: str, query: Mapping[str, Any] | None = None) -> dict[str, Any]:
        suffix = path
        if query:
            suffix = f"{suffix}?{urlencode(query)}"
        request = Request(f"{self.config.base_url}{suffix}", method="GET")
        request.add_header("Opentrons-Version", "3")
        if self.config.token:
            request.add_header("Authorization", f"Bearer {self.config.token}")
        try:
            with urlopen(request, timeout=self.config.timeout_sec) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            return {"error": f"HTTPError: {exc.code}", "path": path}
        except URLError as exc:
            return {"error": f"URLError: {exc.reason}", "path": path}
        if not body.strip():
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body}


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, Mapping) and "data" in payload:
        return payload["data"]
    return payload


def _first_run_id(runs_payload: Mapping[str, Any]) -> str | None:
    runs = _unwrap(runs_payload)
    if isinstance(runs, list) and runs:
        first = runs[0]
        if isinstance(first, Mapping):
            value = first.get("id")
            return str(value) if value else None
    return None


def _run_history(run: Any, commands: Any) -> dict[str, Any]:
    run_obj = run if isinstance(run, Mapping) else {}
    command_items = commands if isinstance(commands, list) else []
    latest_failed = next(
        (
            dict(command)
            for command in reversed(command_items)
            if isinstance(command, Mapping) and command.get("status") == "failed"
        ),
        None,
    )
    return {
        "run_id": run_obj.get("id"),
        "status": run_obj.get("status"),
        "awaiting_recovery": run_obj.get("status") == "awaiting-recovery"
        or bool(run_obj.get("currentlyRecoveringFrom")),
        "latest_failed_command": latest_failed,
        "completed_commands": [
            dict(item)
            for item in command_items
            if isinstance(item, Mapping) and item.get("status") == "succeeded"
        ],
        "failed_commands": [
            dict(item)
            for item in command_items
            if isinstance(item, Mapping) and item.get("status") == "failed"
        ],
        "remaining_plan": [
            dict(item)
            for item in command_items
            if isinstance(item, Mapping) and item.get("status") in {"queued", "running"}
        ],
        "run_errors": [dict(item) for item in run_obj.get("errors", []) if isinstance(item, Mapping)]
        if isinstance(run_obj.get("errors"), list)
        else [],
        "recent_commands": [dict(item) for item in command_items if isinstance(item, Mapping)][-20:],
    }


def _phase_from_run_status(status: str) -> str:
    normalized = status.lower()
    if normalized in {"running"}:
        return "running"
    if normalized in {"paused", "idle", "stopped"}:
        return "paused"
    if normalized in {"awaiting-recovery", "failed"}:
        return "recovering"
    if normalized in {"succeeded"}:
        return "completed"
    return "preflight"
