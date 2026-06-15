"""Summarize authoring benchmark runs for attribution and semantic checks."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .semantic_validator import validate_param_sweep, validate_semantics
from .tasks import load_authoring_tasks


def _load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _trace_status(record: dict[str, Any]) -> str:
    package_dir = record.get("package_dir")
    if not isinstance(package_dir, str):
        return "missing_package_dir"
    trace_path = Path(package_dir) / "trace.jsonl"
    return "present" if trace_path.exists() else "missing"


def _failure_mode(record: dict[str, Any]) -> str:
    explicit = record.get("failure_mode")
    if isinstance(explicit, str) and explicit:
        return explicit
    if record.get("error"):
        return "provider_error"
    if _provider_error_count(record) > 0:
        return "provider_retry_then_success"
    if int(record.get("simulation_repair_attempts", 0)) > 0:
        return "simulation_repair_then_success"
    if record.get("first_simulation", {}).get("ok"):
        return "first_pass"
    return "not_simulated"


def _provider_error_count(record: dict[str, Any]) -> int:
    if "provider_error_count" in record:
        return int(record.get("provider_error_count", 0))
    prior_errors = record.get("prior_errors")
    if isinstance(prior_errors, list):
        return len(prior_errors)
    errors = record.get("errors")
    if isinstance(errors, list):
        return len(errors)
    return 0


def analyze_run(summary_path: Path, tasks_path: Path, output_dir: Path | None = None) -> dict[str, Any]:
    summary = _load_summary(summary_path)
    tasks = {task.task_id: task for task in load_authoring_tasks(tasks_path)}
    records = summary.get("records", [])
    if not isinstance(records, list):
        records = []

    per_task: list[dict[str, Any]] = []
    semantic_results: list[dict[str, Any]] = []
    by_difficulty: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "task_count": 0,
            "simulation_pass_count": 0,
            "validator_ok_count": 0,
            "semantic_ok_count": 0,
            "param_sweep_ok_count": 0,
            "task_pass_count": 0,
            "dynamic_task_count": 0,
            "first_pass_simulation_pass_count": 0,
            "provider_error_count": 0,
            "simulation_repair_attempts": 0,
            "attempts_total": 0,
        }
    )

    for record in records:
        if not isinstance(record, dict):
            continue
        task_id = str(record.get("task_id"))
        task = tasks.get(task_id)
        difficulty = str(
            record.get("difficulty")
            or record.get("level")
            or (task.difficulty if task else "unknown")
        )
        package_dir = record.get("package_dir")
        semantic: dict[str, Any] | None = None
        param_sweep: dict[str, Any] | None = None
        if task and isinstance(package_dir, str) and Path(package_dir).exists():
            semantic = validate_semantics(Path(package_dir), task).to_dict()
            semantic_results.append(semantic)
            param_sweep = validate_param_sweep(Path(package_dir), task).to_dict()

        simulation = record.get("simulation") or {}
        validation = record.get("validation") or {}
        first_simulation = record.get("first_simulation") or {}

        row = {
            "task_id": task_id,
            "difficulty": difficulty,
            "attempts": int(record.get("attempts", 0)),
            "generation_attempts": int(record.get("generation_attempts", 0)),
            "provider_error_count": _provider_error_count(record),
            "simulation_repair_attempts": int(record.get("simulation_repair_attempts", 0)),
            "simulation_ok": bool(simulation.get("ok")),
            "validator_ok": bool(validation.get("ok")),
            "first_pass_simulation_ok": bool(first_simulation.get("ok")),
            "semantic_ok": bool(semantic and semantic.get("ok")),
            "semantic_score": semantic.get("score") if semantic else None,
            "semantic_issue_codes": [
                issue.get("code")
                for issue in (semantic.get("issues", []) if semantic else [])
                if isinstance(issue, dict)
            ],
            "param_sweep_ok": bool(param_sweep and param_sweep.get("ok")),
            "param_sweep_dynamic_task": bool(param_sweep and param_sweep.get("dynamic_task")),
            "param_sweep_issue_codes": [
                issue.get("code")
                for issue in (param_sweep.get("issues", []) if param_sweep else [])
                if isinstance(issue, dict)
            ],
            "trace_status": _trace_status(record),
            "failure_mode": _failure_mode(record),
        }
        row["task_pass"] = bool(
            row["simulation_ok"]
            and row["validator_ok"]
            and row["semantic_ok"]
            and row["param_sweep_ok"]
        )
        per_task.append(row)

        bucket = by_difficulty[difficulty]
        bucket["task_count"] += 1
        bucket["attempts_total"] += row["attempts"]
        bucket["provider_error_count"] += row["provider_error_count"]
        bucket["simulation_repair_attempts"] += row["simulation_repair_attempts"]
        if row["simulation_ok"]:
            bucket["simulation_pass_count"] += 1
        if row["validator_ok"]:
            bucket["validator_ok_count"] += 1
        if row["semantic_ok"]:
            bucket["semantic_ok_count"] += 1
        if row["param_sweep_ok"]:
            bucket["param_sweep_ok_count"] += 1
        if row["param_sweep_dynamic_task"]:
            bucket["dynamic_task_count"] += 1
        if row["task_pass"]:
            bucket["task_pass_count"] += 1
        if row["first_pass_simulation_ok"]:
            bucket["first_pass_simulation_pass_count"] += 1

    by_difficulty_rows = []
    for difficulty in sorted(by_difficulty):
        bucket = by_difficulty[difficulty]
        count = bucket["task_count"]
        by_difficulty_rows.append(
            {
                **bucket,
                "difficulty": difficulty,
                "avg_attempts": bucket["attempts_total"] / count if count else 0.0,
            }
        )

    result = {
        "source_summary": str(summary_path),
        "task_count": len(per_task),
        "simulation_pass_count": sum(1 for row in per_task if row["simulation_ok"]),
        "validator_ok_count": sum(1 for row in per_task if row["validator_ok"]),
        "semantic_ok_count": sum(1 for row in per_task if row["semantic_ok"]),
        "param_sweep_ok_count": sum(1 for row in per_task if row["param_sweep_ok"]),
        "dynamic_task_count": sum(1 for row in per_task if row["param_sweep_dynamic_task"]),
        "task_pass_count": sum(1 for row in per_task if row["task_pass"]),
        "trace_present_count": sum(1 for row in per_task if row["trace_status"] == "present"),
        "by_difficulty": by_difficulty_rows,
        "per_task": per_task,
        "semantic_results": semantic_results,
    }

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "attribution-summary.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        (output_dir / "attribution-summary.md").write_text(
            _to_markdown(result),
            encoding="utf-8",
        )
    return result


def _to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Authoring Run Attribution",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| task_count | {result['task_count']} |",
        f"| simulation_pass_count | {result['simulation_pass_count']} |",
        f"| validator_ok_count | {result['validator_ok_count']} |",
        f"| semantic_ok_count | {result['semantic_ok_count']} |",
        f"| param_sweep_ok_count | {result['param_sweep_ok_count']} |",
        f"| dynamic_task_count | {result['dynamic_task_count']} |",
        f"| task_pass_count | {result['task_pass_count']} |",
        f"| trace_present_count | {result['trace_present_count']} |",
        "",
        "## By difficulty",
        "",
        "| Difficulty | Tasks | Sim Pass | Validator OK | Semantic OK | Param Sweep OK | Task Pass | First Pass | Provider Errors | Repair Attempts | Avg Attempts |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["by_difficulty"]:
        lines.append(
            "| {difficulty} | {task_count} | {simulation_pass_count} | {validator_ok_count} | "
            "{semantic_ok_count} | {param_sweep_ok_count} | {task_pass_count} | {first_pass_simulation_pass_count} | "
            "{provider_error_count} | {simulation_repair_attempts} | {avg_attempts:.2f} |".format(**row)
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    result = analyze_run(args.summary, args.tasks, args.output_dir)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "task_count",
                    "simulation_pass_count",
                    "validator_ok_count",
                    "semantic_ok_count",
                    "param_sweep_ok_count",
                    "dynamic_task_count",
                    "task_pass_count",
                    "trace_present_count",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
