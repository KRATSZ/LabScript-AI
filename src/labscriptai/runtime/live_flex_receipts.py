"""Atomic evidence-record updates backed by persisted MCP recovery receipts."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .execution_evidence import verified_recovery_execution
from .live_flex_evidence import (
    FINAL_LABELS,
    load_live_manifest,
    validate_bundle_contract,
    validate_live_record,
)

EXECUTION_RECEIPT_SCHEMA = "opentrons_recovery_execution.v1"
RECOVERY_TOOL_NAMES = frozenset(
    {"execute_protocol_recovery", "recover_tip_pickup"}
)
FINALIZABLE_LABELS = FINAL_LABELS - {"incomplete"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_log_entry_sha256(entry: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        dict(entry),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(dict(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _bundle_case(
    bundle_dir: Path,
    case_id: str,
) -> tuple[dict[str, Any], dict[str, Any], Path, dict[str, Any]]:
    manifest = load_live_manifest(bundle_dir / "manifest.json")
    failures = validate_bundle_contract(bundle_dir, manifest)
    if failures:
        raise ValueError("live bundle contract failed: " + "; ".join(failures))
    case = next(
        (item for item in manifest["cases"] if item.get("case_id") == case_id),
        None,
    )
    if case is None:
        raise ValueError(f"unknown live case: {case_id}")
    record_path = bundle_dir / str(case["evidence_file"])
    record = _load_json(record_path)
    return manifest, case, record_path, record


def start_live_record(
    bundle_dir: Path,
    *,
    case_id: str,
    run_id: str,
    robot_snapshot: Mapping[str, Any],
    captured_at: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Bind an unstarted case to one real run and its initial robot snapshot."""

    run_id = str(run_id or "").strip()
    if not run_id:
        raise ValueError("run_id is required")
    if not robot_snapshot:
        raise ValueError("robot_snapshot must be a non-empty object")
    manifest, case, record_path, record = _bundle_case(bundle_dir, case_id)
    if record.get("status") != "not_started":
        raise ValueError(
            f"case {case_id} cannot start from status {record.get('status')}"
        )

    timestamp = captured_at or utc_now_iso()
    record.update(
        {
            "status": "running",
            "timestamps": {"started_at": timestamp, "completed_at": None},
            "initial_state": {
                "run_id": run_id,
                "protocol_sha256": case["protocol_sha256"],
                "deck_map": manifest["common_deck"],
                "case_state": case["agent_context"],
                "captured_at": timestamp,
                "robot_snapshot": dict(robot_snapshot),
            },
        }
    )
    if write:
        _atomic_write_json(record_path, record)
    return record


def record_live_decision(
    bundle_dir: Path,
    *,
    case_id: str,
    run_id: str,
    fault_evidence: Sequence[Mapping[str, Any]],
    model_evidence: Mapping[str, Any],
    gatekeeper_evidence: Mapping[str, Any],
    notes: Sequence[str] = (),
    write: bool = False,
) -> dict[str, Any]:
    """Persist the first model/Gatekeeper decision without making the row terminal."""

    _, _, record_path, record = _bundle_case(bundle_dir, case_id)
    if record.get("status") != "running":
        raise ValueError(
            f"case {case_id} must be running before decision capture; got {record.get('status')}"
        )
    initial_run_id = str(_mapping(record.get("initial_state")).get("run_id") or "")
    if initial_run_id != run_id:
        raise ValueError(
            f"decision run_id {run_id} does not match started run {initial_run_id or '<missing>'}"
        )
    prior_model = _mapping(record.get("model_evidence"))
    if prior_model.get("attempted_at") or prior_model.get("raw_first_proposal"):
        raise ValueError(f"case {case_id} already has a preserved first model attempt")
    if not fault_evidence:
        raise ValueError("fault_evidence must contain at least one actual event")
    if not model_evidence:
        raise ValueError("model_evidence must be a non-empty object")
    if not gatekeeper_evidence:
        raise ValueError("gatekeeper_evidence must be a non-empty object")

    record["fault_evidence"] = [dict(event) for event in fault_evidence]
    record["model_evidence"] = dict(model_evidence)
    record["gatekeeper_evidence"] = dict(gatekeeper_evidence)
    record_notes = list(record.get("notes") or [])
    record_notes.extend(str(note) for note in notes if str(note).strip())
    record["notes"] = record_notes
    if write:
        _atomic_write_json(record_path, record)
    return record


def load_result_log_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"result-log entry must be an object at {path}:{line_number}")
        entries.append(payload)
    return entries


def select_recovery_receipt(
    entries: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    entry_id: str | None = None,
) -> Mapping[str, Any]:
    matches = []
    for entry in entries:
        if entry.get("run_id") != run_id:
            continue
        if entry_id and entry.get("entry_id") != entry_id:
            continue
        if entry.get("tool_name") not in RECOVERY_TOOL_NAMES:
            continue
        if entry.get("event_kind") != "protocol_recovery":
            continue
        if entry.get("status") != "succeeded":
            continue
        receipt = _mapping(_mapping(entry.get("data")).get("execution_result"))
        if receipt.get("schema_version") != EXECUTION_RECEIPT_SCHEMA:
            continue
        matches.append(entry)
    if not matches:
        suffix = f" and entry_id={entry_id}" if entry_id else ""
        raise ValueError(f"no verified recovery receipt for run_id={run_id}{suffix}")
    if len(matches) > 1:
        ids = [str(entry.get("entry_id") or "<missing>") for entry in matches]
        raise ValueError(
            "multiple recovery receipts match; pass entry_id explicitly: " + ", ".join(ids)
        )
    return matches[0]


def ingest_recovery_receipt(
    bundle_dir: Path,
    *,
    case_id: str,
    run_id: str,
    result_log_path: Path,
    entry_id: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Attach executor-owned recovery evidence to the matching running case."""

    _, case, record_path, record = _bundle_case(bundle_dir, case_id)
    if record.get("status") != "running":
        raise ValueError(
            f"case {case_id} must be running before receipt import; got {record.get('status')}"
        )
    initial_run_id = str(_mapping(record.get("initial_state")).get("run_id") or "")
    if initial_run_id != run_id:
        raise ValueError(
            f"receipt run_id {run_id} does not match started run {initial_run_id or '<missing>'}"
        )
    expected_action = str(
        _mapping(case.get("oracle")).get("expected_executor_action") or ""
    ).strip()
    if not expected_action:
        raise ValueError(f"case {case_id} does not define an autonomous executor action")

    entry = select_recovery_receipt(
        load_result_log_entries(result_log_path),
        run_id=run_id,
        entry_id=entry_id,
    )
    entry_data = _mapping(entry.get("data"))
    execution_result = _mapping(entry_data.get("execution_result"))
    if execution_result.get("run_id") != run_id:
        raise ValueError("execution receipt run_id does not match result-log entry")
    if not verified_recovery_execution(
        execution_result,
        expected_action=expected_action,
    ):
        raise ValueError(
            f"execution receipt does not verify expected action {expected_action}"
        )
    robot_events = entry_data.get("robot_events")
    if not isinstance(robot_events, list) or not robot_events:
        raise ValueError("execution receipt is missing robot_events")

    record["execution_evidence"] = {
        "robot_events": robot_events,
        "execution_result": dict(execution_result),
        "receipt": {
            "entry_id": entry.get("entry_id"),
            "timestamp": entry.get("timestamp"),
            "session_id": entry.get("session_id"),
            "run_id": entry.get("run_id"),
            "tool_name": entry.get("tool_name"),
            "result_log_path": str(result_log_path.resolve()),
            "result_log_sha256": _sha256(result_log_path),
            "entry_sha256": result_log_entry_sha256(entry),
            "entry": dict(entry),
        },
    }
    notes = list(record.get("notes") or [])
    notes.append(
        f"Imported verified MCP recovery receipt {entry.get('entry_id')} for {expected_action}."
    )
    record["notes"] = notes
    if write:
        _atomic_write_json(record_path, record)
    return record


def finalize_live_record(
    bundle_dir: Path,
    *,
    case_id: str,
    final_label: str,
    completed_at: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Make a running record terminal only when its complete evidence validates."""

    _, case, record_path, record = _bundle_case(bundle_dir, case_id)
    if record.get("status") != "running":
        raise ValueError(
            f"case {case_id} must be running before finalization; got {record.get('status')}"
        )
    if final_label not in FINALIZABLE_LABELS:
        raise ValueError(f"invalid terminal label: {final_label}")
    status = "run_error" if final_label == "run_error" else "complete"
    timestamps = dict(record.get("timestamps") or {})
    timestamps["completed_at"] = completed_at or utc_now_iso()
    record.update(
        {
            "status": status,
            "final_label": final_label,
            "timestamps": timestamps,
        }
    )
    failures = validate_live_record(record, case, bundle_dir=bundle_dir)
    if failures:
        raise ValueError("record cannot be finalized: " + "; ".join(failures))
    if write:
        _atomic_write_json(record_path, record)
    return record


__all__ = [
    "EXECUTION_RECEIPT_SCHEMA",
    "FINALIZABLE_LABELS",
    "ingest_recovery_receipt",
    "finalize_live_record",
    "load_result_log_entries",
    "record_live_decision",
    "result_log_entry_sha256",
    "select_recovery_receipt",
    "start_live_record",
]
