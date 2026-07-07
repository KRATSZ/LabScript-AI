"""Runtime smoke runner for real model/gatekeeper/trace checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labscriptai.benchmark.tasks import (
    AuthoringTask,
    load_authoring_tasks,
    select_stratified_tasks,
)

from .actions import CandidateAction
from .llm_queue_planner import CandidateProvider, LoopResult, ScriptedCandidateProvider, plan_action
from .model_adapter import OpenAICompatibleConfig, OpenAICompatibleCandidateProvider
from .state import RuntimeState


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def write_minimal_package(package_dir: Path, task: AuthoringTask, *, model_id: str) -> None:
    """Create a validator-clean package placeholder for loop smoke tests."""

    package_dir.mkdir(parents=True, exist_ok=True)
    prompt_hash = _prompt_hash(task.prompt)
    (package_dir / "protocol.py").write_text(
        'metadata = {"protocolName": "runtime smoke placeholder"}\n'
        "def run(protocol):\n"
        "    pass\n",
        encoding="utf-8",
    )
    (package_dir / "setup_card.html").write_text(
        f"# Runtime smoke package\n\nTask: {task.task_id}\n\nThis placeholder is for loop smoke tests only.\n",
        encoding="utf-8",
    )
    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "0.4",
                "task_id": task.task_id,
                "system_id": "labscriptai",
                "model_id": model_id,
                "scaffold_id": "runtime-smoke-placeholder",
                "prompt_hash": prompt_hash,
                "deck": {
                    "slots": [
                        {"name": "opentrons_96_wellplate_200ul_pcr_full_skirt", "slot": "D1"},
                        {"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"},
                    ],
                    "modules": [],
                    "instruments": [{"name": "flex_1channel_1000", "mount": "left"}],
                },
                "reagents": [
                    {
                        "name": "water",
                        "source": "reservoir:A1",
                        "required_volume_ul": 900,
                        "available_volume_ul": 1200,
                        "dead_volume_ul": 100,
                    }
                ],
                "tips": {"tips_required": 8, "tips_available": 96, "policy": "one_tip_per_sample"},
                "risk_flags": ["confirm liquid levels"],
                "critical_failures": [],
                "off_platform_handoff": {"declared": False},
                "tool_permissions": ["simulate_protocol"],
                "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _state_for_task(task: AuthoringTask) -> RuntimeState:
    return RuntimeState(
        run_id=f"smoke-{task.task_id.lower()}",
        phase="preflight",
        expected={
            "task_id": task.task_id,
            "difficulty": task.difficulty,
            "holdout": task.holdout,
            "prompt_hash": _prompt_hash(task.prompt),
            "prompt_excerpt": task.prompt[:900],
            "runtime_policy": "LLM may only propose JSON candidate actions; deterministic gatekeeper decides.",
            "holdout_note": "Hold-out is benchmark split metadata, not a reason to request human approval.",
        },
    )


def _result_record(task: AuthoringTask, result: LoopResult, trace_path: Path) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "source": task.source,
        "completed": result.completed,
        "final_phase": result.final_state.phase,
        "decision_statuses": [decision.status for decision in result.decisions],
        "decision_actions": [decision.action_type for decision in result.decisions],
        "trace_path": str(trace_path),
        "attempts": 1,
    }


def _failure_record(
    task: AuthoringTask,
    errors: list[str],
    trace_paths: list[Path],
) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "source": task.source,
        "completed": False,
        "final_phase": "error",
        "decision_statuses": [],
        "decision_actions": [],
        "trace_path": str(trace_paths[-1]) if trace_paths else "",
        "trace_paths": [str(path) for path in trace_paths],
        "attempts": len(errors),
        "error": errors[-1] if errors else "unknown error",
        "errors": errors,
    }


def run_runtime_smoke(
    *,
    tasks_path: Path,
    output_dir: Path,
    candidate_provider_factory: Callable[[AuthoringTask], CandidateProvider],
    model_id: str,
    per_level: int = 1,
    max_steps_per_task: int = 1,
    retry_attempts: int = 1,
    holdout_only: bool = True,
    prefer_new: bool = True,
) -> dict[str, Any]:
    tasks = select_stratified_tasks(
        load_authoring_tasks(tasks_path),
        per_level=per_level,
        holdout_only=holdout_only,
        prefer_new=prefer_new,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    if retry_attempts < 1:
        raise ValueError("retry_attempts must be >= 1")
    with tempfile.TemporaryDirectory(prefix="labscriptai-runtime-smoke-") as tmp:
        package_root = Path(tmp)
        for task in tasks:
            package_dir = package_root / task.task_id
            write_minimal_package(package_dir, task, model_id=model_id)
            errors: list[str] = []
            trace_paths: list[Path] = []
            for attempt in range(1, retry_attempts + 1):
                trace_path = output_dir / f"{task.task_id}.attempt{attempt}.trace.jsonl"
                trace_paths.append(trace_path)
                try:
                    result = plan_action(
                        initial_state=_state_for_task(task),
                        package_dir=package_dir,
                        trace_path=trace_path,
                        candidate_provider=candidate_provider_factory(task),
                        max_steps=max_steps_per_task,
                        simulation_pass=True,
                    )
                except Exception as exc:  # pragma: no cover - exercised through CLI/API failures.
                    errors.append(f"{type(exc).__name__}: {exc}")
                    continue
                record = _result_record(task, result, trace_path)
                record["attempts"] = attempt
                if attempt > 1:
                    record["prior_errors"] = errors
                    record["trace_paths"] = [str(path) for path in trace_paths]
                records.append(record)
                break
            else:
                records.append(_failure_record(task, errors, trace_paths))

    summary = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "task_count": len(records),
        "completed_count": sum(1 for record in records if record["completed"]),
        "blocked_count": sum(
            1 for record in records if "blocked" in record["decision_statuses"]
        ),
        "error_count": sum(1 for record in records if "error" in record),
        "total_attempts": sum(int(record.get("attempts", 0)) for record in records),
        "records": records,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _offline_factory(task: AuthoringTask) -> CandidateProvider:
    return ScriptedCandidateProvider(
        [
            CandidateAction(
                action_type="simulate_protocol",
                reason=f"Run simulator before execution for {task.task_id}.",
            )
        ]
    )


def _deepseek_factory(config: OpenAICompatibleConfig) -> Callable[[AuthoringTask], CandidateProvider]:
    def factory(task: AuthoringTask) -> CandidateProvider:
        del task
        return OpenAICompatibleCandidateProvider(config)

    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs/runtime-smoke/latest"))
    parser.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    parser.add_argument("--per-level", type=int, default=1)
    parser.add_argument("--max-steps-per-task", type=int, default=1)
    parser.add_argument("--retry-attempts", type=int, default=1)
    parser.add_argument("--include-train", action="store_true")
    parser.add_argument("--prefer-legacy", action="store_true")
    args = parser.parse_args(argv)

    if args.provider == "deepseek":
        config = OpenAICompatibleConfig.from_env()
        factory = _deepseek_factory(config)
        model_id = config.model
    else:
        factory = _offline_factory
        model_id = "offline-constant"

    summary = run_runtime_smoke(
        tasks_path=args.tasks,
        output_dir=args.output_dir,
        candidate_provider_factory=factory,
        model_id=model_id,
        per_level=args.per_level,
        max_steps_per_task=args.max_steps_per_task,
        retry_attempts=args.retry_attempts,
        holdout_only=not args.include_train,
        prefer_new=not args.prefer_legacy,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
