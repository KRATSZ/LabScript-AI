"""Shared py-only native-agent authoring baseline runner.

This mirrors scripts/run_codex_authoring_baseline.py after the external agent
returns: copy package/, derive harness-owned sidecars, validate, simulate, and
write the same benchmark record shape.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labscriptai.benchmark.authoring_pilot import (
    AUTHORING_SYSTEM_PROMPT,
    PY_ONLY_AUTHORING_SYSTEM_PROMPT,
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


ROOT = Path(__file__).resolve().parents[1]
PROMPT_MODES = ("minimal", "direct-aligned")


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class NativeAgentSpec:
    system_id: str
    model_id: str
    scaffold_id: str
    log_prefix: str
    executable: str
    default_scratch_root: Path
    default_derive_scaffold_id: str
    command_builder: Callable[[Path, Path, str], list[str]]
    display_command: tuple[str, ...]
    disabled_features: tuple[str, ...]
    token_parser: Callable[[str], TokenUsage]
    env_remove_prefixes: tuple[str, ...] = ("LLM_ONLY_",)
    env_remove_keys: tuple[str, ...] = ()
    version_args: tuple[str, ...] = ("--version",)
    use_llm_only_anthropic_env: bool = False
    anthropic_model_id: str | None = None
    prompt_stdin: bool = False


def parse_regex_tokens(text: str) -> TokenUsage:
    matches = re.findall(r"tokens used\s*\n?\s*([0-9][0-9,]*)", text)
    if not matches:
        matches = re.findall(r"tokens used\D+([0-9][0-9,]*)", text)
    total = int(matches[-1].replace(",", "")) if matches else 0
    return TokenUsage(total_tokens=total)


def parse_claude_tokens(text: str) -> TokenUsage:
    usage = _json_usage(text)
    if usage.total_tokens:
        return usage
    input_match = re.findall(r'"input_tokens"\s*:\s*([0-9]+)', text)
    output_match = re.findall(r'"output_tokens"\s*:\s*([0-9]+)', text)
    input_tokens = sum(int(value) for value in input_match)
    output_tokens = sum(int(value) for value in output_match)
    total = input_tokens + output_tokens
    if total:
        return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total)
    return parse_regex_tokens(text)


def _json_usage(text: str) -> TokenUsage:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return TokenUsage()
    if not isinstance(payload, dict):
        return TokenUsage()
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return TokenUsage()
    input_tokens = _int_value(usage.get("input_tokens"))
    input_tokens += _int_value(usage.get("cache_creation_input_tokens"))
    input_tokens += _int_value(usage.get("cache_read_input_tokens"))
    output_tokens = _int_value(usage.get("output_tokens"))
    total_tokens = _int_value(usage.get("total_tokens")) or input_tokens + output_tokens
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _parse_task_ids(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _task_map(tasks_path: Path) -> dict[str, AuthoringTask]:
    return {task.task_id: task for task in load_authoring_tasks(tasks_path)}


def _prompt(
    task: AuthoringTask,
    *,
    spec: NativeAgentSpec,
    prompt_mode: str,
    metadata_repair: bool,
) -> str:
    manifest_requirements = {
        "task_id": task.task_id,
        "system_id": spec.system_id,
        "model_id": spec.model_id,
        "scaffold_id": f"{spec.scaffold_id}-{prompt_mode}",
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
        "Protocol authoring rules aligned to the direct py-only baseline:\n"
        f"{PY_ONLY_AUTHORING_SYSTEM_PROMPT}\n"
        "Additional protocol.py restrictions:\n"
        "- Do not import or call os, pathlib, subprocess, requests, urllib, IPython, "
        "Jupyter, notebook magics, or shell/system helpers.\n"
        "- Do not read external files, environment variables, parent directories, "
        "benchmark artifacts, simulator outputs, examples, skills, or repository code.\n"
        "- Keep all experiment parameters explicit in protocol.py.\n\n"
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


def _read_manifest(package_dir: Path, task: AuthoringTask, spec: NativeAgentSpec) -> dict[str, Any]:
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
        "system_id": spec.system_id,
        "model_id": spec.model_id,
        "scaffold_id": spec.scaffold_id,
    }


def _stamp_manifest(
    package_dir: Path,
    task: AuthoringTask,
    *,
    spec: NativeAgentSpec,
    prompt_mode: str,
) -> None:
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
            "system_id": spec.system_id,
            "model_id": spec.model_id,
            "scaffold_id": f"{spec.scaffold_id}-{prompt_mode}",
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
    spec: NativeAgentSpec,
    scaffold_id: str,
) -> dict[str, Any] | None:
    protocol_path = package_dir / "protocol.py"
    if not protocol_path.exists():
        return None
    return derive_package_from_protocol(
        package_dir,
        task,
        model_id=spec.model_id,
        scaffold_id=scaffold_id,
        overwrite=True,
    )


def _dotenv_values() -> dict[str, str]:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _agent_env(spec: NativeAgentSpec) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in _dotenv_values().items():
        env.setdefault(key, value)
    llm_only_base_url = env.get("LLM_ONLY_BASE_URL")
    llm_only_api_key = env.get("LLM_ONLY_API_KEY")
    for key in list(env):
        if any(key.startswith(prefix) for prefix in spec.env_remove_prefixes):
            env.pop(key, None)
    for key in spec.env_remove_keys:
        env.pop(key, None)
    if spec.use_llm_only_anthropic_env:
        if llm_only_base_url:
            env["ANTHROPIC_BASE_URL"] = llm_only_base_url.rstrip("/")
        if llm_only_api_key:
            env["ANTHROPIC_API_KEY"] = llm_only_api_key
        if spec.anthropic_model_id:
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = spec.anthropic_model_id
    return env


def _agent_env_audit(spec: NativeAgentSpec) -> dict[str, Any]:
    env = _agent_env(spec)
    return {
        "uses_llm_only_anthropic_env": spec.use_llm_only_anthropic_env,
        "anthropic_base_url": env.get("ANTHROPIC_BASE_URL"),
        "anthropic_api_key_present": bool(env.get("ANTHROPIC_API_KEY")),
        "anthropic_model_id": spec.anthropic_model_id,
    }


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _preflight(spec: NativeAgentSpec) -> dict[str, Any]:
    executable = shutil.which(spec.executable)
    info: dict[str, Any] = {
        "executable": spec.executable,
        "resolved_path": executable,
        "available": executable is not None,
        "model_id": spec.model_id,
    }
    if executable:
        try:
            completed = subprocess.run(
                [spec.executable, *spec.version_args],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
                env=_agent_env(spec),
            )
            info["version_returncode"] = completed.returncode
            info["version_stdout"] = completed.stdout.strip()
            info["version_stderr"] = completed.stderr.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            info["version_error"] = str(exc)
    return info


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
    spec: NativeAgentSpec,
) -> dict[str, Any]:
    task_dir = output_dir / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    work_dir = scratch_root / task.task_id
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    prompt = (
        _protocol_only_prompt(task)
        if protocol_only
        else _prompt(task, spec=spec, prompt_mode=prompt_mode, metadata_repair=metadata_repair)
    )
    prompt_path = work_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = spec.command_builder(work_dir, prompt_path, prompt)
    display_cmd = list(cmd)
    if display_cmd and display_cmd[-1] == prompt:
        display_cmd[-1] = prompt_path.name
    run_input = prompt if spec.prompt_stdin else None

    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            input=run_input,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            cwd=str(work_dir),
            env=_agent_env(spec),
            check=False,
        )
        wall_time_sec = time.monotonic() - started
    except subprocess.TimeoutExpired as exc:
        wall_time_sec = time.monotonic() - started
        completed = subprocess.CompletedProcess(
            cmd,
            124,
            stdout=_timeout_text(exc.stdout),
            stderr=(
                _timeout_text(exc.stderr)
                + f"\n{spec.log_prefix}_timeout_after_{timeout_sec}_sec\n"
            ),
        )
    stdout_path = task_dir / f"{spec.log_prefix}.stdout.log"
    stderr_path = task_dir / f"{spec.log_prefix}.stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    package_dir = _copy_package(work_dir, task_dir)
    usage = spec.token_parser(completed.stdout + "\n" + completed.stderr)
    metadata_repairs: list[str] = []
    derive_info = None
    if protocol_only and package_dir.exists():
        derive_info = _derive_sidecars(
            package_dir,
            task,
            spec=spec,
            scaffold_id=derive_scaffold_id,
        )
    initial_validation = validate_package(
        package_dir,
        simulation_pass=False,
        task_manifest_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        task_id=task.task_id,
    )
    if metadata_repair and not protocol_only and package_dir.exists():
        _stamp_manifest(package_dir, task, spec=spec, prompt_mode=prompt_mode)
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

    simulation_pass = bool(simulation_result and simulation_result.get("ok"))
    validation = validate_package(
        package_dir,
        simulation_pass=simulation_pass,
        task_manifest_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
        task_id=task.task_id,
    )
    manifest = _read_manifest(package_dir, task, spec)
    score = score_record_from_validation(
        validation,
        manifest,
        first_pass=validation.ok,
        attempts=1,
        wall_time_sec=wall_time_sec,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    ).to_dict()

    record = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "package_dir": str(package_dir),
        "attempts": 1,
        "generation_attempts": 1,
        "provider_error_count": 0 if completed.returncode == 0 else 1,
        "wall_time_sec": wall_time_sec,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        f"{spec.log_prefix}_returncode": completed.returncode,
        f"{spec.log_prefix}_command": display_cmd,
        f"{spec.log_prefix}_work_dir": str(work_dir),
        f"{spec.log_prefix}_stdout_log": str(stdout_path),
        f"{spec.log_prefix}_stderr_log": str(stderr_path),
        "native_agent": spec.system_id,
        "native_agent_model_id": spec.model_id,
        "native_agent_returncode": completed.returncode,
        "native_agent_command": display_cmd,
        "prompt_file": str(prompt_path),
        "prompt_mode": prompt_mode,
        "protocol_only": protocol_only,
        "metadata_repair": metadata_repair,
        "derive": derive_info,
        "initial_validation": initial_validation.to_dict(),
        "repairs": metadata_repairs,
        "isolation": {
            "empty_work_dir": True,
            "uses_current_repo_as_work_dir": False,
            "repo_path_not_in_prompt": True,
            "direct_aligned_package_rules": prompt_mode == "direct-aligned",
            "deterministic_metadata_repair_after_generation": metadata_repair,
            "protocol_only_harness_derives_sidecars": protocol_only,
            "env_removed_prefixes": list(spec.env_remove_prefixes),
            "env_removed_keys": list(spec.env_remove_keys),
            "agent_env": _agent_env_audit(spec),
            "disabled_features": list(spec.disabled_features),
            "tool_permissions": ["write_files_in_current_directory_only"],
        },
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
        "simulator_calls": 1 if simulation_result is not None else 0,
        "score": score,
    }
    if completed.returncode != 0:
        record["error"] = f"{spec.log_prefix}_returncode_{completed.returncode}"
    _write_record(task_dir, record)
    return record


def main(spec: NativeAgentSpec) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=ROOT / "benchmarks" / "authoring" / "tasks.yaml")
    parser.add_argument("--task-ids", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, default=spec.default_scratch_root)
    parser.add_argument("--timeout-sec", type=int, default=1800)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--opentrons-python")
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--simulation-timeout-sec", type=int, default=180)
    parser.add_argument("--prompt-mode", choices=PROMPT_MODES, default="minimal")
    parser.add_argument("--metadata-repair", action="store_true")
    parser.add_argument("--protocol-only", action="store_true")
    parser.add_argument("--derive-scaffold-id", default=spec.default_derive_scaffold_id)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    preflight = _preflight(spec)
    if not preflight["available"]:
        raise SystemExit(f"{spec.executable} is not available on PATH")

    output_dir = args.output_dir.resolve()
    if args.force and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    args.scratch_root.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{spec.log_prefix}-preflight.json").write_text(
        json.dumps(preflight, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

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
            opentrons_python=args.opentrons_python,
            workspace_root=args.workspace_root,
            simulation_timeout_sec=args.simulation_timeout_sec,
            prompt_mode=args.prompt_mode,
            metadata_repair=args.metadata_repair,
            protocol_only=args.protocol_only,
            derive_scaffold_id=args.derive_scaffold_id,
            spec=spec,
        )
        records.append(record)
        _write_summary(output_dir, spec.model_id, records)

    summary = _write_summary(output_dir, spec.model_id, records)
    print(json.dumps(summary, indent=2))
    return 0
