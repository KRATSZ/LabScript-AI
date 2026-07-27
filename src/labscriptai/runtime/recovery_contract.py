"""Deterministic contracts shared by runtime recovery actions and patches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .state import RuntimeState


@dataclass(frozen=True)
class AlternativeSourceValidation:
    ok: bool
    reasons: tuple[str, ...] = ()
    source: Mapping[str, Any] | None = None


def validate_alternative_source(
    state: RuntimeState,
    *,
    source_id: str,
    liquid_id: str | None = None,
    required_volume_ul: float | None = None,
) -> AlternativeSourceValidation:
    """Validate a proposed source against explicit, annotated runtime inventory."""

    requested_source = str(source_id or "").strip()
    if not requested_source:
        return AlternativeSourceValidation(False, ("alternative source requires source_id",))

    sources = _annotated_sources(state)
    source = sources.get(requested_source)
    if source is None:
        return AlternativeSourceValidation(
            False,
            (f"source {requested_source} is not an annotated alternative in runtime state",),
        )

    reasons: list[str] = []
    if source.get("annotated") is False:
        reasons.append(f"source {requested_source} is not annotated for substitution")

    unavailable = _unavailable_resources(state)
    if requested_source in unavailable:
        reasons.append(f"source {requested_source} is an unavailable resource")

    expected_liquid = str(
        liquid_id
        or state.observed.get("liquid_id")
        or state.committed.get("liquid_id")
        or state.expected.get("liquid_id")
        or ""
    ).strip()
    source_liquid = str(source.get("liquid_id") or "").strip()
    if expected_liquid and source_liquid and source_liquid != expected_liquid:
        reasons.append(
            f"source {requested_source} liquid_id {source_liquid} does not match {expected_liquid}"
        )

    if required_volume_ul is not None:
        available = _available_volume_ul(state, requested_source, source)
        if available is None:
            reasons.append(f"source {requested_source} has no observed available volume")
        elif available < required_volume_ul:
            reasons.append(
                f"source {requested_source} has {available}uL, requires {required_volume_ul}uL"
            )

    return AlternativeSourceValidation(not reasons, tuple(reasons), source)


def _annotated_sources(state: RuntimeState) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for container in (state.expected, state.committed, state.observed):
        for key in ("annotated_alternative_sources", "alternative_sources", "liquid_inventory"):
            _merge_source_container(sources, container.get(key))

    # Backward-compatible benchmark/runtime fields. The explicit boolean is required;
    # a source name alone must not turn an unannotated tube into a valid backup.
    for container in (state.expected, state.committed, state.observed):
        if container.get("annotated_backup_exists") is not True:
            continue
        backup_id = str(container.get("backup_source_id") or "").strip()
        if not backup_id:
            continue
        sources.setdefault(
            backup_id,
            {
                "source_id": backup_id,
                "liquid_id": container.get("liquid_id"),
                "annotated": True,
            },
        )
    return sources


def _merge_source_container(
    target: dict[str, dict[str, Any]],
    raw: Any,
) -> None:
    if isinstance(raw, Mapping):
        for source_id, value in raw.items():
            record = dict(value) if isinstance(value, Mapping) else {}
            record.setdefault("source_id", str(source_id))
            if record.get("annotated") is not False:
                record.setdefault("annotated", True)
            target[str(source_id)] = record
        return
    if isinstance(raw, (list, tuple)):
        for value in raw:
            if not isinstance(value, Mapping):
                continue
            source_id = str(value.get("source_id") or value.get("id") or "").strip()
            if not source_id:
                continue
            record = dict(value)
            record.setdefault("source_id", source_id)
            if record.get("annotated") is not False:
                record.setdefault("annotated", True)
            target[source_id] = record


def _unavailable_resources(state: RuntimeState) -> set[str]:
    values: set[str] = set()
    for container in (state.committed, state.observed):
        raw = container.get("unavailable_resources") or []
        if isinstance(raw, (list, tuple, set)):
            values.update(str(item) for item in raw)
    return values


def _available_volume_ul(
    state: RuntimeState,
    source_id: str,
    source: Mapping[str, Any],
) -> float | None:
    for key in ("available_volume_ul", "volume_ul"):
        parsed = _float_value(source.get(key))
        if parsed is not None:
            return parsed
    for container in (state.observed, state.committed):
        raw = container.get("source_volumes_ul")
        if isinstance(raw, Mapping):
            parsed = _float_value(raw.get(source_id))
            if parsed is not None:
                return parsed
    return None


def _float_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
