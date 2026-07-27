"""Continuation patch validation for breakpoint recovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .recovery_contract import validate_alternative_source
from .state import RuntimeState

PATCH_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True)
class PatchValidationResult:
    ok: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "reasons": list(self.reasons)}


def validate_continuation_patch(
    patch: Mapping[str, Any],
    state: RuntimeState,
    *,
    require_human_confirmation: bool = False,
) -> PatchValidationResult:
    """Check a proposed remaining-steps patch against the runtime ledger."""

    reasons: list[str] = []
    if patch.get("schema_version") != PATCH_SCHEMA_VERSION:
        reasons.append(f"patch.schema_version must be {PATCH_SCHEMA_VERSION}")

    recovery_type = patch.get("recovery_type")
    if recovery_type not in {
        "small_action",
        "alternative_resource",
        "continuation_protocol",
    }:
        reasons.append("patch.recovery_type is invalid")

    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        reasons.append("patch.operations must be a non-empty list")
        operations = []

    if require_human_confirmation and not patch.get("human_confirmed"):
        reasons.append("execution of a recovery patch requires human_confirmed=true")

    used_tips = set(state.used_tips)
    treated = set(state.treated_wells)
    unavailable = set(_string_list(state.committed.get("unavailable_resources", [])))
    source_volumes = _source_volumes(state)
    already_transferred = {
        (
            str(item.get("source_well") or item.get("source") or ""),
            str(item.get("destination_well") or item.get("destination") or ""),
            str(item.get("reagent") or ""),
        )
        for item in state.liquid_transfers
    }
    has_retire_tip = False
    has_use_tip = False
    has_effectful_operation = False

    for index, raw_operation in enumerate(operations):
        if not isinstance(raw_operation, Mapping):
            reasons.append(f"operations[{index}] must be an object")
            continue
        op_type = str(raw_operation.get("op_type", ""))
        if op_type == "retire_tip":
            tip = _resource_id(raw_operation, "tip")
            if not tip:
                reasons.append(f"operations[{index}] retire_tip requires tip")
            else:
                has_retire_tip = True
                has_effectful_operation = True
            continue

        if op_type == "use_tip":
            tip = _resource_id(raw_operation, "tip")
            if not tip:
                reasons.append(f"operations[{index}] use_tip requires tip")
            elif tip in used_tips:
                reasons.append(f"operations[{index}] reuses already used tip {tip}")
            else:
                has_use_tip = True
                has_effectful_operation = True
            continue

        if op_type == "transfer":
            has_effectful_operation = True
            tip = _resource_id(raw_operation, "tip")
            source = _resource_id(raw_operation, "source_well", fallback="source")
            destination = _resource_id(
                raw_operation,
                "destination_well",
                fallback="destination",
            )
            reagent = str(raw_operation.get("reagent") or "")
            volume_ul = _float_value(raw_operation.get("volume_ul"))
            if tip and tip in used_tips:
                reasons.append(f"operations[{index}] reuses already used tip {tip}")
            if not source:
                reasons.append(f"operations[{index}] transfer requires source_well")
            if not destination:
                reasons.append(f"operations[{index}] transfer requires destination_well")
            if volume_ul is None or volume_ul <= 0:
                reasons.append(f"operations[{index}] transfer requires positive volume_ul")
            if source and source in unavailable:
                reasons.append(f"operations[{index}] source {source} is unavailable")
            known_sources = _known_source_ids(state)
            if source and known_sources and source not in known_sources:
                reasons.append(
                    f"operations[{index}] source {source} is not present in runtime inventory"
                )
            if source and volume_ul is not None and source in source_volumes:
                if volume_ul > source_volumes[source]:
                    reasons.append(
                        f"operations[{index}] would aspirate {volume_ul}uL from {source}, "
                        f"only {source_volumes[source]}uL observed"
                    )
                else:
                    source_volumes[source] -= volume_ul
            transfer_key = (source, destination, reagent)
            if destination in treated and not raw_operation.get("allow_repeat", False):
                reasons.append(
                    f"operations[{index}] targets already treated well {destination}"
                )
            if transfer_key in already_transferred and not raw_operation.get("allow_repeat", False):
                reasons.append(
                    f"operations[{index}] duplicates committed transfer {source}->{destination}"
                )
            continue

        if op_type == "resource_substitution":
            has_effectful_operation = True
            from_resource = _resource_id(raw_operation, "from_resource")
            to_resource = _resource_id(raw_operation, "to_resource")
            if not from_resource or not to_resource:
                reasons.append(
                    f"operations[{index}] resource_substitution requires from_resource and to_resource"
                )
            if to_resource in unavailable:
                reasons.append(f"operations[{index}] substitute target {to_resource} is unavailable")
            available = _float_value(raw_operation.get("available_volume_ul"))
            required = _float_value(raw_operation.get("required_volume_ul"))
            if available is not None and required is not None and available < required:
                reasons.append(
                    f"operations[{index}] substitute target {to_resource} has insufficient volume"
                )
            if to_resource:
                source_result = validate_alternative_source(
                    state,
                    source_id=to_resource,
                    liquid_id=str(raw_operation.get("liquid_id") or "") or None,
                    required_volume_ul=required,
                )
                reasons.extend(
                    f"operations[{index}] {reason}" for reason in source_result.reasons
                )
            continue

        if op_type in {"skip", "comment"}:
            continue

        reasons.append(f"operations[{index}] has unsupported op_type {op_type or '<missing>'}")

    requires_tip_replacement = bool(state.observed.get("tip_contaminated")) or str(
        state.observed.get("tip_clog_class") or ""
    ).lower() == "ordinary"
    # Same-liquid path after buffer probe: tip may be wet/contaminated-flagged but reuse is allowed
    # when tip_swap is not required (live_paired_v2 P4 green / F11 tip-policy).
    same_liquid_ok = bool(state.observed.get("same_liquid_path")) and not bool(
        state.observed.get("tip_swap_required")
    )
    if requires_tip_replacement and not same_liquid_ok:
        if not has_retire_tip:
            reasons.append("recovery patch must retire the contaminated or clogged current tip")
        if not has_use_tip:
            reasons.append("recovery patch must select a fresh tip")
    if operations and not has_effectful_operation:
        reasons.append("recovery patch must include at least one effectful operation")

    return PatchValidationResult(ok=not reasons, reasons=tuple(reasons))


def _known_source_ids(state: RuntimeState) -> set[str]:
    known: set[str] = set()
    for container in (state.expected, state.committed, state.observed):
        for key in ("source_id", "current_source_id", "backup_source_id"):
            value = str(container.get(key) or "").strip()
            if value:
                known.add(value)
        raw = container.get("annotated_alternative_sources") or []
        if isinstance(raw, (list, tuple)):
            for item in raw:
                if isinstance(item, Mapping):
                    value = str(item.get("source_id") or "").strip()
                    if value:
                        known.add(value)
    return known


def build_ledger_from_run_history(run_history: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a live run/commands snapshot into the fields RuntimeState stores."""

    commands = run_history.get("recent_commands") or run_history.get("commands") or []
    if not isinstance(commands, list):
        commands = []
    completed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    for command in commands:
        if not isinstance(command, Mapping):
            continue
        normalized = dict(command)
        status = str(normalized.get("status") or "").lower()
        if status == "succeeded":
            completed.append(normalized)
        elif status == "failed":
            failed.append(normalized)
        elif status in {"queued", "running", "pending"}:
            remaining.append(normalized)
    return {
        "completed_commands": completed,
        "failed_commands": failed,
        "remaining_plan": remaining,
    }


def _source_volumes(state: RuntimeState) -> dict[str, float]:
    raw = state.observed.get("source_volumes_ul") or state.committed.get("source_volumes_ul") or {}
    if not isinstance(raw, Mapping):
        return {}
    volumes: dict[str, float] = {}
    for key, value in raw.items():
        parsed = _float_value(value)
        if parsed is not None:
            volumes[str(key)] = parsed
    return volumes


def _resource_id(operation: Mapping[str, Any], key: str, *, fallback: str | None = None) -> str:
    value = operation.get(key)
    if value is None and fallback:
        value = operation.get(fallback)
    return str(value or "")


def _float_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
