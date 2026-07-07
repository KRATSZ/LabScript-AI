from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from labscriptai.benchmark.run_progress import is_task_record_complete


def _validator_ok(record: dict[str, Any]) -> bool:
    validation = record.get("validation", {})
    if not isinstance(validation, dict):
        return False
    if "ok" in validation:
        return bool(validation["ok"])
    return bool(validation.get("package_complete")) and not validation.get("critical_failures") and not validation.get("issues")


def _nested_ok(record: dict[str, Any], key: str) -> bool:
    payload = record.get(key)
    return isinstance(payload, dict) and bool(payload.get("ok"))


def _keep_record(record: dict[str, Any], retry_attempts: int | None) -> bool:
    if retry_attempts is None:
        return True
    return is_task_record_complete(record, retry_attempts)


def _int(record: dict[str, Any], key: str) -> int:
    try:
        return int(record.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _float(record: dict[str, Any], key: str) -> float:
    try:
        return float(record.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _summary_patch_backend(records: list[dict[str, Any]]) -> str:
    backends = {
        str(record.get("repair_patch_backend", "none"))
        for record in records
        if record.get("repair_patch_backend")
    }
    if not backends:
        return "none"
    if len(backends) == 1:
        return next(iter(backends))
    return "mixed"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_root", type=Path)
    parser.add_argument(
        "--retry-attempts",
        type=int,
        default=None,
        help="Optional retry count used to ignore task records that are only interim failures.",
    )
    args = parser.parse_args(argv[1:])

    root = args.shard_root
    root.mkdir(parents=True, exist_ok=True)
    shard_dirs = [path for path in sorted(root.glob("shard*/")) if path.is_dir()]
    if not shard_dirs:
        shard_dirs = [
            path
            for path in sorted(root.parent.glob(f"{root.name}_s*"))
            if path.is_dir()
        ]
    summaries = [path / "summary.json" for path in shard_dirs if (path / "summary.json").is_file()]
    records: list[dict[str, Any]] = []
    for shard_dir in shard_dirs:
        shard_records = []
        for record_path in sorted(shard_dir.glob("T*/record.json")):
            payload = json.loads(record_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and _keep_record(payload, args.retry_attempts):
                shard_records.append(payload)
        if shard_records:
            records.extend(shard_records)
            continue
        summary_path = shard_dir / "summary.json"
        if not summary_path.is_file():
            continue
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            if isinstance(record, dict) and _keep_record(record, args.retry_attempts):
                records.append(record)
    if not records:
        for record_path in sorted(root.glob("*/record.json")):
            payload = json.loads(record_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and _keep_record(payload, args.retry_attempts):
                records.append(payload)
    repaired_records = [r for r in records if _int(r, "simulation_repair_attempts") > 0]
    wall_times = [_float(r, "wall_time_sec") for r in records]
    merged = {
        "schema_version": "0.1",
        "shard_root": str(root),
        "shard_count": len(summaries),
        "task_count": len(records),
        "package_complete_count": sum(1 for r in records if r.get("validation", {}).get("package_complete")),
        "deterministic_pass_count": sum(1 for r in records if r.get("deterministic_checks_pass")),
        "validator_ok_count": sum(1 for r in records if _validator_ok(r)),
        "simulation_attempted_count": sum(1 for r in records if r.get("simulation") is not None),
        "simulation_pass_count": sum(1 for r in records if _nested_ok(r, "simulation")),
        "first_pass_simulation_pass_count": sum(1 for r in records if _nested_ok(r, "first_simulation")),
        "first_pass_validator_pass_count": sum(1 for r in records if _nested_ok(r, "first_pass_validation")),
        "repaired_simulation_pass_count": sum(1 for r in repaired_records if _nested_ok(r, "simulation")),
        "repaired_validator_pass_count": sum(1 for r in repaired_records if _validator_ok(r)),
        "simulation_repair_attempts": sum(_int(r, "simulation_repair_attempts") for r in records),
        "repair_success_count": sum(1 for r in records if r.get("repair_success")),
        "avg_repair_attempts_when_repaired": (
            sum(_int(r, "simulation_repair_attempts") for r in repaired_records) / len(repaired_records)
            if repaired_records
            else 0.0
        ),
        "max_repair_attempts_observed": max(
            [_int(r, "simulation_repair_attempts") for r in records] or [0]
        ),
        "provider_error_count": sum(_int(r, "provider_error_count") for r in records),
        "provider_errors_per_task": {
            str(r.get("task_id")): _int(r, "provider_error_count")
            for r in records
            if r.get("task_id")
        },
        "generation_attempts_per_task": {
            str(r.get("task_id")): _int(r, "generation_attempts")
            for r in records
            if r.get("task_id")
        },
        "repair_attempts_per_task": {
            str(r.get("task_id")): _int(r, "simulation_repair_attempts")
            for r in records
            if r.get("task_id")
        },
        "attempts_per_task": {
            str(r.get("task_id")): _int(r, "attempts")
            for r in records
            if r.get("task_id")
        },
        "error_count": sum(1 for r in records if "error" in r),
        "total_attempts": sum(_int(r, "attempts") for r in records),
        "total_wall_time_sec": sum(wall_times),
        "avg_wall_time_sec": sum(wall_times) / len(wall_times) if wall_times else 0.0,
        "max_wall_time_sec": max(wall_times or [0.0]),
        "total_tokens": sum(_int(r, "total_tokens") for r in records),
        "input_tokens": sum(_int(r, "input_tokens") for r in records),
        "output_tokens": sum(_int(r, "output_tokens") for r in records),
        "authoring_input_tokens": sum(_int(r, "authoring_input_tokens") for r in records),
        "authoring_output_tokens": sum(_int(r, "authoring_output_tokens") for r in records),
        "authoring_total_tokens": sum(_int(r, "authoring_total_tokens") for r in records),
        "repair_input_tokens": sum(_int(r, "repair_input_tokens") for r in records),
        "repair_output_tokens": sum(_int(r, "repair_output_tokens") for r in records),
        "repair_total_tokens": sum(_int(r, "repair_total_tokens") for r in records),
        "tokens_per_task": {
            str(r.get("task_id")): _int(r, "total_tokens")
            for r in records
            if r.get("task_id")
        },
        "simulator_calls": sum(_int(r, "simulator_calls") for r in records),
        "tool_calls": sum(_int(r, "tool_calls") for r in records),
        "skill_loads": sum(_int(r, "skill_loads") for r in records),
        "protocol_hits": sum(_int(r, "protocol_hits") for r in records),
        "memory_hits": sum(_int(r, "memory_hits") for r in records),
        "kb_context_tokens_estimate": sum(_int(r, "kb_context_tokens_estimate") for r in records),
        "repair_patch_count": sum(_int(r, "repair_patch_count") for r in records),
        "repair_patch_rejected_count": sum(_int(r, "repair_patch_rejected_count") for r in records),
        "repair_patch_backend": _summary_patch_backend(records),
        "records": records,
    }
    (root / "summary.json").write_text(
        json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
