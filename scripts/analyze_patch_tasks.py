#!/usr/bin/env python3
"""Analyze a small set of patch task dirs for supplemental table row."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from labscriptai.benchmark.analyze_authoring_run import analyze_run
from labscriptai.benchmark.tasks import load_authoring_tasks


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: analyze_patch_tasks.py <tasks.yaml> <patch-dir> T001,T002,...", file=sys.stderr)
        return 2
    tasks_path = Path(argv[1])
    patch_dir = Path(argv[2])
    task_ids = [t.strip() for t in argv[3].split(",") if t.strip()]
    tasks = {t.task_id: t for t in load_authoring_tasks(tasks_path)}
    records = []
    for task_id in task_ids:
        rec_path = patch_dir / task_id / "record.json"
        if not rec_path.is_file():
            solo = patch_dir / f"{task_id}-solo" / task_id / "record.json"
            rec_path = solo if solo.is_file() else rec_path
        if rec_path.is_file():
            records.append(json.loads(rec_path.read_text(encoding="utf-8")))
    summary = {
        "schema_version": "0.1",
        "task_count": len(records),
        "records": records,
        "total_tokens": sum(int(r.get("total_tokens", 0)) for r in records),
        "provider_error_count": sum(int(r.get("provider_error_count", 0)) for r in records),
    }
    tmp = patch_dir / "_patch_summary.json"
    tmp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    result = analyze_run(tmp, tasks_path)
    tmp.unlink(missing_ok=True)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
