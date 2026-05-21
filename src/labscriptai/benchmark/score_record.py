"""Score record helpers for the LabscriptAI authoring benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .package_validator import PackageValidationResult


@dataclass(frozen=True)
class ScoreRecord:
    task_id: str
    system_id: str
    model_id: str
    scaffold_id: str
    first_pass_success: bool
    best_of_budget_success: bool
    attempts: int
    wall_time_sec: float
    input_tokens: int | None
    output_tokens: int | None
    simulation_pass: bool
    package_complete: bool
    deck_consistency_score: float
    volume_feasibility_score: float
    tip_budget_score: float
    contamination_safety_score: float
    risk_flag_recall: float
    handoff_declared_score: float
    task_alignment_score: float | None = None
    biological_reasonableness_score: float | None = None
    liquid_handling_quality_score: float | None = None
    safety_control_score: float | None = None
    code_quality_score: float | None = None
    review_notes_path: str | None = None
    critical_failures: tuple[str, ...] = ()

    @property
    def expert_score_mean(self) -> float | None:
        scores = [
            self.task_alignment_score,
            self.biological_reasonableness_score,
            self.liquid_handling_quality_score,
            self.safety_control_score,
            self.code_quality_score,
        ]
        numeric_scores = [score for score in scores if score is not None]
        if not numeric_scores:
            return None
        return sum(numeric_scores) / len(numeric_scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "system_id": self.system_id,
            "model_id": self.model_id,
            "scaffold_id": self.scaffold_id,
            "first_pass_success": self.first_pass_success,
            "best_of_budget_success": self.best_of_budget_success,
            "attempts": self.attempts,
            "wall_time_sec": self.wall_time_sec,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "simulation_pass": self.simulation_pass,
            "package_complete": self.package_complete,
            "deck_consistency_score": self.deck_consistency_score,
            "volume_feasibility_score": self.volume_feasibility_score,
            "tip_budget_score": self.tip_budget_score,
            "contamination_safety_score": self.contamination_safety_score,
            "risk_flag_recall": self.risk_flag_recall,
            "handoff_declared_score": self.handoff_declared_score,
            "task_alignment_score": self.task_alignment_score,
            "biological_reasonableness_score": self.biological_reasonableness_score,
            "liquid_handling_quality_score": self.liquid_handling_quality_score,
            "safety_control_score": self.safety_control_score,
            "code_quality_score": self.code_quality_score,
            "expert_score_mean": self.expert_score_mean,
            "critical_failures": list(self.critical_failures),
            "review_notes_path": self.review_notes_path,
        }


def score_record_from_validation(
    validation: PackageValidationResult,
    manifest: Mapping[str, Any],
    *,
    first_pass: bool,
    attempts: int,
    wall_time_sec: float,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> ScoreRecord:
    success = validation.ok
    return ScoreRecord(
        task_id=str(manifest.get("task_id", "")),
        system_id=str(manifest.get("system_id", "")),
        model_id=str(manifest.get("model_id", "")),
        scaffold_id=str(manifest.get("scaffold_id", "")),
        first_pass_success=first_pass and success,
        best_of_budget_success=success,
        attempts=attempts,
        wall_time_sec=wall_time_sec,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        simulation_pass=validation.simulation_pass,
        package_complete=validation.package_complete,
        deck_consistency_score=validation.deck_consistency_score,
        volume_feasibility_score=validation.volume_feasibility_score,
        tip_budget_score=validation.tip_budget_score,
        contamination_safety_score=validation.contamination_safety_score,
        risk_flag_recall=validation.risk_flag_recall,
        handoff_declared_score=validation.handoff_declared_score,
        critical_failures=validation.critical_failures,
    )

