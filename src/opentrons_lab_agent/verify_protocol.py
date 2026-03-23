"""Helpers for checking and invoking local Opentrons analyze/simulate entry points."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class WorkspacePaths:
    workspace_root: Path
    api_root: Path
    shared_data_root: Path

    @property
    def api_src(self) -> Path:
        return self.api_root / "src"

    @property
    def shared_data_python(self) -> Path:
        return self.shared_data_root / "python"

    @property
    def default_python(self) -> Path:
        return self.api_root / ".venv" / "bin" / "python"


def discover_workspace_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "opentrons" / "api" / "src" / "opentrons").exists():
            return candidate
    return None


def resolve_workspace_paths(
    workspace_root: Path | None = None,
    api_root: Path | None = None,
    shared_data_root: Path | None = None,
) -> WorkspacePaths:
    root = workspace_root or discover_workspace_root()
    if root is None:
        raise SystemExit(
            "could not locate workspace root containing opentrons/api/src/opentrons"
        )

    resolved_api_root = api_root or (root / "opentrons" / "api")
    resolved_shared_data_root = shared_data_root or (root / "opentrons" / "shared-data")

    return WorkspacePaths(
        workspace_root=root,
        api_root=resolved_api_root.resolve(),
        shared_data_root=resolved_shared_data_root.resolve(),
    )


def build_bootstrap_code(module_name: str) -> str:
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


def probe_module(
    python_executable: str,
    paths: WorkspacePaths,
    module_name: str,
) -> dict[str, Any]:
    probe_code = f"""
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
        "python": sys.executable,
        "module": "{module_name}",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }}))
else:
    print(json.dumps({{
        "ok": True,
        "python": sys.executable,
        "module": "{module_name}",
    }}))
""".strip()

    result = subprocess.run(
        [
            python_executable,
            "-c",
            probe_code,
            str(paths.api_src),
            str(paths.shared_data_python),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = result.stdout.strip() or result.stderr.strip()
    if not payload:
        return {
            "ok": False,
            "python": python_executable,
            "module": module_name,
            "error_type": "UnknownError",
            "error": "probe produced no output",
            "traceback": result.stderr,
        }
    return json.loads(payload)


def run_module(
    python_executable: str,
    paths: WorkspacePaths,
    module_name: str,
    forwarded_argv: Sequence[str],
) -> int:
    bootstrap_code = build_bootstrap_code(module_name)
    completed = subprocess.run(
        [
            python_executable,
            "-c",
            bootstrap_code,
            str(paths.api_src),
            str(paths.shared_data_python),
            *forwarded_argv,
        ],
        check=False,
    )
    return completed.returncode


def choose_python(paths: WorkspacePaths, explicit_python: str | None) -> str:
    if explicit_python:
        return explicit_python
    if paths.default_python.exists():
        return str(paths.default_python)
    return sys.executable


def handle_doctor(args: argparse.Namespace) -> int:
    paths = resolve_workspace_paths(
        workspace_root=Path(args.workspace_root).resolve() if args.workspace_root else None,
        api_root=Path(args.api_root).resolve() if args.api_root else None,
        shared_data_root=Path(args.shared_data_root).resolve()
        if args.shared_data_root
        else None,
    )
    python_executable = choose_python(paths, args.python)
    analyze_probe = probe_module(python_executable, paths, "opentrons.cli")
    simulate_probe = probe_module(python_executable, paths, "opentrons.simulate")
    summary = {
        "workspace_root": str(paths.workspace_root),
        "api_root": str(paths.api_root),
        "shared_data_root": str(paths.shared_data_root),
        "python": python_executable,
        "opentrons_cli": analyze_probe,
        "opentrons_simulate": simulate_probe,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _handle_execution(args: argparse.Namespace, module_name: str, argv_prefix: list[str]) -> int:
    paths = resolve_workspace_paths(
        workspace_root=Path(args.workspace_root).resolve() if args.workspace_root else None,
        api_root=Path(args.api_root).resolve() if args.api_root else None,
        shared_data_root=Path(args.shared_data_root).resolve()
        if args.shared_data_root
        else None,
    )
    python_executable = choose_python(paths, args.python)
    probe = probe_module(python_executable, paths, module_name)
    if not probe.get("ok"):
        print(json.dumps(probe, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2
    forwarded_argv = argv_prefix + [args.protocol, *args.extra_args]
    return run_module(python_executable, paths, module_name, forwarded_argv)


def handle_analyze(args: argparse.Namespace) -> int:
    return _handle_execution(args, "opentrons.cli", ["analyze"])


def handle_simulate(args: argparse.Namespace) -> int:
    return _handle_execution(args, "opentrons.simulate", [])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check and invoke local Opentrons analyze/simulate entry points"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Report whether local imports are runnable")
    doctor.add_argument("--workspace-root", help="Workspace root containing opentrons/")
    doctor.add_argument("--api-root", help="Override path to opentrons/api")
    doctor.add_argument("--shared-data-root", help="Override path to opentrons/shared-data")
    doctor.add_argument("--python", help="Python interpreter to use")
    doctor.set_defaults(handler=handle_doctor)

    analyze = subparsers.add_parser("analyze", help="Run opentrons.cli analyze")
    analyze.add_argument("protocol", help="Path to a protocol file or bundle directory")
    analyze.add_argument("--workspace-root", help="Workspace root containing opentrons/")
    analyze.add_argument("--api-root", help="Override path to opentrons/api")
    analyze.add_argument("--shared-data-root", help="Override path to opentrons/shared-data")
    analyze.add_argument("--python", help="Python interpreter to use")
    analyze.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to analyze. Use '--' before them.",
    )
    analyze.set_defaults(handler=handle_analyze)

    simulate = subparsers.add_parser("simulate", help="Run python -m opentrons.simulate")
    simulate.add_argument("protocol", help="Path to a protocol file or bundle directory")
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

