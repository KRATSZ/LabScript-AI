"""Run `python -m opentrons.cli analyze` on uploaded protocol files."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_THIS_FILE = Path(__file__).resolve()
_PYTHON_CANDIDATE_SUFFIXES = (
    Path("api/.venv/bin/python"),
    Path(".ot_env/bin/python"),
    Path("ot_env/bin/python"),
)


def _candidate_python_paths() -> list[Path]:
    candidates: list[Path] = []
    for base in (_THIS_FILE.parent, *_THIS_FILE.parents):
        for suffix in _PYTHON_CANDIDATE_SUFFIXES:
            candidate = base / suffix
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _failure_message(proc: subprocess.CompletedProcess[str], fallback: str) -> str:
    detail = proc.stderr.strip() or proc.stdout.strip()
    if detail:
        return detail
    if proc.returncode != 0:
        return f"Analyzer exited with status {proc.returncode}"
    return fallback


def resolve_python_executable() -> str:
    """Interpreter that has the Opentrons package (api venv in dev, or override)."""
    override = os.environ.get("OT_ANALYZE_PYTHON")
    if override:
        return override
    for candidate in _candidate_python_paths():
        if candidate.is_file():
            return str(candidate)
    return "python3"


def run_analyze(
    protocol_path: Path,
    extra_paths: list[Path],
    *,
    rtp_values_json: str | None = None,
    rtp_files_json: str | None = None,
    check: bool = False,
) -> dict[str, Any]:
    """
    Run analyzer; return parsed JSON object.

    extra_paths: additional files (e.g. custom labware JSON) passed as positional args.
    """
    python = resolve_python_executable()
    out_fd, out_path = tempfile.mkstemp(suffix=".json", prefix="pv-analyze-")
    os.close(out_fd)
    output_path = Path(out_path)

    try:
        cmd: list[str] = [
            python,
            "-I",
            "-m",
            "opentrons.cli",
            "analyze",
            f"--json-output={output_path}",
        ]
        if check:
            cmd.append("--check")
        if rtp_values_json:
            cmd.append(f"--rtp-values={rtp_values_json}")
        if rtp_files_json:
            cmd.append(f"--rtp-files={rtp_files_json}")

        cmd.append(str(protocol_path))
        for p in extra_paths:
            cmd.append(str(p))

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(protocol_path.parent),
            timeout=600,
        )
        if not output_path.is_file():
            raise RuntimeError(_failure_message(proc, "analyze produced no output file"))

        raw = output_path.read_text(encoding="utf-8")
        if raw.strip() == "":
            raise RuntimeError(_failure_message(proc, "analyze produced empty JSON output"))
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            detail = _failure_message(proc, "analyze returned malformed JSON")
            raise RuntimeError(f"Invalid JSON from analyzer: {e}. {detail}") from e
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
