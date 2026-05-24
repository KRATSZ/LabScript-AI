"""Shared types and constants for package validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


THREE_PIECE_SCHEMA_VERSION = "0.4"

THREE_PIECE_PACKAGE_FILES = (
    "protocol.py",
    "setup_card.html",
    "manifest.json",
)

REQUIRED_PACKAGE_FILES = THREE_PIECE_PACKAGE_FILES

CRITICAL_FAILURES = (
    "collision",
    "tip_exhaustion",
    "deck_conflict",
    "reagent_underfill",
    "cross_contamination",
    "volume_infeasible",
    "module_misuse",
    "schema_invalid",
    "other",
)

THREE_PIECE_MANIFEST_REQUIRED_FIELDS = (
    "schema_version",
    "deck",
    "reagents",
    "tips",
    "risk_flags",
    "tool_permissions",
    "budget",
)

BUDGET_LIMITS = {
    "max_attempts": 8,
    "max_wall_time_sec": 1800,
    "max_output_tokens": 24000,
    "max_tool_calls": 80,
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    path: str | None = None
    critical_failure: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.path:
            payload["path"] = self.path
        if self.critical_failure:
            payload["critical_failure"] = self.critical_failure
        return payload


@dataclass(frozen=True)
class PackageValidationResult:
    package_dir: str
    package_complete: bool
    simulation_pass: bool
    deck_consistency_score: float
    volume_feasibility_score: float
    tip_budget_score: float
    contamination_safety_score: float
    risk_flag_recall: float
    handoff_declared_score: float
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.package_complete and self.simulation_pass and not self.critical_failures

    @property
    def critical_failures(self) -> tuple[str, ...]:
        failures = {
            issue.critical_failure
            for issue in self.issues
            if issue.severity == "error" and issue.critical_failure
        }
        return tuple(failure for failure in CRITICAL_FAILURES if failure in failures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "package_dir": self.package_dir,
            "package_complete": self.package_complete,
            "simulation_pass": self.simulation_pass,
            "deck_consistency_score": self.deck_consistency_score,
            "volume_feasibility_score": self.volume_feasibility_score,
            "tip_budget_score": self.tip_budget_score,
            "contamination_safety_score": self.contamination_safety_score,
            "risk_flag_recall": self.risk_flag_recall,
            "handoff_declared_score": self.handoff_declared_score,
            "critical_failures": list(self.critical_failures),
            "issues": [issue.to_dict() for issue in self.issues],
        }
