#!/usr/bin/env python3
"""Hourly status for runs/authoring90/llm_only (90-task direct baseline)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "authoring90" / "llm_only"
MODELS = ("gpt-5.5", "gemini-3.5-flash")
SHARDS = ("shard01", "shard02", "shard03")
LOG_PATH = RUN_ROOT / "monitor.log"


def _count_tasks(model_dir: Path) -> int:
    if not model_dir.is_dir():
        return 0
    return sum(
        1
        for shard in SHARDS
        for _ in (model_dir / shard).glob("T*")
        if (model_dir / shard / _.name).is_dir()
    )


def _shard_record_stats(shard_dir: Path) -> dict[str, int]:
    errs = prov = sim_ok = 0
    n = 0
    for rec_path in shard_dir.glob("T*/record.json"):
        n += 1
        try:
            row = json.loads(rec_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            errs += 1
            continue
        if row.get("error"):
            errs += 1
        prov += int(row.get("provider_error_count", 0))
        if (row.get("simulation") or {}).get("ok"):
            sim_ok += 1
    return {"tasks": n, "record_errors": errs, "sim_pass": sim_ok, "provider_errors": prov}


def _driver_running() -> bool:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "run_authoring90_llm_only"],
            text=True,
        ).strip()
        return bool(out)
    except subprocess.CalledProcessError:
        return False


def _pilot_running() -> bool:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "runs/authoring90/llm_only"],
            text=True,
        ).strip()
        return bool(out)
    except subprocess.CalledProcessError:
        return False


def snapshot() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    models: dict[str, dict] = {}
    for model in MODELS:
        mdir = RUN_ROOT / model
        shard_detail = {
            shard: _shard_record_stats(mdir / shard)
            for shard in SHARDS
            if (mdir / shard).is_dir()
        }
        summary_path = mdir / "summary.json"
        analysis_path = mdir / "analysis" / "attribution-summary.json"
        entry: dict = {
            "task_dirs": _count_tasks(mdir),
            "shards": shard_detail,
            "summary": summary_path.is_file(),
            "analysis": analysis_path.is_file(),
        }
        if summary_path.is_file():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            entry["task_count"] = summary.get("task_count")
            entry["provider_error_count"] = summary.get("provider_error_count")
            entry["model_id"] = summary.get("model_id")
        if analysis_path.is_file():
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            entry["task_pass_count"] = analysis.get("task_pass_count")
        models[model] = entry

    done = all(
        isinstance(models.get(m, {}).get("task_count"), int)
        and models[m]["task_count"] == 90
        and models[m].get("summary")
        for m in MODELS
    )
    return {
        "at": now,
        "driver_running": _driver_running(),
        "pilot_running": _pilot_running(),
        "models": models,
        "both_complete": done,
    }


def format_report(data: dict) -> str:
    lines = [
        f"=== llm_only monitor {data['at']} ===",
        f"driver: {'running' if data['driver_running'] else 'stopped'}",
        f"pilot:  {'running' if data['pilot_running'] else 'idle'}",
    ]
    for model in MODELS:
        m = data["models"].get(model, {})
        lines.append(f"\n[{model}] task_dirs={m.get('task_dirs', 0)}/90 summary={m.get('summary')}")
        for shard, st in (m.get("shards") or {}).items():
            lines.append(
                f"  {shard}: {st['tasks']}/30 tasks, errors={st['record_errors']}, "
                f"sim_pass={st['sim_pass']}, provider_err={st['provider_errors']}"
            )
        if m.get("task_pass_count") is not None:
            lines.append(f"  BoB (analysis): {m['task_pass_count']}/90")
        if m.get("provider_error_count") is not None:
            lines.append(f"  provider_error_count (summary): {m['provider_error_count']}")
    if data["both_complete"]:
        lines.append("\nSTATUS: both models finished (90+90). Run build_table_llm_only if needed.")
    elif not data["driver_running"] and not data["pilot_running"]:
        lines.append("\nWARN: no benchmark process — check full-run.log or restart run_authoring90_llm_only_all.sh")
    return "\n".join(lines)


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    data = snapshot()
    report = format_report(data)
    print(report)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(report + "\n\n")
    if data["both_complete"]:
        table = RUN_ROOT / "TABLE_LLM_ONLY.md"
        if not table.is_file():
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_table_llm_only.py"), str(RUN_ROOT)],
                cwd=ROOT,
                check=False,
                env={**dict(**{"PYTHONPATH": "src"}), **dict(__import__("os").environ)},
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
