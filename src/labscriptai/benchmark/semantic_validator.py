"""Lightweight semantic oracle for authoring benchmark packages.

This module is intentionally separate from package_validator. The package
validator answers "is this package complete and simulator-compatible?". The
semantic oracle answers "does this package appear to implement task-specific
experimental intent?" with deterministic, auditable rules.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Iterable
from typing import Any, Mapping

from .package_validator import REQUIRED_PACKAGE_FILES
from .tasks import AuthoringTask, load_authoring_tasks
from .validators.core import as_number, first_present, iter_plan_items


@dataclass(frozen=True)
class SemanticIssue:
    code: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass(frozen=True)
class SemanticValidationResult:
    package_dir: str
    task_id: str
    ok: bool
    score: float
    checks: dict[str, bool]
    issues: tuple[SemanticIssue, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "package_dir": self.package_dir,
            "task_id": self.task_id,
            "checks": self.checks,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ParamSweepResult:
    package_dir: str
    task_id: str
    dynamic_task: bool
    ok: bool
    checks: dict[str, bool]
    issues: tuple[SemanticIssue, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dynamic_task": self.dynamic_task,
            "package_dir": self.package_dir,
            "task_id": self.task_id,
            "checks": self.checks,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _read_package_text(package_dir: Path) -> str:
    parts: list[str] = []
    for file_name in REQUIRED_PACKAGE_FILES:
        path = package_dir / file_name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts).lower()


def _prompt_volumes(prompt: str) -> list[str]:
    volumes: list[str] = []
    for match in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:uL|µL|ul|microliters?)\b", prompt):
        value = match.group(1)
        normalized = value[:-2] if value.endswith(".0") else value
        if normalized not in volumes:
            volumes.append(normalized)
    return volumes


def _contains_volume(package_text: str, volume: str) -> bool:
    escaped = re.escape(volume)
    return re.search(rf"\b{escaped}(?:\.0)?\s*(?:ul|µl|microliters?)?\b", package_text) is not None


def _json_object(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _manifest_object(package_dir: Path) -> Mapping[str, Any] | None:
    loaded = _json_object(package_dir / "manifest.json")
    if isinstance(loaded, Mapping) and loaded.get("schema_version") == "0.4":
        return loaded
    return None


def _tip_plan_object(package_dir: Path) -> Mapping[str, Any] | None:
    manifest = _manifest_object(package_dir)
    if manifest is None:
        return None
    tips = manifest.get("tips")
    return tips if isinstance(tips, Mapping) else None


def _reagent_plan_object(package_dir: Path) -> Any:
    manifest = _manifest_object(package_dir)
    if manifest is None:
        return None
    return {"reagents": manifest.get("reagents", [])}


def _tip_plan_has_quantity(package_dir: Path) -> bool:
    loaded = _tip_plan_object(package_dir)
    if not isinstance(loaded, dict):
        return False
    if _collect_tip_required(loaded) or _collect_tip_available(loaded):
        return True
    quantities = loaded.get("quantities")
    if isinstance(quantities, dict):
        return any(isinstance(value, (int, float)) and value > 0 for value in quantities.values())
    return False


TIP_REQUIRED_KEYS = (
    "tips_required",
    "total_tips_required",
    "tips_required_total",
    "total_tip_usage",
    "wells_used",
    "tips_used",
)

TIP_AVAILABLE_KEYS = (
    "tips_available",
    "total_tips_available",
    "tips_available_total",
    "max_tips_per_rack",
    "wells_total",
)

REAGENT_VOLUME_KEYS = (
    "required_volume_ul",
    "required_volume_uL",
    "total_required_ul",
    "total_required_volume_ul",
    "total_required_volume_uL",
    "total_volume_ul",
    "total_volume_uL",
    "volume_required_ul",
    "total_volume_required",
    "total_volume_required_ul",
    "total_volume_needed_ul",
    "total_required_volume",
    "minimum_volume_needed",
    "volume_used_ul",
    "total_volume_used_ul",
    "total_transfer_volume_ul",
    "required_with_dead_ul",
)

CANONICAL_REAGENT_TOTAL_KEYS = (
    "required_volume_ul",
    "required_volume_uL",
    "total_volume_ul",
    "total_volume_uL",
)


def _positive_number(value: Any) -> float | None:
    number = as_number(value)
    if number is None or number <= 0:
        return None
    return number


def _extend_candidate(candidates: list[float], value: Any) -> None:
    number = _positive_number(value)
    if number is not None:
        candidates.append(number)


def _iter_mapping_values(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for item in value.values():
            if isinstance(item, Mapping):
                yield item
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, Mapping):
                yield item


def _sum_from_items(value: Any, keys: tuple[str, ...]) -> float | None:
    total = 0.0
    matched = False
    for item in _iter_mapping_values(value):
        direct = as_number(first_present(item, keys))
        if direct is not None:
            total += direct
            matched = True
            continue
        tips_used = item.get("tips_used")
        if isinstance(tips_used, list):
            total += len(tips_used)
            matched = True
    return total if matched and total > 0 else None


def _collect_tip_required(loaded: Mapping[str, Any]) -> list[float]:
    """Collect all plausible required-tip counts and let the caller choose.

    Some model outputs contain a small top-level placeholder, for example
    ``tips_required: 1``, plus a richer nested plan. Returning every candidate
    and taking the maximum prevents the placeholder from hiding the real count.
    """

    candidates: list[float] = []
    for key in TIP_REQUIRED_KEYS:
        _extend_candidate(candidates, loaded.get(key))
    for nested_key in ("tips", "tip_plan"):
        nested = loaded.get(nested_key)
        if isinstance(nested, Mapping):
            for key in TIP_REQUIRED_KEYS:
                _extend_candidate(candidates, nested.get(key))
    for container_key in ("tip_racks", "pipettes", "tip_usage", "usage"):
        total = _sum_from_items(loaded.get(container_key), TIP_REQUIRED_KEYS)
        if total is not None:
            candidates.append(total)
    return candidates


def _collect_tip_available(loaded: Mapping[str, Any]) -> list[float]:
    candidates: list[float] = []
    for key in TIP_AVAILABLE_KEYS:
        _extend_candidate(candidates, loaded.get(key))
    for nested_key in ("tips", "tip_plan"):
        nested = loaded.get(nested_key)
        if isinstance(nested, Mapping):
            for key in TIP_AVAILABLE_KEYS:
                _extend_candidate(candidates, nested.get(key))
    for container_key in ("tip_racks", "pipettes"):
        total = _sum_from_items(loaded.get(container_key), TIP_AVAILABLE_KEYS)
        if total is not None:
            candidates.append(total)
        for item in _iter_mapping_values(loaded.get(container_key)):
            labware = item.get("labware") or item.get("type") or item.get("name") or item.get("tiprack")
            if isinstance(labware, str) and "96" in labware:
                candidates.append(96.0)
    return candidates


def _tip_plan_required_available(package_dir: Path) -> tuple[float | None, float | None]:
    loaded = _tip_plan_object(package_dir)
    if not isinstance(loaded, Mapping):
        return None, None
    required_candidates = _collect_tip_required(loaded)
    available_candidates = _collect_tip_available(loaded)
    required = max(required_candidates) if required_candidates else None
    available = max(available_candidates) if available_candidates else None
    return required, available


def _required_reagent_volumes(task: AuthoringTask) -> dict[str, float]:
    if not task.spec.default_samples:
        return {}
    required: dict[str, float] = {}
    for reagent in task.spec.reagents:
        if reagent.volume_per_sample_uL is None:
            continue
        required[reagent.name.lower()] = task.spec.default_samples * reagent.volume_per_sample_uL
    return required


def _plan_reagent_items(package_dir: Path) -> list[Mapping[str, Any]]:
    loaded = _reagent_plan_object(package_dir)
    if loaded is None:
        return []
    return iter_plan_items(loaded, "reagents") or iter_plan_items(loaded, "sources")


def _named_plan_reagent_items(package_dir: Path) -> list[Mapping[str, Any]]:
    loaded = _reagent_plan_object(package_dir)
    if loaded is None:
        return []
    if isinstance(loaded, Mapping):
        for key in ("reagents", "sources"):
            value = loaded.get(key)
            if isinstance(value, Mapping):
                items: list[Mapping[str, Any]] = []
                for name, item in value.items():
                    if isinstance(item, Mapping):
                        normalized = dict(item)
                        normalized.setdefault("name", str(name))
                        items.append(normalized)
                if items:
                    return items
    return _plan_reagent_items(package_dir)


def _matches_reagent_name(expected_name: str, item: Mapping[str, Any]) -> bool:
    raw = item.get("name") or item.get("id") or item.get("reagent") or item.get("label")
    if not isinstance(raw, str):
        return False
    expected = expected_name.lower().replace("_", " ")
    actual = raw.lower().replace("_", " ")
    if expected in actual or actual in expected:
        return True
    expected_tokens = {token for token in expected.split() if len(token) >= 4}
    actual_tokens = {token for token in actual.split() if len(token) >= 4}
    return bool(expected_tokens & actual_tokens)


def _matching_reagent_volume_status(
    items: list[Mapping[str, Any]],
    expected_name: str,
    expected_volume: float,
    *,
    enforce_upper_bound: bool,
) -> tuple[bool, bool]:
    lower_ok = False
    upper_ok = True
    for item in items:
        if not _matches_reagent_name(expected_name, item):
            continue
        value = as_number(
            first_present(
                item,
                REAGENT_VOLUME_KEYS,
            )
        )
        if value is not None and value >= expected_volume * 0.95:
            lower_ok = True
        canonical_value = as_number(first_present(item, CANONICAL_REAGENT_TOTAL_KEYS))
        if enforce_upper_bound and canonical_value is not None and canonical_value > expected_volume * 1.25:
            upper_ok = False
    return lower_ok, upper_ok


def _reagent_total_upper_bound_is_exact(task: AuthoringTask) -> bool:
    prompt = task.prompt.lower()
    ambiguous_terms = (
        "plus standards",
        "plus standard",
        "standard curve",
        "calibrator",
    )
    return not any(term in prompt for term in ambiguous_terms)


def _uses_dynamic_inputs(task: AuthoringTask) -> bool:
    prompt = task.prompt.lower()
    return any(
        term in prompt
        for term in (
            "runtime parameter",
            "runtime csv",
            "csv sample sheet",
            "uploaded as a runtime csv parameter",
            "parameterized",
            "sample_count",
            "replicate_count",
            "include_controls",
        )
    )


def _expected_dynamic_terms(task: AuthoringTask) -> tuple[str, ...]:
    prompt = task.prompt.lower()
    terms: list[str] = []
    for term in (
        "sample_count",
        "replicate_count",
        "include_controls",
        "pipette_mount",
        "pipette_model",
    ):
        if term in prompt:
            terms.append(term)
    if "csv" in prompt or "sample sheet" in prompt:
        terms.append("csv")
    return tuple(dict.fromkeys(terms))


def _dynamic_plan_text(package_dir: Path) -> str:
    parts: list[str] = []
    for file_name in ("setup_card.html", "manifest.json", "protocol.py"):
        path = package_dir / file_name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts).lower()


def _contains_runtime_parameter_definition(protocol_text: str, term: str) -> bool:
    if term == "csv":
        return all(
            column in protocol_text
            for column in ("sample_id", "source_well", "destination_well", "target_volume")
        ) and ("csv" in protocol_text or "sample sheet" in protocol_text)
    if term not in protocol_text:
        return False
    return any(
        marker in protocol_text
        for marker in (
            "add_parameter",
            "add_parameters",
            "protocol.params",
            "ctx.params",
            "runtime parameter",
            "parameter",
        )
    )


def _plans_explain_dynamic_behavior(plan_text: str, term: str) -> bool:
    if term == "csv":
        return all(column in plan_text for column in ("source_well", "destination_well")) and (
            "csv" in plan_text or "sample sheet" in plan_text
        )
    if term not in plan_text:
        return False
    return any(
        marker in plan_text
        for marker in (
            "runtime",
            "parameter",
            "formula",
            "computed",
            "recompute",
            "derived",
            "sample_count",
            "replicate_count",
            "include_controls",
            "pipette_mount",
            "pipette_model",
        )
    )


def validate_param_sweep(package_dir: Path | str, task: AuthoringTask) -> ParamSweepResult:
    """Check whether dynamic tasks are truly parameterized instead of hard-coded.

    This is a deterministic v1 of the param-sweep oracle. It does not inject
    runtime values into Opentrons yet; it verifies that the generated package has
    the parameter hooks and cross-file plan evidence needed for a real sweep.
    """

    root = Path(package_dir).resolve()
    dynamic_task = _uses_dynamic_inputs(task)
    checks: dict[str, bool] = {}
    issues: list[SemanticIssue] = []
    if not dynamic_task:
        return ParamSweepResult(
            package_dir=str(root),
            task_id=task.task_id,
            dynamic_task=False,
            ok=True,
            checks={"not_dynamic_task": True},
        )

    protocol_path = root / "protocol.py"
    protocol_text = (
        protocol_path.read_text(encoding="utf-8", errors="replace").lower()
        if protocol_path.exists()
        else ""
    )
    plan_text = _dynamic_plan_text(root)
    terms = _expected_dynamic_terms(task)
    checks["dynamic_terms_detected"] = bool(terms)
    if not terms:
        issues.append(
            SemanticIssue(
                code="dynamic_terms_missing",
                message="Dynamic task was detected, but no expected runtime parameter term could be derived.",
            )
        )

    for term in terms:
        protocol_ok = _contains_runtime_parameter_definition(protocol_text, term)
        plan_ok = _plans_explain_dynamic_behavior(plan_text, term)
        checks[f"{term}_protocol_parameterized"] = protocol_ok
        checks[f"{term}_plans_parameterized"] = plan_ok
        if not protocol_ok:
            issues.append(
                SemanticIssue(
                    code=f"{term}_protocol_not_parameterized",
                    message=f"protocol.py does not expose or use runtime parameter {term}.",
                )
            )
        if not plan_ok:
            issues.append(
                SemanticIssue(
                    code=f"{term}_plan_not_parameterized",
                    message=f"setup_card.html or manifest.json do not show how {term} changes tips, reagents, or deck behavior.",
                )
            )

    if "sample_count" in terms and "greater than 96" in task.prompt.lower():
        checks["sample_count_plate_switch_documented"] = "96" in plan_text and "384" in plan_text
        if not checks["sample_count_plate_switch_documented"]:
            issues.append(
                SemanticIssue(
                    code="sample_count_plate_switch_missing",
                    message="Dynamic plate-format task does not document both 96-well and 384-well paths.",
                )
            )

    ok = not any(issue.severity == "error" for issue in issues)
    return ParamSweepResult(
        package_dir=str(root),
        task_id=task.task_id,
        dynamic_task=True,
        ok=ok,
        checks=checks,
        issues=tuple(issues),
    )


def _waste_expected_volume_ul(task: AuthoringTask) -> float | None:
    prompt = task.prompt
    explicit = re.search(
        r"about\s+(\d+(?:\.\d+)?)\s*mL\s+for\s+(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*uL",
        prompt,
        flags=re.IGNORECASE,
    )
    if explicit:
        return float(explicit.group(1)) * 1000
    match = re.search(
        r"(\d+)\s*(?:wells|samples).*?(\d+(?:\.\d+)?)\s*uL.*?(?:waste|discard)",
        prompt,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return float(match.group(1)) * float(match.group(2))
    if task.spec.default_samples:
        waste_reagents = [
            reagent
            for reagent in task.spec.reagents
            if reagent.volume_per_sample_uL is not None
            and any(term in reagent.name.lower() for term in ("wash", "waste"))
        ]
        if waste_reagents:
            return sum(task.spec.default_samples * reagent.volume_per_sample_uL for reagent in waste_reagents)
    return None


def _waste_capacity_values(package_text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(
        r"(?:waste|trash)[^.\n]{0,80}?(?:capacity|max(?:imum)? fill|max_fill)[^.\n]{0,40}?(\d+(?:\.\d+)?)\s*(mL|uL|µL|ul)",
        package_text,
        flags=re.IGNORECASE,
    ):
        value = float(match.group(1))
        unit = match.group(2).lower()
        values.append(value * 1000 if unit == "ml" else value)
    return values


def _waste_route_declared(package_text: str) -> bool:
    return any(
        term in package_text
        for term in (
            "liquid waste",
            "waste container",
            "waste reservoir",
            "waste well",
            "waste chute",
            "trash bin",
            "fixed trash",
        )
    )


def _liquid_waste_capacity_required(prompt: str) -> bool:
    return "liquid waste container" in prompt or "waste container capacity" in prompt


def _module_state_terms_ok(prompt: str, package_text: str) -> bool | None:
    if not any(term in prompt for term in ("module", "thermocycler", "magnet", "heater-shaker")):
        return None
    if "thermocycler" in prompt or "95" in prompt:
        return any(term in package_text for term in ("deactivate_lid", "open_lid", "cool", "pause"))
    if "magnet" in prompt or "magnetic" in prompt:
        return any(term in package_text for term in ("engage", "disengage"))
    return any(
        term in package_text
        for term in (
            "pause",
            "open_lid",
            "deactivate_lid",
            "cool",
            "engage",
            "disengage",
            "target temperature",
            "module state",
            "lid open",
            "magnet disengaged",
        )
    )


def _control_well_count(task: AuthoringTask) -> int:
    controls = task.spec.controls
    if not isinstance(controls, Mapping):
        return 0
    count = 0
    for value in controls.values():
        if isinstance(value, list):
            count += len(value)
        elif isinstance(value, str) and value not in {"none", "null"}:
            count += 1
    return count


def _controls_are_inside_sample_wells(task: AuthoringTask) -> bool:
    if not task.spec.default_samples or not task.spec.controls:
        return False
    prompt = task.prompt.lower()
    samples = task.spec.default_samples
    return bool(
        re.search(rf"\b(?:into|to|in)\s+{samples}\s+wells?\s+with\b", prompt)
        or re.search(rf"\b{samples}\s+wells?\s+.*controls?\s+at\b", prompt)
        or re.search(rf"\b{samples}\s+.*positive control at\b", prompt)
    )


def _declares_duplicate_control_count(package_text: str, expected: int, duplicate_total: int) -> bool:
    count_patterns = (
        rf"\b{duplicate_total}\s+(?:transfers?|destination wells?|used wells?|sample wells?|tips?)\b",
        rf"\b(?:transfers?|destination wells?|used wells?|sample wells?|tips?)\s*[:=]\s*{duplicate_total}\b",
    )
    if any(re.search(pattern, package_text) for pattern in count_patterns):
        return True
    if re.search(rf"\b{expected}\s*(?:samples?|wells?)\s*\+\s*\d+\s*controls?\b", package_text):
        return True
    return False


def validate_semantics(package_dir: Path | str, task: AuthoringTask) -> SemanticValidationResult:
    root = Path(package_dir).resolve()
    prompt = task.prompt.lower()
    package_text = _read_package_text(root)
    issues: list[SemanticIssue] = []
    checks: dict[str, bool] = {}

    volumes = _prompt_volumes(task.prompt)
    if volumes:
        matched = sum(1 for volume in volumes if _contains_volume(package_text, volume))
        checks["prompt_volume_coverage"] = matched / len(volumes) >= 0.75
        if not checks["prompt_volume_coverage"]:
            issues.append(
                SemanticIssue(
                    code="prompt_volume_missing",
                    message=f"Only {matched}/{len(volumes)} prompt volumes appear in the package.",
                )
            )

    if "negative control" in prompt:
        checks["negative_control_present"] = "negative control" in package_text
        if not checks["negative_control_present"]:
            issues.append(
                SemanticIssue(
                    code="missing_negative_control",
                    message="Task asks for a negative control but the package does not mention one.",
                )
            )

    if "positive control" in prompt:
        checks["positive_control_present"] = "positive control" in package_text
        if not checks["positive_control_present"]:
            issues.append(
                SemanticIssue(
                    code="missing_positive_control",
                    message="Task asks for a positive control but the package does not mention one.",
                )
            )

    dilution_requested = any(term in prompt for term in ("serial dilution", "dilution series"))
    if dilution_requested:
        checks["serial_dilution_mixes"] = "mix" in package_text and (
            "dilution" in package_text or "dilute" in package_text
        )
        if not checks["serial_dilution_mixes"]:
            issues.append(
                SemanticIssue(
                    code="dilution_mixing_missing",
                    message="Serial dilution task should explicitly mix dilution steps.",
                )
            )

    pcr_requested = any(term in prompt for term in ("pcr", "qpcr", "thermocycler"))
    if pcr_requested and "master mix" in prompt:
        checks["master_mix_accounted"] = "master mix" in package_text
        if not checks["master_mix_accounted"]:
            issues.append(
                SemanticIssue(
                    code="missing_master_mix",
                    message="PCR task asks for master mix but the package does not account for it.",
                )
            )

    if any(term in prompt for term in ("cross-contamination", "cross contamination", "carryover")):
        checks["contamination_mitigation_present"] = any(
            term in package_text for term in ("cross-contamination", "cross contamination", "new tip")
        )
        if not checks["contamination_mitigation_present"]:
            issues.append(
                SemanticIssue(
                    code="contamination_mitigation_missing",
                    message="Task flags contamination risk but package lacks an explicit mitigation.",
                )
            )

    if "tip" in prompt:
        checks["tip_quantity_declared"] = _tip_plan_has_quantity(root)
        if not checks["tip_quantity_declared"]:
            issues.append(
                SemanticIssue(
                    code="tip_quantity_missing",
                    message="Task mentions tip handling but manifest tips lack a positive quantity.",
                )
            )

    if task.spec.default_samples and any(
        term in prompt for term in ("fresh tip", "one fresh tip", "one tip per sample")
    ):
        required, available = _tip_plan_required_available(root)
        checks["tip_count_covers_samples"] = (
            required is not None
            and required >= task.spec.default_samples
            and (available is None or required <= available)
        )
        if not checks["tip_count_covers_samples"]:
            issues.append(
                SemanticIssue(
                    code="tip_count_below_sample_count",
                    message=(
                        "Task requires fresh tips per sample, but manifest tips do not cover "
                        f"{task.spec.default_samples} samples."
                    ),
                )
            )

    reagent_items = _named_plan_reagent_items(root)
    required_reagents = _required_reagent_volumes(task)
    if _uses_dynamic_inputs(task) and required_reagents:
        checks["reagent_totals_static_check_deferred"] = True
    elif reagent_items and required_reagents:
        checked = 0
        matched = 0
        upper_ok = True
        enforce_upper_bound = _reagent_total_upper_bound_is_exact(task)
        for name, volume in required_reagents.items():
            if volume <= 0:
                continue
            checked += 1
            lower_match, upper_match = _matching_reagent_volume_status(
                reagent_items,
                name,
                volume,
                enforce_upper_bound=enforce_upper_bound,
            )
            matched += 1 if lower_match else 0
            upper_ok = upper_ok and upper_match
        if checked:
            checks["reagent_totals_match_task_spec"] = matched == checked
            if not checks["reagent_totals_match_task_spec"]:
                issues.append(
                    SemanticIssue(
                        code="reagent_total_mismatch",
                        message=f"Only {matched}/{checked} reagent totals match task sample count and per-sample volumes.",
                    )
                )
            checks["reagent_totals_not_obviously_overstated"] = upper_ok
            if not checks["reagent_totals_not_obviously_overstated"]:
                issues.append(
                    SemanticIssue(
                        code="reagent_total_overstated",
                        message="A canonical reagent total is more than 125% of the expected task volume.",
                    )
                )

    if _controls_are_inside_sample_wells(task):
        control_count = _control_well_count(task)
        duplicate_total = (task.spec.default_samples or 0) + control_count
        required_tips, _ = _tip_plan_required_available(root)
        duplicate_tip_count = (
            required_tips is not None
            and control_count > 0
            and int(required_tips) == duplicate_total
        )
        duplicate_text_count = control_count > 0 and _declares_duplicate_control_count(
            package_text,
            task.spec.default_samples or 0,
            duplicate_total,
        )
        checks["controls_not_double_counted"] = not (duplicate_tip_count or duplicate_text_count)
        if not checks["controls_not_double_counted"]:
            issues.append(
                SemanticIssue(
                    code="controls_double_counted",
                    message="Controls appear to be counted in addition to sample wells even though they are inside the requested well count.",
                )
            )

    if any(term in prompt for term in ("waste", "discard", "wash")):
        expected_waste = _waste_expected_volume_ul(task)
        capacities = _waste_capacity_values(package_text)
        checks["waste_route_declared"] = _waste_route_declared(package_text)
        if not checks["waste_route_declared"]:
            issues.append(
                SemanticIssue(
                    code="waste_route_missing",
                    message="Task asks for waste handling but package does not declare where waste goes.",
                )
            )
        capacity_required = _liquid_waste_capacity_required(prompt)
        checks["waste_capacity_declared"] = not capacity_required or bool(capacities)
        if not checks["waste_capacity_declared"]:
            issues.append(
                SemanticIssue(
                    code="waste_capacity_missing",
                    message=(
                        "Task asks for a liquid-waste container capacity, but package does not "
                        "declare capacity/max fill. Generic trash or waste chute capacity is not assumed."
                    ),
                )
            )
        if expected_waste is not None and capacities:
            checks["waste_capacity_sufficient"] = max(capacities) >= expected_waste
            if not checks["waste_capacity_sufficient"]:
                issues.append(
                    SemanticIssue(
                        code="waste_capacity_insufficient",
                        message=(
                            f"Declared waste capacity {max(capacities):g} uL is below expected "
                            f"{expected_waste:g} uL waste."
                        ),
                    )
                )

    module_state_ok = _module_state_terms_ok(prompt, package_text)
    if module_state_ok is not None:
        checks["module_state_control_present"] = module_state_ok
        if not module_state_ok:
            issues.append(
                SemanticIssue(
                    code="module_state_control_missing",
                    message="Module task lacks clear executable module-state control or operator confirmation.",
                )
            )

    passed = sum(1 for value in checks.values() if value)
    score = passed / len(checks) if checks else 1.0
    ok = not any(issue.severity == "error" for issue in issues)
    return SemanticValidationResult(
        package_dir=str(root),
        task_id=task.task_id,
        ok=ok,
        score=score,
        checks=checks,
        issues=tuple(issues),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run semantic oracle v0 on one package")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args(argv)

    tasks = {task.task_id: task for task in load_authoring_tasks(args.tasks)}
    if args.task_id not in tasks:
        raise SystemExit(f"unknown task id: {args.task_id}")
    result = validate_semantics(args.package_dir, tasks[args.task_id])
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
