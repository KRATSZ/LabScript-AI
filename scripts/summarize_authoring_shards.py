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
    merged = {
        "schema_version": "0.1",
        "shard_root": str(root),
        "shard_count": len(summaries),
        "task_count": len(records),
        "package_complete_count": sum(1 for r in records if r.get("validation", {}).get("package_complete")),
        "validator_ok_count": sum(1 for r in records if _validator_ok(r)),
        "simulation_pass_count": sum(1 for r in records if _nested_ok(r, "simulation")),
        "first_pass_simulation_pass_count": sum(1 for r in records if _nested_ok(r, "first_simulation")),
        "provider_error_count": sum(int(r.get("provider_error_count", 0)) for r in records),
        "total_tokens": sum(int(r.get("total_tokens", 0)) for r in records),
        "input_tokens": sum(int(r.get("input_tokens", 0)) for r in records),
        "output_tokens": sum(int(r.get("output_tokens", 0)) for r in records),
        "simulator_calls": sum(int(r.get("simulator_calls", 0)) for r in records),
        "tool_calls": sum(int(r.get("tool_calls", 0)) for r in records),
        "skill_loads": sum(int(r.get("skill_loads", 0)) for r in records),
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
