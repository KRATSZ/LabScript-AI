"""Offline simulator/package validation adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...benchmark.package_validator import validate_package


def simulate_protocol_package(package_dir: Path | str, *, simulation_pass: bool = False) -> dict[str, Any]:
    """Return a trace-friendly validation payload.

    The first MVP keeps actual Opentrons analyze/simulate as an injectable concern.
    Passing ``simulation_pass=True`` is useful for offline loop tests where the
    package validator is the only deterministic tool under test.
    """

    result = validate_package(package_dir, simulation_pass=simulation_pass)
    return result.to_dict()

