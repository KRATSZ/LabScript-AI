"""Pair module catalog for live_paired_v2."""

from __future__ import annotations

from importlib import import_module
from typing import Any

PAIR_MODULES = (
    "p1_tip_budget",
    "p2_backup_volume",
    "p3_overpressure",
    "p4_contamination",
    "p5_pause_window",
    "p6_evidence_abstain",
)

_PKG = "benchmarks.runtime.live_paired_v2.pairs"


def load_pair_module(name: str) -> Any:
    return import_module(f"{_PKG}.{name}")


def load_implemented_pairs() -> list[Any]:
    modules = []
    for name in PAIR_MODULES:
        mod = load_pair_module(name)
        if getattr(mod, "IMPLEMENTED", False):
            modules.append(mod)
    return modules


def list_pending_pairs() -> list[dict[str, Any]]:
    pending = []
    for name in PAIR_MODULES:
        mod = load_pair_module(name)
        if not getattr(mod, "IMPLEMENTED", False):
            pending.append(mod.pair_definition())
    return pending


__all__ = [
    "PAIR_MODULES",
    "list_pending_pairs",
    "load_implemented_pairs",
    "load_pair_module",
]
