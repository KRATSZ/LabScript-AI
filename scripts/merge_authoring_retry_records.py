#!/usr/bin/env python3
"""Merge successful provider-error retries back into an authoring run root."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _records_by_task(root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    records: dict[str, tuple[Path, dict[str, Any]]] = {}
    for record_path in sorted(root.glob("**/T*/record.json")):
        record = _load(record_path)
        task_id = str(record.get("task_id") or record_path.parent.name)
        records[task_id] = (record_path, record)
    return records


def _parse_task_ids(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    return {part.strip() for part in raw.split(",") if part.strip()}


def _has_final_provider_error(record: dict[str, Any]) -> bool:
    if record.get("error"):
        return True
    native_returncode = record.get("native_agent_returncode")
    if native_returncode is not None and int(native_returncode) != 0:
        return True
    for key, value in record.items():
        if key.endswith("_returncode") and value is not None and int(value) != 0:
            return True
    return False


def _accepted_retry(record: dict[str, Any]) -> bool:
    if int(record.get("total_tokens", 0)) <= 0:
        return False
    return not _has_final_provider_error(record)


def _copy_task_dir(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _backup_once(path: Path, stem: str) -> str | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.stem}.pre_{stem}{path.suffix}")
    if backup.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_name(f"{path.stem}.pre_{stem}.{stamp}{path.suffix}")
    if path.is_dir():
        shutil.copytree(path, backup)
    else:
        shutil.copy2(path, backup)
    return str(backup)


def _rerun_summarizer(target_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "summarize_authoring_shards.py"), str(target_root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    if completed.returncode:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise subprocess.CalledProcessError(completed.returncode, completed.args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_root", type=Path)
    parser.add_argument("retry_root", type=Path)
    parser.add_argument("--task-ids", help="Optional comma-separated task IDs to consider.")
    parser.add_argument(
        "--output-name",
        default="api_retry_merge.json",
        help="Merge audit filename written under target_root.",
    )
    parser.add_argument(
        "--replace-any",
        action="store_true",
        help="Allow replacement even if the target record was not a provider error.",
    )
    parser.add_argument(
        "--append-missing",
        action="store_true",
        help="Append accepted retry records that are not already present in the target root.",
    )
    parser.add_argument(
        "--append-shard",
        default="shard_retry",
        help="Shard directory name under target_root for --append-missing records.",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Do not regenerate target_root/summary.json after copying records.",
    )
    args = parser.parse_args(argv)

    target_root = args.target_root.resolve()
    retry_root = args.retry_root.resolve()
    target_records = _records_by_task(target_root)
    retry_records = _records_by_task(retry_root)
    wanted = _parse_task_ids(args.task_ids)

    stem = Path(args.output_name).stem
    summary_backup = _backup_once(target_root / "summary.json", stem)
    analysis_backup = _backup_once(target_root / "analysis", stem)

    replaced: list[str] = []
    appended: list[str] = []
    skipped: dict[str, str] = {}
    append_dir = target_root / args.append_shard
    for task_id, (retry_record_path, retry_record) in sorted(retry_records.items()):
        if wanted is not None and task_id not in wanted:
            continue
        target = target_records.get(task_id)
        if target is None:
            if not args.append_missing:
                skipped[task_id] = "missing_target_record"
                continue
            if not _accepted_retry(retry_record):
                skipped[task_id] = "retry_not_final_success"
                continue
            retry_task_dir = retry_record_path.parent
            destination = append_dir / task_id
            _copy_task_dir(retry_task_dir, destination)
            appended.append(task_id)
            continue
        target_record_path, target_record = target
        if not args.replace_any and int(target_record.get("provider_error_count", 0)) <= 0:
            skipped[task_id] = "target_not_provider_error"
            continue
        if not _accepted_retry(retry_record):
            skipped[task_id] = "retry_not_final_success"
            continue
        target_task_dir = target_record_path.parent
        retry_task_dir = retry_record_path.parent
        _copy_task_dir(retry_task_dir, target_task_dir)
        replaced.append(task_id)

    if not args.no_summary:
        _rerun_summarizer(target_root)

    summary = _load(target_root / "summary.json") if (target_root / "summary.json").exists() else {}
    audit = {
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "target_root": str(target_root.relative_to(ROOT) if target_root.is_relative_to(ROOT) else target_root),
        "retry_root": str(retry_root.relative_to(ROOT) if retry_root.is_relative_to(ROOT) else retry_root),
        "task_filter": sorted(wanted) if wanted else None,
        "replaced_task_ids": replaced,
        "appended_task_ids": appended,
        "skipped_task_ids": skipped,
        "summary_backup": summary_backup,
        "analysis_backup": analysis_backup,
        "merged_task_count": summary.get("task_count"),
        "merged_provider_error_count": summary.get("provider_error_count"),
        "merged_simulation_pass_count": summary.get("simulation_pass_count"),
        "merged_validator_ok_count": summary.get("validator_ok_count"),
        "merged_total_tokens": summary.get("total_tokens"),
    }
    (target_root / args.output_name).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
