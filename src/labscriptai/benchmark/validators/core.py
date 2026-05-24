"""Platform-agnostic execution package checks (files, manifest, volumes, tips, risk)."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .models import BUDGET_LIMITS, CRITICAL_FAILURES, ValidationIssue
from .models import THREE_PIECE_MANIFEST_REQUIRED_FIELDS, THREE_PIECE_SCHEMA_VERSION


def read_json(path: Path, issues: list[ValidationIssue]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            ValidationIssue(
                code="json_parse_error",
                message=f"Could not parse JSON: {exc}",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    return None


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def first_present(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def iter_plan_items(plan: Any, list_key: str) -> list[Mapping[str, Any]]:
    if isinstance(plan, list):
        return [item for item in plan if isinstance(item, Mapping)]
    if isinstance(plan, Mapping):
        value = plan.get(list_key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        if isinstance(value, Mapping):
            return [item for item in value.values() if isinstance(item, Mapping)]
    return []


def validate_protocol_syntax(path: Path, issues: list[ValidationIssue]) -> None:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        issues.append(
            ValidationIssue(
                code="protocol_syntax_error",
                message=f"protocol.py is not valid Python: {exc}",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )


def validate_manifest(manifest: Any, path: Path, issues: list[ValidationIssue]) -> None:
    if not isinstance(manifest, Mapping):
        issues.append(
            ValidationIssue(
                code="manifest_not_object",
                message="manifest.json must be a JSON object",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
        return

    validate_three_piece_manifest(manifest, path, issues)


def validate_three_piece_manifest(
    manifest: Mapping[str, Any],
    path: Path,
    issues: list[ValidationIssue],
) -> None:
    for field_name in THREE_PIECE_MANIFEST_REQUIRED_FIELDS:
        if field_name not in manifest:
            issues.append(
                ValidationIssue(
                    code="manifest_missing_field",
                    message=f"manifest.json missing required field: {field_name}",
                    path=str(path),
                    critical_failure="schema_invalid",
                )
            )

    if manifest.get("schema_version") != THREE_PIECE_SCHEMA_VERSION:
        issues.append(
            ValidationIssue(
                code="manifest_schema_version_invalid",
                message=f"manifest.schema_version must be {THREE_PIECE_SCHEMA_VERSION}",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )

    if "deck" in manifest and not isinstance(manifest.get("deck"), Mapping):
        issues.append(
            ValidationIssue(
                code="manifest_deck_not_object",
                message="manifest.deck must be an object",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    if "reagents" in manifest and not isinstance(manifest.get("reagents"), list):
        issues.append(
            ValidationIssue(
                code="manifest_reagents_not_list",
                message="manifest.reagents must be a list",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    if "tips" in manifest and not isinstance(manifest.get("tips"), Mapping):
        issues.append(
            ValidationIssue(
                code="manifest_tips_not_object",
                message="manifest.tips must be an object",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    if "risk_flags" in manifest and not isinstance(manifest.get("risk_flags"), list):
        issues.append(
            ValidationIssue(
                code="manifest_risk_flags_not_list",
                message="manifest.risk_flags must be a list",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )

    budget = manifest.get("budget")
    if not isinstance(budget, Mapping):
        issues.append(
            ValidationIssue(
                code="budget_not_object",
                message="manifest.budget must be an object",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
        return

    limits = {
        "attempts": BUDGET_LIMITS["max_attempts"],
        "wall_min": BUDGET_LIMITS["max_wall_time_sec"] // 60,
        "tokens": BUDGET_LIMITS["max_output_tokens"],
    }
    for key, limit in limits.items():
        value = budget.get(key)
        if value is None:
            continue
        if not isinstance(value, int):
            issues.append(
                ValidationIssue(
                    code="budget_invalid",
                    message=f"manifest.budget.{key} must be an integer",
                    path=str(path),
                    critical_failure="schema_invalid",
                )
            )
        elif value > limit:
            issues.append(
                ValidationIssue(
                    code="budget_exceeds_limit",
                    message=f"manifest.budget.{key}={value} exceeds {limit}",
                    path=str(path),
                    critical_failure="schema_invalid",
                )
            )


def validate_reagent_plan(reagent_plan: Any, path: Path, issues: list[ValidationIssue]) -> float:
    items = iter_plan_items(reagent_plan, "reagents") or iter_plan_items(reagent_plan, "sources")
    if not items:
        return 1.0

    invalid = False
    for item in items:
        required = as_number(first_present(item, ("required_volume_ul", "total_required_ul")))
        available = as_number(first_present(item, ("available_volume_ul", "starting_volume_ul")))
        dead = as_number(item.get("dead_volume_ul")) or 0.0
        if required is None or available is None:
            continue
        if required < 0 or available < 0 or dead < 0:
            invalid = True
            issues.append(
                ValidationIssue(
                    code="negative_reagent_volume",
                    message="Reagent volumes must be non-negative",
                    path=str(path),
                    critical_failure="volume_infeasible",
                )
            )
        elif available < required + dead:
            invalid = True
            name = item.get("name") or item.get("id") or "reagent"
            issues.append(
                ValidationIssue(
                    code="reagent_underfill",
                    message=f"{name} has {available} uL available but needs {required + dead} uL including dead volume",
                    path=str(path),
                    critical_failure="reagent_underfill",
                )
            )
    return 0.0 if invalid else 1.0


def validate_tip_plan(tip_plan: Any, path: Path, issues: list[ValidationIssue]) -> float:
    if not isinstance(tip_plan, Mapping):
        issues.append(
            ValidationIssue(
                code="tip_plan_not_object",
                message="manifest.tips must be a JSON object",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
        return 0.0

    required = as_number(first_present(tip_plan, ("tips_required", "total_tip_usage", "wells_used")))
    available = as_number(first_present(tip_plan, ("tips_available", "max_tips_per_rack", "wells_total")))
    if required is None or available is None:
        nested = tip_plan.get("tips")
        if isinstance(nested, Mapping):
            required = required if required is not None else as_number(
                first_present(nested, ("tips_required", "total_tip_usage", "wells_used"))
            )
            available = available if available is not None else as_number(
                first_present(nested, ("tips_available", "max_tips_per_rack", "wells_total"))
            )
    if required is None or available is None:
        tip_racks = tip_plan.get("tip_racks")
        if isinstance(tip_racks, list):
            required_sum = 0.0
            available_sum = 0.0
            for rack in tip_racks:
                if not isinstance(rack, Mapping):
                    continue
                rack_required = as_number(
                    first_present(rack, ("tips_required", "total_tip_usage", "wells_used"))
                )
                if rack_required is None and isinstance(rack.get("tips_used"), list):
                    rack_required = float(len(rack["tips_used"]))
                rack_available = as_number(
                    first_present(rack, ("tips_available", "max_tips_per_rack", "wells_total"))
                )
                labware_name = rack.get("labware") or rack.get("type") or rack.get("name")
                if rack_available is None and isinstance(labware_name, str) and "96" in labware_name:
                    rack_available = 96.0
                if rack_required is not None:
                    required_sum += rack_required
                if rack_available is not None:
                    available_sum += rack_available
            if required is None and required_sum:
                required = required_sum
            if available is None and available_sum:
                available = available_sum
    if required is None or available is None:
        issues.append(
            ValidationIssue(
                code="tip_plan_missing_quantities",
                message="manifest.tips must declare tips_required/tips_available or supported aliases",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
        return 0.0
    if required > available:
        issues.append(
            ValidationIssue(
                code="tip_exhaustion",
                message=f"tip_plan requires {required:g} tips but only {available:g} are available",
                path=str(path),
                critical_failure="tip_exhaustion",
            )
        )
        return 0.0
    return 1.0


def normalize_risk_flag(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def iter_risk_flag_texts(value: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, Mapping):
        for key in ("flag", "name", "risk", "description", "mitigation", "note"):
            item = value.get(key)
            if isinstance(item, str):
                texts.append(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            texts.extend(iter_risk_flag_texts(item))
    return texts


def declared_risk_flag_texts(risk_checklist: Mapping[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in (
        "risk_flags",
        "risks",
        "expected_risk_flags",
        "manual_checks",
        "human_setup_risks",
        "unobservable_risks",
        "simulator_checkable_risks",
    ):
        if key in risk_checklist:
            texts.extend(iter_risk_flag_texts(risk_checklist[key]))
    return texts


def risk_flag_recall(risk_checklist: Any, expected_risk_flags: Sequence[str]) -> float:
    expected = [normalize_risk_flag(flag) for flag in expected_risk_flags if flag]
    if not expected:
        return 1.0
    if not isinstance(risk_checklist, Mapping):
        return 0.0
    declared = [
        normalize_risk_flag(text)
        for text in declared_risk_flag_texts(risk_checklist)
        if text
    ]
    if not declared:
        return 0.0
    hits = 0
    for expected_flag in expected:
        if any(
            expected_flag in declared_flag or declared_flag in expected_flag
            for declared_flag in declared
        ):
            hits += 1
    return hits / len(expected)


def validate_risk_checklist(
    risk_checklist: Any,
    path: Path,
    issues: list[ValidationIssue],
    *,
    expected_risk_flags: Sequence[str] = (),
) -> tuple[float, float]:
    declared: Sequence[Any] = ()
    if isinstance(risk_checklist, Mapping):
        value = risk_checklist.get("critical_failures")
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            declared = value
        else:
            issues.append(
                ValidationIssue(
                    code="risk_checklist_missing_critical_failures",
                    message="manifest.critical_failures must be a list",
                    path=str(path),
                    critical_failure="schema_invalid",
                )
            )
            return 0.0, 0.0
    else:
        issues.append(
            ValidationIssue(
                code="risk_checklist_not_object",
                message="manifest risk fields must be a JSON object or list as documented",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
        return 0.0, 0.0
    invalid = [failure for failure in declared if failure not in CRITICAL_FAILURES]
    for failure in invalid:
        issues.append(
            ValidationIssue(
                code="unknown_critical_failure",
                message=f"Unknown critical failure value: {failure}",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    recall = risk_flag_recall(risk_checklist, expected_risk_flags)
    return (0.0 if invalid else 1.0), recall


def declared_handoffs(risk_checklist: Any) -> set[str]:
    if not isinstance(risk_checklist, Mapping):
        return set()
    handoffs: set[str] = set()
    for key in ("off_platform_handoff", "off_platform_handoffs", "handoffs"):
        value = risk_checklist.get(key)
        for item in iter_risk_flag_texts(value):
            handoffs.add(normalize_risk_flag(item).replace(" ", "_"))
    return handoffs


def handoff_declared_score(
    risk_checklist: Any,
    expected_handoffs: Sequence[str],
    path: Path,
    issues: list[ValidationIssue],
) -> float:
    expected = {normalize_risk_flag(item).replace(" ", "_") for item in expected_handoffs if item}
    if not expected:
        return 1.0
    declared = declared_handoffs(risk_checklist)
    missing = sorted(expected - declared)
    for handoff in missing:
        issues.append(
            ValidationIssue(
                code="off_platform_handoff_missing",
                message=f"manifest must declare off-platform handoff: {handoff}",
                path=str(path),
                critical_failure="schema_invalid",
            )
        )
    return 1.0 if not missing else 0.0
