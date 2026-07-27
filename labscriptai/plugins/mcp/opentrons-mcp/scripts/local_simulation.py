"""Structured local Opentrons simulation helper for MCP use."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class WorkspacePaths:
    workspace_root: Path | None
    api_root: Path | None
    shared_data_root: Path | None

    @property
    def api_src(self) -> Path | None:
        return None if self.api_root is None else self.api_root / "src"

    @property
    def shared_data_python(self) -> Path | None:
        return None if self.shared_data_root is None else self.shared_data_root / "python"

    @property
    def source_layout_ready(self) -> bool:
        return bool(
            self.api_src
            and self.api_src.exists()
            and (self.api_src / "opentrons").exists()
            and self.shared_data_python
            and self.shared_data_python.exists()
        )


def resolve_workspace_paths(
    workspace_root: Path | None = None,
    api_root: Path | None = None,
    shared_data_root: Path | None = None,
) -> WorkspacePaths:
    root = workspace_root.resolve() if workspace_root else None
    resolved_api_root = api_root
    resolved_shared_data_root = shared_data_root

    if root is not None:
        resolved_api_root = resolved_api_root or (root / "opentrons" / "api")
        resolved_shared_data_root = resolved_shared_data_root or (
            root / "opentrons" / "shared-data"
        )

    return WorkspacePaths(
        workspace_root=root,
        api_root=resolved_api_root.resolve() if resolved_api_root else None,
        shared_data_root=resolved_shared_data_root.resolve()
        if resolved_shared_data_root
        else None,
    )


def build_bootstrap_code(module_name: str, use_source_layout: bool) -> str:
    if use_source_layout:
        return f"""
import runpy
import sys
import types

api_src = sys.argv[1]
shared_data_python = sys.argv[2]
forwarded_argv = sys.argv[3:]

sys.path.insert(0, api_src)
sys.path.insert(0, shared_data_python)

mod = types.ModuleType("opentrons._version")
mod.version = "0.0.0-dev"
sys.modules["opentrons._version"] = mod

sys.argv = ["{module_name}"] + forwarded_argv
runpy.run_module("{module_name}", run_name="__main__")
""".strip()

    return f"""
import runpy
import sys

forwarded_argv = sys.argv[1:]
sys.argv = ["{module_name}"] + forwarded_argv
runpy.run_module("{module_name}", run_name="__main__")
""".strip()


def build_probe_code(module_name: str, use_source_layout: bool) -> str:
    if use_source_layout:
        return f"""
import importlib
import json
import sys
import traceback
import types

api_src = sys.argv[1]
shared_data_python = sys.argv[2]
sys.path.insert(0, api_src)
sys.path.insert(0, shared_data_python)

mod = types.ModuleType("opentrons._version")
mod.version = "0.0.0-dev"
sys.modules["opentrons._version"] = mod

try:
    importlib.import_module("{module_name}")
except Exception as exc:
    print(json.dumps({{
        "ok": False,
        "module": "{module_name}",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }}))
else:
    print(json.dumps({{
        "ok": True,
        "module": "{module_name}",
    }}))
""".strip()

    return f"""
import importlib
import json
import traceback

try:
    importlib.import_module("{module_name}")
except Exception as exc:
    print(json.dumps({{
        "ok": False,
        "module": "{module_name}",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }}))
else:
    print(json.dumps({{
        "ok": True,
        "module": "{module_name}",
    }}))
""".strip()


def _subprocess_env() -> dict[str, str]:
    """Force UTF-8 stdout/stderr so simulate runlogs with µL do not fail on Windows GBK."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def probe_module(
    python_executable: str,
    paths: WorkspacePaths,
    module_name: str,
) -> dict[str, Any]:
    use_source_layout = paths.source_layout_ready
    probe_code = build_probe_code(module_name, use_source_layout)
    args = [python_executable, "-c", probe_code]
    if use_source_layout:
        args.extend([str(paths.api_src), str(paths.shared_data_python)])

    result = subprocess.run(args, capture_output=True, text=True, check=False, env=_subprocess_env())
    payload = result.stdout.strip() or result.stderr.strip()
    if not payload:
        return {
            "ok": False,
            "module": module_name,
            "error_type": "UnknownError",
            "error": "probe produced no output",
            "traceback": result.stderr,
        }

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "module": module_name,
            "error_type": "InvalidProbeOutput",
            "error": payload,
            "traceback": result.stderr,
        }


def choose_python(explicit_python: str | None) -> str:
    return explicit_python or sys.executable


def run_module(
    python_executable: str,
    paths: WorkspacePaths,
    module_name: str,
    forwarded_argv: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    use_source_layout = paths.source_layout_ready
    bootstrap_code = build_bootstrap_code(module_name, use_source_layout)
    args = [python_executable, "-c", bootstrap_code]
    if use_source_layout:
        args.extend([str(paths.api_src), str(paths.shared_data_python)])
    args.extend(forwarded_argv)
    return subprocess.run(args, capture_output=True, text=True, check=False, env=_subprocess_env())


def build_result(
    *,
    ok: bool,
    python_executable: str,
    module_name: str,
    paths: WorkspacePaths,
    protocol: str | None,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "python": python_executable,
        "module": module_name,
        "protocol": protocol,
        "workspace_root": str(paths.workspace_root) if paths.workspace_root else None,
        "api_root": str(paths.api_root) if paths.api_root else None,
        "shared_data_root": str(paths.shared_data_root)
        if paths.shared_data_root
        else None,
        "source_layout_ready": paths.source_layout_ready,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "error": error,
    }


def handle_doctor(args: argparse.Namespace) -> int:
    paths = resolve_workspace_paths(
        workspace_root=Path(args.workspace_root).resolve() if args.workspace_root else None,
        api_root=Path(args.api_root).resolve() if args.api_root else None,
        shared_data_root=Path(args.shared_data_root).resolve()
        if args.shared_data_root
        else None,
    )
    python_executable = choose_python(args.python)
    simulate_probe = probe_module(python_executable, paths, "opentrons.simulate")
    payload = {
        "ok": simulate_probe.get("ok", False),
        "python": python_executable,
        "workspace_root": str(paths.workspace_root) if paths.workspace_root else None,
        "api_root": str(paths.api_root) if paths.api_root else None,
        "shared_data_root": str(paths.shared_data_root)
        if paths.shared_data_root
        else None,
        "source_layout_ready": paths.source_layout_ready,
        "opentrons_simulate": simulate_probe,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def handle_simulate(args: argparse.Namespace) -> int:
    paths = resolve_workspace_paths(
        workspace_root=Path(args.workspace_root).resolve() if args.workspace_root else None,
        api_root=Path(args.api_root).resolve() if args.api_root else None,
        shared_data_root=Path(args.shared_data_root).resolve()
        if args.shared_data_root
        else None,
    )
    python_executable = choose_python(args.python)
    probe = probe_module(python_executable, paths, "opentrons.simulate")
    protocol_path = str(Path(args.protocol).resolve())

    if not probe.get("ok"):
        print(
            json.dumps(
                build_result(
                    ok=False,
                    python_executable=python_executable,
                    module_name="opentrons.simulate",
                    paths=paths,
                    protocol=protocol_path,
                    exit_code=None,
                    stdout="",
                    stderr="",
                    error=probe,
                ),
                ensure_ascii=False,
            )
        )
        return 0

    completed = run_module(
        python_executable,
        paths,
        "opentrons.simulate",
        [protocol_path, *args.extra_args],
    )
    print(
        json.dumps(
            build_result(
                ok=completed.returncode == 0,
                python_executable=python_executable,
                module_name="opentrons.simulate",
                paths=paths,
                protocol=protocol_path,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                error=None,
            ),
            ensure_ascii=False,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Structured local Opentrons simulation helper"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Probe local simulation imports")
    doctor.add_argument("--workspace-root", help="Workspace root containing opentrons/")
    doctor.add_argument("--api-root", help="Override path to opentrons/api")
    doctor.add_argument("--shared-data-root", help="Override path to opentrons/shared-data")
    doctor.add_argument("--python", help="Python interpreter to use")
    doctor.set_defaults(handler=handle_doctor)

    simulate = subparsers.add_parser("simulate", help="Run python -m opentrons.simulate")
    simulate.add_argument("protocol", help="Path to a protocol file")
    simulate.add_argument("--workspace-root", help="Workspace root containing opentrons/")
    simulate.add_argument("--api-root", help="Override path to opentrons/api")
    simulate.add_argument("--shared-data-root", help="Override path to opentrons/shared-data")
    simulate.add_argument("--python", help="Python interpreter to use")
    simulate.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to simulate. Use '--' before them.",
    )
    simulate.set_defaults(handler=handle_simulate)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
