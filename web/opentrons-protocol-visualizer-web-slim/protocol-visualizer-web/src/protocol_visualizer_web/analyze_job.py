"""Materialize uploads to a temp directory and run `run_analyze` (sync, thread-pool safe)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from protocol_visualizer_web.analyze import run_analyze


def _validate_json_object(name: str, raw: str) -> None:
    try:
        v = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {name}: {e}") from e
    if not isinstance(v, dict):
        raise ValueError(f"{name} must be a JSON object")


def build_rtp_files_argument(
    rtp_files_map_json: str | None,
    csv_by_basename: dict[str, Path],
) -> str | None:
    """
    Build the CLI `--rtp-files` JSON from a map of RTP variable name -> client file basename,
    resolved to absolute paths under the temp directory.
    """
    if not rtp_files_map_json or not rtp_files_map_json.strip():
        if csv_by_basename:
            raise ValueError(
                "rtp_files_map is required when uploading RTP CSV files "
                '(JSON object mapping RTP names to uploaded file names, e.g. {"liquids": "liquids.csv"})'
            )
        return None
    _validate_json_object("rtp_files_map", rtp_files_map_json)
    mapping: dict[str, Any] = json.loads(rtp_files_map_json)
    resolved: dict[str, str] = {}
    for param, basename in mapping.items():
        if not isinstance(param, str) or not isinstance(basename, str):
            raise ValueError("rtp_files_map keys and values must be strings")
        base = Path(basename).name
        if base not in csv_by_basename:
            raise ValueError(
                f"rtp_files_map references file {base!r} but no uploaded CSV matched that name"
            )
        resolved[param] = str(csv_by_basename[base].resolve())
    return json.dumps(resolved)


def sync_analyze_from_uploads(
    protocol_filename: str,
    protocol_content: bytes,
    labware_files: list[tuple[str, bytes]],
    rtp_csv_files: list[tuple[str, bytes]],
    rtp_values: str | None,
    rtp_files_map: str | None,
    check: bool,
) -> dict[str, Any]:
    """
    Write protocol, optional labware JSON, optional RTP CSVs to a temp dir; run analyzer.
    """
    suffix = Path(protocol_filename).suffix.lower()
    if suffix not in (".py", ".json"):
        raise ValueError("Protocol must be a .py or .json file")

    if rtp_values and rtp_values.strip():
        _validate_json_object("rtp_values", rtp_values)

    tmp = Path(tempfile.mkdtemp(prefix="pv-upload-"))
    try:
        main_name = Path(protocol_filename).name
        protocol_path = tmp / main_name
        protocol_path.write_bytes(protocol_content)

        extra_paths: list[Path] = []
        if labware_files:
            lw_dir = tmp / "labware"
            lw_dir.mkdir()
            for name, content in labware_files:
                lp = lw_dir / Path(name).name
                lp.write_bytes(content)
                extra_paths.append(lp)

        csv_by_basename: dict[str, Path] = {}
        if rtp_csv_files:
            rtp_dir = tmp / "rtp_csv"
            rtp_dir.mkdir()
            for name, content in rtp_csv_files:
                base = Path(name).name
                dest = rtp_dir / base
                dest.write_bytes(content)
                csv_by_basename[base] = dest

        rtp_files_arg = build_rtp_files_argument(rtp_files_map, csv_by_basename)

        return run_analyze(
            protocol_path,
            extra_paths,
            rtp_values_json=rtp_values if (rtp_values and rtp_values.strip()) else None,
            rtp_files_json=rtp_files_arg,
            check=check,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
