"""Runtime failure case export for read-only robot traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .adapters.robot_http import RobotHttpReadOnlyAdapter
from .state import RuntimeRisk, RuntimeState
from .trace import TraceEvent, TraceWriter


CASE_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True)
class RuntimeCase:
    case_id: str
    run_id: str
    source: str
    status: str
    error_category: str
    error_text: str
    expected_policy: str
    allowed_action_types: tuple[str, ...]
    state: RuntimeState
    snapshot: Mapping[str, Any]
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CASE_SCHEMA_VERSION,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "source": self.source,
            "created_at": self.created_at,
            "status": self.status,
            "error_category": self.error_category,
            "error_text": self.error_text,
            "expected_policy": self.expected_policy,
            "allowed_action_types": list(self.allowed_action_types),
            "state": self.state.to_dict(),
            "snapshot": dict(self.snapshot),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RuntimeCase":
        return cls(
            case_id=str(payload["case_id"]),
            run_id=str(payload["run_id"]),
            source=str(payload.get("source", "unknown")),
            created_at=payload.get("created_at") if isinstance(payload.get("created_at"), str) else None,
            status=str(payload.get("status", "unknown")),
            error_category=str(payload.get("error_category", "unknown")),
            error_text=str(payload.get("error_text", "")),
            expected_policy=str(payload.get("expected_policy", "manual_review")),
            allowed_action_types=tuple(str(item) for item in payload.get("allowed_action_types", [])),
            state=RuntimeState.from_mapping(payload["state"]),
            snapshot=payload.get("snapshot", {}) if isinstance(payload.get("snapshot", {}), Mapping) else {},
        )


def collect_runtime_cases(
    adapter: RobotHttpReadOnlyAdapter,
    *,
    output_dir: Path,
    run_ids: tuple[str, ...] = (),
    limit: int = 20,
    include_succeeded: bool = False,
) -> dict[str, Any]:
    """Collect read-only run snapshots and export them as replayable cases."""

    output_dir.mkdir(parents=True, exist_ok=True)
    runs = adapter.list_runs(page_length=limit)
    selected_ids = run_ids or tuple(_select_run_ids(runs, limit=limit, include_succeeded=include_succeeded))
    records: list[dict[str, Any]] = []
    for run_id in selected_ids:
        snapshot = adapter.snapshot(run_id=run_id)
        case = case_from_snapshot(snapshot, source="robot_http")
        case_dir = output_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        _write_json(case_dir / "snapshot.json", snapshot)
        _write_json(case_dir / "case.json", case.to_dict())
        trace_path = case_dir / "trace.jsonl"
        writer = TraceWriter(trace_path)
        writer.append(
            TraceEvent.for_state(
                case.state,
                event_type="observation",
                actor="system",
                payload={
                    "source": "robot_http",
                    "case_id": case.case_id,
                    "error_category": case.error_category,
                    "expected_policy": case.expected_policy,
                },
            )
        )
        record = {
            "case_id": case.case_id,
            "run_id": case.run_id,
            "status": case.status,
            "error_category": case.error_category,
            "expected_policy": case.expected_policy,
            "case_path": str(case_dir / "case.json"),
            "trace_path": str(trace_path),
        }
        records.append(record)

    summary = {
        "schema_version": CASE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "robot_http",
        "case_count": len(records),
        "records": records,
    }
    _write_json(output_dir / "summary.json", summary)
    with (output_dir / "index.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    return summary


def case_from_snapshot(snapshot: Mapping[str, Any], *, source: str) -> RuntimeCase:
    run = snapshot.get("run") if isinstance(snapshot.get("run"), Mapping) else {}
    run_history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), Mapping) else {}
    run_id = str(run.get("id") or run_history.get("run_id") or "unknown-run")
    status = str(run.get("status") or run_history.get("status") or "unknown")
    error_text = _error_text(run, run_history)
    error_category = classify_error(error_text, run_history)
    policy = _policy_for_category(error_category)
    risks = _risks_for_category(error_category, error_text)
    state = RuntimeState(
        run_id=run_id,
        phase=_phase_for_status(status),
        robot=_robot_identity(snapshot),
        observed=dict(snapshot),
        completed_commands=tuple(run_history.get("completed_commands", [])),
        failed_commands=tuple(run_history.get("failed_commands", [])),
        remaining_plan=tuple(run_history.get("remaining_plan", [])),
        risks=risks,
    )
    return RuntimeCase(
        case_id=f"case-{run_id}",
        run_id=run_id,
        source=source,
        created_at=run.get("createdAt") if isinstance(run.get("createdAt"), str) else None,
        status=status,
        error_category=error_category,
        error_text=error_text,
        expected_policy=policy["expected_policy"],
        allowed_action_types=policy["allowed_action_types"],
        state=state,
        snapshot=snapshot,
    )


def classify_error(error_text: str, run_history: Mapping[str, Any] | None = None) -> str:
    text = error_text.lower()
    if "err408" in text or "thermal drift" in text:
        return "thermocycler_thermal_drift"
    if "no tip" in text or "tip pickup" in text or "pick up tip" in text:
        return "missing_tip"
    if "destination" in text and "occupied" in text:
        return "destination_occupied"
    if "module" in text or "thermocycler" in text or "temperature" in text:
        return "module_error"
    latest_failed = (run_history or {}).get("latest_failed_command") if isinstance(run_history, Mapping) else None
    if latest_failed:
        return "command_failed"
    return "unknown"


def load_cases(path: Path) -> list[RuntimeCase]:
    """Load cases from a directory, case JSON file, or index JSONL."""

    if path.is_dir():
        return [RuntimeCase.from_mapping(_read_json(case_path)) for case_path in sorted(path.glob("case-*/case.json"))]
    if path.suffix == ".jsonl":
        cases: list[RuntimeCase] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            case_path = Path(record.get("case_path", ""))
            if case_path.exists():
                cases.append(RuntimeCase.from_mapping(_read_json(case_path)))
        return cases
    payload = _read_json(path)
    if "records" in payload:
        cases = []
        for record in payload["records"]:
            case_path = Path(record.get("case_path", ""))
            if case_path.exists():
                cases.append(RuntimeCase.from_mapping(_read_json(case_path)))
        return cases
    return [RuntimeCase.from_mapping(payload)]


def _select_run_ids(runs: Any, *, limit: int, include_succeeded: bool) -> list[str]:
    items = runs if isinstance(runs, list) else []
    selected: list[str] = []
    for run in reversed(items):
        if not isinstance(run, Mapping):
            continue
        status = str(run.get("status") or "")
        if not include_succeeded and status == "succeeded":
            continue
        run_id = run.get("id")
        if run_id:
            selected.append(str(run_id))
        if len(selected) >= limit:
            break
    return selected


def _error_text(run: Mapping[str, Any], run_history: Mapping[str, Any]) -> str:
    errors = run.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, Mapping):
            return str(first.get("detail") or first.get("errorType") or first)
    latest = run_history.get("latest_failed_command")
    if isinstance(latest, Mapping):
        error = latest.get("error")
        if isinstance(error, Mapping):
            return str(error.get("detail") or error.get("message") or error)
        return str(latest)
    return ""


def _policy_for_category(category: str) -> dict[str, Any]:
    if category == "missing_tip":
        return {
            "expected_policy": "low_risk_recovery_candidate_shadow_only",
            "allowed_action_types": (
                "mark_resource_unavailable",
                "choose_alternative_source",
                "request_human_confirmation",
                "inspect_robot_state",
                "pause_run",
            ),
        }
    if category == "destination_occupied":
        return {
            "expected_policy": "manual_confirmation_required",
            "allowed_action_types": (
                "request_human_confirmation",
                "inspect_robot_state",
                "capture_deck_image",
                "pause_run",
            ),
        }
    if category in {"thermocycler_thermal_drift", "module_error"}:
        return {
            "expected_policy": "human_module_check_required",
            "allowed_action_types": (
                "request_human_confirmation",
                "inspect_robot_state",
                "capture_deck_image",
                "pause_run",
            ),
        }
    return {
        "expected_policy": "manual_review",
        "allowed_action_types": ("request_human_confirmation", "inspect_robot_state", "pause_run"),
    }


def _risks_for_category(category: str, error_text: str) -> tuple[RuntimeRisk, ...]:
    if category in {"thermocycler_thermal_drift", "module_error", "destination_occupied"}:
        return (
            RuntimeRisk(
                code=category,
                severity="blocker",
                message=error_text or f"Runtime case requires manual review: {category}",
            ),
        )
    if category == "missing_tip":
        return (
            RuntimeRisk(
                code=category,
                severity="warning",
                message=error_text or "Tip pickup failed or tip is unavailable.",
            ),
        )
    return ()


def _robot_identity(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    health = snapshot.get("robot_health") if isinstance(snapshot.get("robot_health"), Mapping) else {}
    return {
        "id": health.get("robot_serial") or health.get("robotSerial"),
        "model": health.get("robot_model") or health.get("robotModel"),
    }


def _phase_for_status(status: str) -> str:
    normalized = status.lower()
    if normalized == "running":
        return "running"
    if normalized in {"paused", "stopped"}:
        return "paused"
    if normalized in {"failed", "awaiting-recovery"}:
        return "recovering"
    if normalized == "succeeded":
        return "completed"
    return "preflight"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
