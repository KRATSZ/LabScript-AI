"""Deterministic checks for LabscriptAI authoring benchmark packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .tasks import load_authoring_tasks
from .validators.core import (
    handoff_declared_score,
    read_json,
    validate_manifest,
    validate_protocol_syntax,
    validate_reagent_plan,
    validate_risk_checklist,
    validate_tip_plan,
)
from .validators.models import (
    REQUIRED_PACKAGE_FILES,
    CRITICAL_FAILURES,
    LEGACY_PACKAGE_FILES,
    PackageValidationResult,
    THREE_PIECE_PACKAGE_FILES,
    THREE_PIECE_SCHEMA_VERSION,
    ValidationIssue,
)
from .validators.opentrons import validate_deck_plan

__all__ = (
    "CRITICAL_FAILURES",
    "LEGACY_PACKAGE_FILES",
    "REQUIRED_PACKAGE_FILES",
    "THREE_PIECE_PACKAGE_FILES",
    "PackageValidationResult",
    "ValidationIssue",
    "validate_package",
)


def _manifest_schema_version(manifest: Any) -> str:
    if isinstance(manifest, Mapping):
        value = manifest.get("schema_version")
        if isinstance(value, str):
            return value
    return "0.3"


def _manifest_deck_plan(manifest: Any) -> Any:
    if not isinstance(manifest, Mapping):
        return None
    deck = manifest.get("deck")
    if not isinstance(deck, Mapping):
        return None
    deck_plan = dict(deck)
    if "labware" not in deck_plan and isinstance(deck.get("slots"), list):
        deck_plan["labware"] = deck["slots"]
    if "instruments" not in deck_plan and isinstance(deck.get("pipettes"), list):
        deck_plan["instruments"] = deck["pipettes"]
    return deck_plan


def _manifest_reagent_plan(manifest: Any) -> Any:
    if not isinstance(manifest, Mapping):
        return None
    return {"reagents": manifest.get("reagents", [])}


def _manifest_tip_plan(manifest: Any) -> Any:
    if not isinstance(manifest, Mapping):
        return None
    tips = manifest.get("tips")
    return tips if isinstance(tips, Mapping) else tips


def _manifest_risk_checklist(manifest: Any) -> Any:
    if not isinstance(manifest, Mapping):
        return None
    handoffs: list[Any] = []
    handoff = manifest.get("off_platform_handoff")
    if isinstance(handoff, Mapping):
        declared = handoff.get("declared")
        instrument = handoff.get("instrument")
        if declared and isinstance(instrument, str):
            handoffs.append(instrument)
    elif isinstance(handoff, list):
        handoffs.extend(handoff)
    critical_failures = manifest.get("critical_failures")
    if not isinstance(critical_failures, list):
        critical_failures = []
    return {
        "critical_failures": critical_failures,
        "risk_flags": manifest.get("risk_flags", []),
        "off_platform_handoffs": handoffs,
    }


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_declared_hashes(
    manifest: Any,
    root: Path,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(manifest, Mapping):
        return
    hashes = manifest.get("hashes")
    if not isinstance(hashes, Mapping):
        return
    targets = {
        "protocol_py": root / "protocol.py",
        "setup_card_html": root / "setup_card.html",
        "setup_card_md": root / "setup_card.md",
    }
    for key, path in targets.items():
        declared = hashes.get(key)
        if not isinstance(declared, str):
            continue
        actual = _sha256_file(path)
        if actual is None:
            continue
        if declared != actual:
            issues.append(
                ValidationIssue(
                    code="hash_mismatch",
                    message=f"manifest.hashes.{key} does not match {path.name}",
                    path=str(root / "manifest.json"),
                    critical_failure="schema_invalid",
                )
            )


def _resolve_task_expectations(
    *,
    task_manifest_path: Path | str | None,
    task_id_override: str | None,
    manifest: Any,
    expected_risk_flags: Sequence[str],
    expected_handoffs: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    risk = tuple(expected_risk_flags)
    handoffs = tuple(expected_handoffs)
    if not task_manifest_path:
        return risk, handoffs
    tasks = load_authoring_tasks(task_manifest_path)
    tid = task_id_override
    if not tid and isinstance(manifest, dict):
        raw = manifest.get("task_id")
        if isinstance(raw, str):
            tid = raw
    if not tid:
        return risk, handoffs
    for task in tasks:
        if task.task_id == tid:
            return (
                (*task.spec.expected_risk_flags, *risk),
                (*task.off_platform_handoff, *handoffs),
            )
    return risk, handoffs


def validate_package(
    package_dir: Path | str,
    *,
    simulation_pass: bool = False,
    expected_risk_flags: Sequence[str] = (),
    expected_handoffs: Sequence[str] = (),
    task_manifest_path: Path | str | None = None,
    task_id: str | None = None,
) -> PackageValidationResult:
    root = Path(package_dir).resolve()
    issues: list[ValidationIssue] = []
    loaded_json: dict[str, Any] = {}

    if not root.exists() or not root.is_dir():
        issues.append(
            ValidationIssue(
                code="package_dir_missing",
                message=f"Package directory does not exist: {root}",
                path=str(root),
                critical_failure="schema_invalid",
            )
        )
        return PackageValidationResult(
            package_dir=str(root),
            package_complete=False,
            simulation_pass=simulation_pass,
            deck_consistency_score=0.0,
            volume_feasibility_score=0.0,
            tip_budget_score=0.0,
            contamination_safety_score=0.0,
            risk_flag_recall=0.0,
            handoff_declared_score=0.0,
            issues=tuple(issues),
        )

    manifest_path = root / "manifest.json"
    manifest_obj = read_json(manifest_path, issues) if manifest_path.exists() else None
    schema_version = _manifest_schema_version(manifest_obj)
    required_files = (
        THREE_PIECE_PACKAGE_FILES
        if schema_version == THREE_PIECE_SCHEMA_VERSION
        else LEGACY_PACKAGE_FILES
    )
    if manifest_obj is not None:
        loaded_json["manifest.json"] = manifest_obj

    for file_name in required_files:
        path = root / file_name
        if not path.exists():
            issues.append(
                ValidationIssue(
                    code="missing_package_file",
                    message=f"Missing required package file: {file_name}",
                    path=str(path),
                    critical_failure="schema_invalid",
                )
            )
            continue
        if file_name.endswith(".json") and file_name not in loaded_json:
            loaded_json[file_name] = read_json(path, issues)

    protocol_path = root / "protocol.py"
    if protocol_path.exists():
        validate_protocol_syntax(protocol_path, issues)

    human_card_name = "setup_card.html" if schema_version == THREE_PIECE_SCHEMA_VERSION else "runbook.md"
    runbook_path = root / human_card_name
    if runbook_path.exists() and not runbook_path.read_text(encoding="utf-8").strip():
        issues.append(
            ValidationIssue(
                code="empty_setup_card" if schema_version == THREE_PIECE_SCHEMA_VERSION else "empty_runbook",
                message=f"{human_card_name} must include human setup instructions",
                path=str(runbook_path),
                critical_failure="schema_invalid",
            )
        )

    if "manifest.json" in loaded_json:
        validate_manifest(manifest_obj, root / "manifest.json", issues)
        _validate_declared_hashes(manifest_obj, root, issues)

    merged_risk, merged_handoffs = _resolve_task_expectations(
        task_manifest_path=task_manifest_path,
        task_id_override=task_id,
        manifest=manifest_obj,
        expected_risk_flags=expected_risk_flags,
        expected_handoffs=expected_handoffs,
    )

    deck_plan = (
        _manifest_deck_plan(manifest_obj)
        if schema_version == THREE_PIECE_SCHEMA_VERSION
        else loaded_json.get("deck_plan.json")
    )
    reagent_plan = (
        _manifest_reagent_plan(manifest_obj)
        if schema_version == THREE_PIECE_SCHEMA_VERSION
        else loaded_json.get("reagent_plan.json")
    )
    tip_plan = (
        _manifest_tip_plan(manifest_obj)
        if schema_version == THREE_PIECE_SCHEMA_VERSION
        else loaded_json.get("tip_plan.json")
    )
    risk_checklist = (
        _manifest_risk_checklist(manifest_obj)
        if schema_version == THREE_PIECE_SCHEMA_VERSION
        else loaded_json.get("risk_checklist.json")
    )

    deck_source_path = root / ("manifest.json" if schema_version == THREE_PIECE_SCHEMA_VERSION else "deck_plan.json")
    risk_source_path = root / ("manifest.json" if schema_version == THREE_PIECE_SCHEMA_VERSION else "risk_checklist.json")
    deck_score = validate_deck_plan(
        deck_plan,
        deck_source_path,
        issues,
        protocol_path=protocol_path,
    )
    volume_score = validate_reagent_plan(
        reagent_plan, root / ("manifest.json" if schema_version == THREE_PIECE_SCHEMA_VERSION else "reagent_plan.json"), issues
    )
    tip_score = validate_tip_plan(
        tip_plan,
        root / ("manifest.json" if schema_version == THREE_PIECE_SCHEMA_VERSION else "tip_plan.json"),
        issues,
    )
    contamination_score, risk_flag_recall = validate_risk_checklist(
        risk_checklist,
        risk_source_path,
        issues,
        expected_risk_flags=merged_risk,
    )
    handoff_score = handoff_declared_score(
        risk_checklist,
        merged_handoffs,
        risk_source_path,
        issues,
    )

    package_complete = all((root / file_name).exists() for file_name in required_files)
    return PackageValidationResult(
        package_dir=str(root),
        package_complete=package_complete,
        simulation_pass=simulation_pass,
        deck_consistency_score=deck_score,
        volume_feasibility_score=volume_score,
        tip_budget_score=tip_score,
        contamination_safety_score=contamination_score,
        risk_flag_recall=risk_flag_recall,
        handoff_declared_score=handoff_score,
        issues=tuple(issues),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a LabscriptAI protocol package")
    parser.add_argument("package_dir", help="Directory containing a v0.4 three-piece or legacy package")
    parser.add_argument(
        "--simulation-pass",
        action="store_true",
        help="Mark simulator/analyze as passed when composing the validation result",
    )
    parser.add_argument(
        "--expected-risk-flag",
        action="append",
        default=[],
        help="Expected risk flag from task spec; may be supplied multiple times",
    )
    parser.add_argument(
        "--expected-handoff",
        action="append",
        default=[],
        help="Expected off-platform handoff; may be supplied multiple times",
    )
    parser.add_argument(
        "--task-manifest",
        type=Path,
        default=None,
        help="Authoring task manifest (tasks.yaml); merge spec.expected_risk_flags and off_platform_handoff for the task",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Task id for manifest merge; defaults to manifest.json task_id when omitted",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_package(
        args.package_dir,
        simulation_pass=args.simulation_pass,
        expected_risk_flags=args.expected_risk_flag,
        expected_handoffs=args.expected_handoff,
        task_manifest_path=args.task_manifest,
        task_id=args.task_id,
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
