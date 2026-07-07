"""Run an isolated Codex coding-agent authoring baseline.

This runner keeps the evaluated Codex process away from this repository. It
passes only one task prompt into an empty temporary working directory, then
copies the resulting package back for post-hoc scoring.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labscriptai.benchmark.authoring_pilot import (
    AUTHORING_SYSTEM_PROMPT,
    _prompt_hash,
    _simulator_summary,
    _write_record,
    _write_summary,
    repair_package_metadata,
    simulate_protocol_file,
)
from labscriptai.benchmark.derive_package import derive_package_from_protocol
from labscriptai.benchmark.package_validator import REQUIRED_PACKAGE_FILES, validate_package
from labscriptai.benchmark.score_record import score_record_from_validation
from labscriptai.benchmark.tasks import AuthoringTask, load_authoring_tasks
try:
    from native_agent_baseline_common import (
        SimulationRepairOutcome,
        build_rewrite_protocol_repairer,
        resolve_optional_repo_path,
        run_simulation_repair_loop,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style test imports.
    from scripts.native_agent_baseline_common import (
        SimulationRepairOutcome,
        build_rewrite_protocol_repairer,
        resolve_optional_repo_path,
        run_simulation_repair_loop,
    )


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "codex-cli-gpt-5.5"
SCAFFOLD_ID = "coding-agent-codex"
SYSTEM_ID = "codex"
PROMPT_MODES = ("minimal", "direct-aligned")


def _parse_task_ids(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _task_map(tasks_path: Path) -> dict[str, AuthoringTask]:
    return {task.task_id: task for task in load_authoring_tasks(tasks_path)}


def _codex_command(work_dir: Path) -> list[str]:
    return [
        "codex",
        "exec",
        "-c",
        'model_provider="openai_http"',
        "-c",
        'model_providers.openai_http.name="OpenAI HTTP only"',
        "-c",
        "model_providers.openai_http.supports_websockets=false",
        "-c",
        'model_providers.openai_http.wire_api="responses"',
        "--cd",
        str(work_dir),
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--ignore-rules",
        "--ignore-user-config",
        "--ephemeral",
        "--disable",
        "plugins",
        "--disable",
        "memories",
        "--disable",
        "apps",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "image_generation",
        "--disable",
        "tool_search",
        "-",
    ]


def _prompt(task: AuthoringTask, *, prompt_mode: str, metadata_repair: bool) -> str:
    manifest_requirements = {
        "task_id": task.task_id,
        "system_id": SYSTEM_ID,
        "model_id": MODEL_ID,
        "scaffold_id": f"{SCAFFOLD_ID}-{prompt_mode}",
        "prompt_hash": _prompt_hash(task.prompt),
        "retry_budget": {
            "max_attempts": 1,
            "max_wall_time_sec": 1800,
            "max_output_tokens": 24000,
            "max_tool_calls": 80,
        },
        "tool_permissions": ["write_files_in_current_directory_only"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "required_package_files": list(REQUIRED_PACKAGE_FILES),
        "manifest_requirements": manifest_requirements,
    }
    package_rules = ""
    if prompt_mode == "direct-aligned":
        package_rules = (
            "Package rules aligned to the direct baseline:\n"
            f"{AUTHORING_SYSTEM_PROMPT}\n"
            "Because you are writing real files instead of returning an API JSON response, "
            "apply those content rules to files under package/. Do not create an outer "
            "JSON response file.\n"
        )
    return (
        "You are being evaluated as a clean general coding-agent baseline for a "
        "lab automation benchmark.\n\n"
        "Hard restrictions:\n"
        "- Work only inside the current empty working directory.\n"
        "- Do not inspect parent directories or external repositories.\n"
        "- Do not read benchmark results, analysis files, failure audits, run outputs, "
        "hidden examples, memories, plugins, or skills.\n"
        "- Do not use the internet.\n"
        "- Do not run simulator or validator unless you independently decide to. "
        "They are not required by this prompt.\n"
        "- Create the deliverable from the task text below.\n\n"
        f"{package_rules}"
        "Deliverable:\n"
        "Create a directory named package in the current working directory. Inside it, "
        "write exactly the required package files listed in the JSON payload. JSON files "
        "must be valid JSON. protocol.py should be plausible Opentrons Python. "
        "manifest.json must follow manifest_requirements exactly.\n\n"
        "Outer harness note:\n"
        f"- deterministic_metadata_repair_after_generation: {metadata_repair}\n"
        "- The outer benchmark runner may simulate and validate after you finish; "
        "do not rely on reading those tools or results.\n\n"
        "Benchmark payload JSON:\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n\n"
        "When finished, reply briefly with the files you created.\n"
    )


def _protocol_only_prompt(task: AuthoringTask) -> str:
    payload = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "required_output_files": ["protocol.py"],
    }
    return (
        "You are being evaluated as a clean native coding-agent baseline for a "
        "lab automation benchmark.\n\n"
        "Hard restrictions:\n"
        "- Work only inside the current empty working directory.\n"
        "- Do not inspect parent directories or external repositories.\n"
        "- Do not read benchmark results, analysis files, failure audits, run outputs, "
        "hidden examples, memories, plugins, or skills.\n"
        "- Do not use the internet.\n"
        "- Do not run simulator or validator.\n"
        "- Create the deliverable only from the task text below.\n\n"
        "Deliverable:\n"
        "Create a directory named package in the current working directory. Inside it, "
        "write exactly one file: package/protocol.py.\n"
        "Do not create manifest.json or setup_card.html. The outer benchmark harness will "
        "derive those files from protocol.py after you finish.\n"
        "protocol.py should be plausible Opentrons Python with correct apiLevel placement "
        "and realistic labware, pipette, and transfer logic.\n\n"
        "Benchmark payload JSON:\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n\n"
        "When finished, reply briefly with the files you created.\n"
    )


def _parse_total_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s*\n?\s*([0-9][0-9,]*)", text)
    if not matches:
        matches = re.findall(r"tokens used\D+([0-9][0-9,]*)", text)
    if not matches:
        return 0
    return int(matches[-1].replace(",", ""))


def _read_manifest(package_dir: Path, task: AuthoringTask) -> dict[str, Any]:
    manifest_path = package_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(manifest, dict):
                return manifest
        except json.JSONDecodeError:
            pass
    return {
        "task_id": task.task_id,
        "system_id": SYSTEM_ID,
        "model_id": MODEL_ID,
        "scaffold_id": SCAFFOLD_ID,
    }


def _stamp_codex_manifest(package_dir: Path, task: AuthoringTask, *, prompt_mode: str) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
        except json.JSONDecodeError:
            manifest = {}
    manifest.update(
        {
            "task_id": task.task_id,
            "system_id": SYSTEM_ID,
            "model_id": MODEL_ID,
            "scaffold_id": f"{SCAFFOLD_ID}-{prompt_mode}",
            "prompt_hash": _prompt_hash(task.prompt),
            "retry_budget": {
                "max_attempts": 1,
                "max_wall_time_sec": 1800,
                "max_output_tokens": 24000,
                "max_tool_calls": 80,
            },
            "tool_permissions": manifest.get("tool_permissions")
            or ["write_files_in_current_directory_only"],
            "timestamp": manifest.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _copy_package(work_dir: Path, task_dir: Path) -> Path:
    src = work_dir / "package"
    dst = task_dir / "attempt1" / "package"
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)
    return dst


def _derive_sidecars(
    package_dir: Path,
    task: AuthoringTask,
    *,
    model_id: str,
    scaffold_id: str,
) -> dict[str, Any] | None:
    protocol_path = package_dir / "protocol.py"
    if not protocol_path.exists():
        return None
    return derive_package_from_protocol(
        package_dir,
        task,
        model_id=model_id,
        scaffold_id=scaffold_id,
        overwrite=True,
    )


def run_task(
    *,
    task: AuthoringTask,
    output_dir: Path,
    scratch_root: Path,
    timeout_sec: int,
    simulate: bool,
    opentrons_python: str | None,
    workspace_root: Path | None,
    simulation_timeout_sec: int,
    prompt_mode: str,
    metadata_repair: bool,
    protocol_only: bool,
    derive_scaffold_id: str,
    simulation_repair_attempts: int,
    repair_api_prefix: str,
    repair_model: str,
    repair_max_tokens: int,
) -> dict[str, Any]:
    task_dir = output_dir / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    work_dir = scratch_root / task.task_id
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    cmd = _codex_command(work_dir)
    started = time.monotonic()
    completed = subprocess.run(
        cmd,
        input=(
            _protocol_only_prompt(task)
            if protocol_only
            else _prompt(task, prompt_mode=prompt_mode, metadata_repair=metadata_repair)
        ),
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        cwd=str(work_dir),
        env=os.environ.copy(),
        check=False,
    )
    wall_time_sec = time.monotonic() - started
    stdout_path = task_dir / "codex.stdout.log"
    stderr_path = task_dir / "codex.stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    package_dir = _copy_package(work_dir, task_dir)
    total_tokens = _parse_total_tokens(completed.stdout + "\n" + completed.stderr)
    metadata_repairs: list[str] = []
    derive_info = None
    if protocol_only and package_dir.exists():
        derive_info = _derive_sidecars(
            package_dir,
            task,
            model_id=MODEL_ID,
            scaffold_id=derive_scaffold_id,
        )
    initial_validation = validate_package(
        package_dir,
        simulation_pass=False,
        task_manifest_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        task_id=task.task_id,
    )
    if metadata_repair and not protocol_only and package_dir.exists():
        _stamp_codex_manifest(package_dir, task, prompt_mode=prompt_mode)
        metadata_repairs = repair_package_metadata(package_dir)
    simulation_result: dict[str, Any] | None = None
    first_simulation: dict[str, Any] | None = None
    first_pass_validation = validate_package(
        package_dir,
        simulation_pass=False,
        task_manifest_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        task_id=task.task_id,
    )
    if simulate and package_dir.exists():
        simulation_result = simulate_protocol_file(
            package_dir / "protocol.py",
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            timeout_sec=simulation_timeout_sec,
        )
        first_simulation = simulation_result
        if simulation_repair_attempts > 0 and not simulation_result.get("ok"):
            repairer = build_rewrite_protocol_repairer(
                repair_api_prefix=repair_api_prefix,
                repair_model=repair_model,
                repair_max_tokens=repair_max_tokens,
            )
            repair_outcome = run_simulation_repair_loop(
                task=task,
                task_dir=task_dir,
                package_dir=package_dir,
                attempt=1,
                derive_info=derive_info,
                derive_from_protocol=protocol_only,
                derive_model_id=MODEL_ID,
                derive_scaffold_id=derive_scaffold_id,
                simulation_result=simulation_result,
                simulation_repair_attempts=simulation_repair_attempts,
                repairer=repairer,
                opentrons_python=opentrons_python,
                workspace_root=workspace_root,
                simulation_timeout_sec=simulation_timeout_sec,
            )
            package_dir = repair_outcome.package_dir
            derive_info = repair_outcome.derive_info
            simulation_result = repair_outcome.simulation_result
        else:
            repair_outcome = SimulationRepairOutcome(
                package_dir=package_dir,
                attempt=1,
                derive_info=derive_info,
                simulation_result=simulation_result,
                repair_attempts=0,
                repair_success=False,
                repair_errors=[],
                repair_input_tokens=0,
                repair_output_tokens=0,
                repair_total_tokens=0,
                repair_patch_count=0,
                repair_patch_rejected_count=0,
                repair_simulator_calls=0,
            )
    else:
        repair_outcome = SimulationRepairOutcome(
            package_dir=package_dir,
            attempt=1,
            derive_info=derive_info,
            simulation_result=simulation_result,
            repair_attempts=0,
            repair_success=False,
            repair_errors=[],
            repair_input_tokens=0,
            repair_output_tokens=0,
            repair_total_tokens=0,
            repair_patch_count=0,
            repair_patch_rejected_count=0,
            repair_simulator_calls=0,
        )

    simulation_pass = bool(simulation_result and simulation_result.get("ok"))
    validation = validate_package(
        package_dir,
        simulation_pass=simulation_pass,
        task_manifest_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        task_id=task.task_id,
    )
    manifest = _read_manifest(package_dir, task)
    score = score_record_from_validation(
        validation,
        manifest,
        first_pass=validation.ok and repair_outcome.repair_attempts == 0,
        attempts=repair_outcome.attempt,
        wall_time_sec=wall_time_sec,
        input_tokens=repair_outcome.repair_input_tokens,
        output_tokens=repair_outcome.repair_output_tokens,
    ).to_dict()
    total_tokens_with_repair = total_tokens + repair_outcome.repair_total_tokens

    record = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "package_dir": str(package_dir),
        "attempts": repair_outcome.attempt,
        "generation_attempts": 1,
        "provider_error_count": 0 if completed.returncode == 0 else 1,
        "wall_time_sec": wall_time_sec,
        "input_tokens": repair_outcome.repair_input_tokens,
        "output_tokens": repair_outcome.repair_output_tokens,
        "total_tokens": total_tokens_with_repair,
        "authoring_input_tokens": 0,
        "authoring_output_tokens": 0,
        "authoring_total_tokens": total_tokens,
        "repair_input_tokens": repair_outcome.repair_input_tokens,
        "repair_output_tokens": repair_outcome.repair_output_tokens,
        "repair_total_tokens": repair_outcome.repair_total_tokens,
        "repair_api_prefix": repair_api_prefix,
        "repair_model": repair_model,
        "repair_edit_mode": "rewrite",
        "repair_patch_backend": "rewrite",
        "repair_patch_count": repair_outcome.repair_patch_count,
        "repair_patch_rejected_count": repair_outcome.repair_patch_rejected_count,
        "codex_returncode": completed.returncode,
        "codex_command": cmd,
        "codex_work_dir": str(work_dir),
        "codex_stdout_log": str(stdout_path),
        "codex_stderr_log": str(stderr_path),
        "prompt_mode": prompt_mode,
        "protocol_only": protocol_only,
        "metadata_repair": metadata_repair,
        "derive": derive_info,
        "initial_validation": initial_validation.to_dict(),
        "repairs": metadata_repairs,
        "isolation": {
            "empty_work_dir": True,
            "ignore_user_config": True,
            "ignore_rules": True,
            "ephemeral": True,
            "disabled_features": [
                "plugins",
                "memories",
                "apps",
                "browser_use",
                "computer_use",
                "image_generation",
                "tool_search",
            ],
            "repo_path_not_in_prompt": True,
            "direct_aligned_package_rules": prompt_mode == "direct-aligned",
            "deterministic_metadata_repair_after_generation": metadata_repair,
            "protocol_only_harness_derives_sidecars": protocol_only,
        },
        "first_pass_validation": first_pass_validation.to_dict(),
        "validation": validation.to_dict(),
        "deterministic_checks_pass": validation.ok,
        "first_simulation": first_simulation,
        "simulation": simulation_result,
        "simulator_summary": _simulator_summary(simulation_result),
        "simulation_repair_attempts": repair_outcome.repair_attempts,
        "repair_success": repair_outcome.repair_success,
        "repair_errors": repair_outcome.repair_errors,
        "tool_calls": 0,
        "skill_loads": 0,
        "simulator_calls": (1 if first_simulation is not None else 0)
        + repair_outcome.repair_simulator_calls,
        "score": score,
    }
    if completed.returncode != 0:
        record["error"] = f"codex_returncode_{completed.returncode}"
    _write_record(task_dir, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=ROOT / "benchmarks" / "authoring" / "tasks.yaml")
    parser.add_argument("--task-ids", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, default=Path("/tmp/codex-authoring-baseline"))
    parser.add_argument("--timeout-sec", type=int, default=1800)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--opentrons-python")
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--simulation-timeout-sec", type=int, default=180)
    parser.add_argument("--prompt-mode", choices=PROMPT_MODES, default="minimal")
    parser.add_argument("--metadata-repair", action="store_true")
    parser.add_argument("--protocol-only", action="store_true")
    parser.add_argument("--derive-scaffold-id", default="codex-native-agent-py-derived-v0.4")
    parser.add_argument("--simulation-repair-attempts", type=int, default=0)
    parser.add_argument(
        "--repair-api-prefix",
        choices=("DEEPSEEK", "LLM_ONLY"),
        default="LLM_ONLY",
    )
    parser.add_argument("--repair-model", default="gpt-5.5")
    parser.add_argument("--repair-max-tokens", type=int, default=12000)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    args.simulation_repair_attempts = max(0, min(args.simulation_repair_attempts, 3))
    opentrons_python = resolve_optional_repo_path(args.opentrons_python)
    workspace_root = (
        Path(resolve_optional_repo_path(args.workspace_root))
        if args.workspace_root is not None
        else None
    )

    output_dir = args.output_dir.resolve()
    if args.force and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    args.scratch_root.mkdir(parents=True, exist_ok=True)

    tasks_by_id = _task_map(args.tasks)
    task_ids = _parse_task_ids(args.task_ids)
    records: list[dict[str, Any]] = []
    for task_id in task_ids:
        task = tasks_by_id[task_id]
        record = run_task(
            task=task,
            output_dir=output_dir,
            scratch_root=args.scratch_root,
            timeout_sec=args.timeout_sec,
            simulate=args.simulate,
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            simulation_timeout_sec=args.simulation_timeout_sec,
            prompt_mode=args.prompt_mode,
            metadata_repair=args.metadata_repair,
            protocol_only=args.protocol_only,
            derive_scaffold_id=args.derive_scaffold_id,
            simulation_repair_attempts=args.simulation_repair_attempts,
            repair_api_prefix=args.repair_api_prefix,
            repair_model=args.repair_model,
            repair_max_tokens=args.repair_max_tokens,
        )
        records.append(record)
        _write_summary(output_dir, MODEL_ID, records)

    summary = _write_summary(output_dir, MODEL_ID, records)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
