from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: summarize_authoring_shards.py <shard-root>", file=sys.stderr)
        return 2
    root = Path(argv[1])
    summaries = sorted(root.glob("shard*/summary.json"))
    records: list[dict[str, Any]] = []
    for summary_path in summaries:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            if isinstance(record, dict):
                records.append(record)
    if not records:
        for record_path in sorted(root.glob("*/record.json")):
            payload = json.loads(record_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                records.append(payload)
    merged = {
        "schema_version": "0.1",
        "shard_root": str(root),
        "shard_count": len(summaries),
        "task_count": len(records),
        "package_complete_count": sum(1 for r in records if r.get("validation", {}).get("package_complete")),
        "validator_ok_count": sum(1 for r in records if r.get("validation", {}).get("ok")),
        "simulation_pass_count": sum(1 for r in records if r.get("simulation", {}).get("ok")),
        "first_pass_simulation_pass_count": sum(1 for r in records if r.get("first_simulation", {}).get("ok")),
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
