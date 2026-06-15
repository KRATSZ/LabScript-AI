from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def is_task_record_complete(record: dict[str, Any], retry_attempts: int) -> bool:
    if retry_attempts < 1:
        raise ValueError("retry_attempts must be >= 1")
    if not isinstance(record, dict) or not record.get("task_id"):
        return False
    validation = record.get("validation")
    if isinstance(validation, dict):
        return True
    try:
        generation_attempts = int(record.get("generation_attempts", 0) or 0)
    except (TypeError, ValueError):
        generation_attempts = 0
    return generation_attempts >= retry_attempts


def load_task_record(record_path: Path) -> dict[str, Any] | None:
    if not record_path.is_file():
        return None
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def completed_task_ids(
    out_dir: Path,
    task_ids: Iterable[str],
    *,
    retry_attempts: int,
) -> list[str]:
    completed: list[str] = []
    for task_id in task_ids:
        payload = load_task_record(out_dir / task_id / "record.json")
        if payload is None:
            continue
        if payload.get("task_id") != task_id:
            continue
        if is_task_record_complete(payload, retry_attempts):
            completed.append(task_id)
    return completed


def pending_task_ids(
    out_dir: Path,
    task_ids: Iterable[str],
    *,
    retry_attempts: int,
) -> list[str]:
    completed = set(completed_task_ids(out_dir, task_ids, retry_attempts=retry_attempts))
    return [task_id for task_id in task_ids if task_id not in completed]
