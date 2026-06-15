#!/usr/bin/env python3
"""Ingest collected OpentronsAI web-chat protocols into the authoring harness."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labscriptai.benchmark.authoring_pilot import (
    _simulator_summary,
    _write_record,
    _write_summary,
    repair_package_metadata,
    simulate_protocol_file,
)
from labscriptai.benchmark.derive_package import derive_package_from_protocol
from labscriptai.benchmark.package_validator import validate_package
from labscriptai.benchmark.score_record import score_record_from_validation
from labscriptai.benchmark.tasks import AuthoringTask, load_authoring_tasks


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "runs" / "authoring90" / "opentrons_ai_v1"
DEFAULT_TASKS = ROOT / "benchmarks" / "authoring" / "tasks.yaml"
MODEL_ID = "opentrons-ai-web"
SCAFFOLD_ID = "official-nl-tool"
SMOKE_TASK_IDS = (
    "T001",
    "T002",
    "T014",
    "T024",
    "T034",
    "T047",
    "T055",
    "T057",
    "T068",
    "T073",
    "T087",
    "T090",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_task_ids(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def selected_tasks(
    tasks_path: Path,
    *,
    task_ids: tuple[str, ...],
    smoke: bool,
    panel_path: Path | None,
    limit: int | None,
) -> list[AuthoringTask]:
    tasks = load_authoring_tasks(tasks_path)
    by_id = {task.task_id: task for task in tasks}
    wanted = task_ids
    if smoke:
        wanted = SMOKE_TASK_IDS
    if panel_path is not None:
        panel = json.loads(panel_path.read_text(encoding="utf-8"))
        wanted = tuple(str(task_id) for task_id in panel.get("task_ids", []))
    if wanted:
        missing = [task_id for task_id in wanted if task_id not in by_id]
        if missing:
            raise ValueError(f"task ids missing from {tasks_path}: {', '.join(missing)}")
        tasks = [by_id[task_id] for task_id in wanted]
    if limit is not None:
        tasks = tasks[:limit]
    return tasks


def _read_manifest(package_dir: Path, task: AuthoringTask) -> dict[str, Any]:
    manifest = load_json(package_dir / "manifest.json")
    if manifest:
        return manifest
    return {
        "task_id": task.task_id,
        "system_id": "opentrons-ai",
        "model_id": MODEL_ID,
        "scaffold_id": SCAFFOLD_ID,
    }


def _raw_paths(out_dir: Path, task_id: str) -> dict[str, str]:
    raw_dir = out_dir / task_id / "raw"
    return {
        "raw_dir": str(raw_dir),
        "prompt": str(raw_dir / "prompt.txt"),
        "transcript": str(raw_dir / "transcript.json"),
        "response": str(raw_dir / "response.md"),
        "meta": str(raw_dir / "meta.json"),
    }


def _extract_status(out_dir: Path, task_id: str) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    raw_dir = out_dir / task_id / "raw"
    transcript = load_json(raw_dir / "transcript.json")
    meta = load_json(raw_dir / "meta.json")
    status = str(transcript.get("extract_status") or meta.get("extract_status") or "missing_raw")
    method = str(transcript.get("extract_method") or meta.get("extract_method") or "none")
    return status, method, transcript, meta


def _failure_mode_for_extract(status: str) -> str:
    if status == "refused":
        return "unsupported"
    if status in {"no_protocol", "partial", "missing_raw"}:
        return "no_code"
    if status == "timeout":
        return "provider_error"
    return "not_simulated"


def ingest_task(
    *,
    task: AuthoringTask,
    output_dir: Path,
    tasks_path: Path,
    simulate: bool,
    opentrons_python: str | None,
    workspace_root: Path | None,
    simulation_timeout_sec: int,
) -> dict[str, Any]:
    task_dir = output_dir / task.task_id
    package_dir = task_dir / "attempt1" / "package"
    protocol_path = package_dir / "protocol.py"
    extract_status, extract_method, transcript, meta = _extract_status(output_dir, task.task_id)
    started = time.monotonic()
    has_protocol = protocol_path.is_file()
    derive_info: dict[str, Any] | None = None
    metadata_repairs: list[str] = []

    if has_protocol:
        derive_info = derive_package_from_protocol(
            package_dir,
            task,
            model_id=MODEL_ID,
            scaffold_id=SCAFFOLD_ID,
            overwrite=True,
        )
        metadata_repairs = repair_package_metadata(package_dir)
        if metadata_repairs:
            derive_info = derive_package_from_protocol(
                package_dir,
                task,
                model_id=MODEL_ID,
                scaffold_id=SCAFFOLD_ID,
                overwrite=True,
            )

    initial_validation = validate_package(
        package_dir,
        simulation_pass=False,
        task_manifest_path=tasks_path,
        task_id=task.task_id,
    )
    first_pass_validation = initial_validation
    simulation_result: dict[str, Any] | None = None
    first_simulation: dict[str, Any] | None = None
    if simulate and has_protocol:
        simulation_result = simulate_protocol_file(
            protocol_path,
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            timeout_sec=simulation_timeout_sec,
        )
        first_simulation = simulation_result

    simulation_pass = bool(simulation_result and simulation_result.get("ok"))
    validation = validate_package(
        package_dir,
        simulation_pass=simulation_pass,
        task_manifest_path=tasks_path,
        task_id=task.task_id,
    )
    manifest = _read_manifest(package_dir, task)
    score = score_record_from_validation(
        validation,
        manifest,
        first_pass=validation.ok,
        attempts=1,
        wall_time_sec=time.monotonic() - started,
        input_tokens=0,
        output_tokens=0,
    ).to_dict()
    failure_mode = None if has_protocol else _failure_mode_for_extract(extract_status)
    provider_error_count = 1 if extract_status == "timeout" else 0
    record: dict[str, Any] = {
        "task_id": task.task_id,
        "scaffold_label": "opentrons-ai-web",
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "package_dir": str(package_dir),
        "attempts": 1,
        "generation_attempts": int(meta.get("collection_attempts", 1) or 1),
        "provider_error_count": provider_error_count,
        "wall_time_sec": float(meta.get("wall_time_sec", score["wall_time_sec"]) or score["wall_time_sec"]),
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "model_id": MODEL_ID,
        "scaffold_id": SCAFFOLD_ID,
        "protocol_only": True,
        "metadata_repair": True,
        "derive": derive_info,
        "initial_validation": initial_validation.to_dict(),
        "repairs": metadata_repairs,
        "first_pass_validation": first_pass_validation.to_dict(),
        "validation": validation.to_dict(),
        "deterministic_checks_pass": validation.ok,
        "first_simulation": first_simulation,
        "simulation": simulation_result,
        "simulator_summary": _simulator_summary(simulation_result),
        "simulation_repair_attempts": 0,
        "repair_success": False,
        "repair_errors": [],
        "tool_calls": 0,
        "skill_loads": 0,
        "protocol_hits": 0,
        "memory_hits": 0,
        "kb_context_tokens_estimate": 0,
        "simulator_calls": 1 if simulation_result is not None else 0,
        "score": score,
        "collection": {
            "target": "https://ai.opentrons.com/#/chat",
            "session_policy": "new_chat_per_task",
            "prompt_scheme": "A_flattened_py_only",
            "extract_status": extract_status,
            "extract_method": extract_method,
            "transcript_turn_count": len(transcript.get("turns", []))
            if isinstance(transcript.get("turns"), list)
            else 0,
            "raw_paths": _raw_paths(output_dir, task.task_id),
        },
    }
    if failure_mode:
        record["failure_mode"] = failure_mode
    if extract_status == "timeout":
        record["error"] = "opentrons_ai_collection_timeout"
    _write_record(task_dir, record)
    return record


def run_analysis(summary_path: Path, tasks_path: Path, output_dir: Path) -> dict[str, Any]:
    from labscriptai.benchmark.analyze_authoring_run import analyze_run

    return analyze_run(summary_path, tasks_path, output_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--task-ids")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-simulate", action="store_true")
    parser.add_argument("--opentrons-python")
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--simulation-timeout-sec", type=int, default=180)
    parser.add_argument("--analyze", action="store_true", default=True)
    parser.add_argument("--no-analyze", dest="analyze", action="store_false")
    parser.add_argument("--build-table", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = args.tasks.resolve()
    tasks = selected_tasks(
        tasks_path,
        task_ids=parse_task_ids(args.task_ids),
        smoke=args.smoke,
        panel_path=args.panel,
        limit=args.limit,
    )
    records = [
        ingest_task(
            task=task,
            output_dir=output_dir,
            tasks_path=tasks_path,
            simulate=not args.skip_simulate,
            opentrons_python=args.opentrons_python,
            workspace_root=args.workspace_root,
            simulation_timeout_sec=args.simulation_timeout_sec,
        )
        for task in tasks
    ]
    summary = _write_summary(output_dir, MODEL_ID, records)
    if args.analyze:
        analysis = run_analysis(
            output_dir / "summary.json",
            tasks_path,
            output_dir / "analysis",
        )
        summary["analysis_task_pass_count"] = analysis["task_pass_count"]
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if args.build_table:
        completed = subprocess.run(
            [sys.executable, "scripts/build_table1_v2.py"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            print(completed.stdout, file=sys.stdout)
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
