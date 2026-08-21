"""Structured LogicPass issues (repair-prompt-ready ``detail_text``)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping, Sequence

IssueSeverity = Literal["error", "report", "terminal"]

SUPPORTED_LEAF_SUBSET = (
    "loadLiquid,pickUpTip,dropTip,dropTipInPlace,aspirate,dispense"
)


@dataclass(frozen=True)
class LogicIssue:
    """One LogicPass finding.

    Required repair-facing fields: ``code``, ``step_index``, ``well``,
    ``detail_text``. Extra fields follow the Phase-0 error schema.
    """

    code: str
    step_index: int | None
    well: str | None
    detail_text: str
    severity: IssueSeverity = "error"
    labware: str | None = None
    command_id: str | None = None
    hint: str | None = None
    provenance: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CoverageCounts:
    """Aggregate skip / evaluable denominators for paper tables."""

    evaluable_denominator: int = 0
    skip_counts: dict[str, int] = field(default_factory=dict)
    per_rule: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluable_denominator": self.evaluable_denominator,
            "skip_counts": dict(self.skip_counts),
            "per_rule": list(self.per_rule),
        }


def format_l1_detail(
    *,
    step_index: int,
    requested_ul: float,
    labware: str,
    well: str,
    current_ul: float,
    dead_ul: float | None,
    kind: str,
) -> str:
    dead_text = "unknown" if dead_ul is None else f"{_fmt_ul(dead_ul)}"
    return (
        f"Step {step_index}: aspirate {_fmt_ul(requested_ul)} µL from "
        f"{labware}:{well}; current={_fmt_ul(current_ul)} µL, "
        f"dead_volume={dead_text} µL → violation={kind}."
    )


def format_l2_detail(
    *,
    reagent_id: str,
    consumed_ul: float,
    demand_ul: float | None,
    remaining_ul: float | None,
    mode: Literal["hard", "report"],
) -> str:
    demand_text = "same_trace" if demand_ul is None else _fmt_ul(demand_ul)
    remaining_text = "unknown" if remaining_ul is None else _fmt_ul(remaining_ul)
    return (
        f"Reagent '{reagent_id}': path consumed {_fmt_ul(consumed_ul)} µL; "
        f"demand={demand_text}; remaining={remaining_text}; mode={mode}."
    )


def format_l3_detail(
    *,
    step_index: int,
    pipette_id: str,
    dirty_well: str,
    protected_well: str,
) -> str:
    return (
        f"Step {step_index}: tip on {pipette_id} dirty from {dirty_well} "
        f"then aspirated protected source {protected_well} without tip change."
    )


def format_l4_detail(
    *,
    step_index: int,
    add_ul: float,
    labware: str,
    well: str,
    projected_ul: float,
    max_ul: float,
) -> str:
    return (
        f"Step {step_index}: dispense {_fmt_ul(add_ul)} µL into "
        f"{labware}:{well} → projected={_fmt_ul(projected_ul)} µL > "
        f"max={_fmt_ul(max_ul)} µL."
    )


def format_l5_detail(
    *,
    locus: str,
    reason: str,
    subset: str | None = None,
    step_index: int | None = None,
    command_id: str | None = None,
    command_type: str | None = None,
) -> str:
    subset_text = subset if subset is not None else SUPPORTED_LEAF_SUBSET
    parts = [f"Trace incomplete at {locus}: reason={reason}"]
    if step_index is not None:
        parts.append(f"index={step_index}")
    if command_id is not None:
        parts.append(f"command_id={command_id}")
    if command_type is not None:
        parts.append(f"command_type={command_type}")
    parts.append(f"supported_subset={subset_text}")
    parts.append("action=fail_closed")
    parts.append("logic_pass=false.")
    return "; ".join(parts)


def format_l6_detail(*, term: str, v1: Any, v2: Any) -> str:
    return (
        f"Dynamic term '{term}': executable evidence missing or analyze values "
        f"{v1},{v2} not wired (prose ignored)."
    )


def format_input_conflict_detail(conflict: Mapping[str, Any] | Any) -> str:
    if hasattr(conflict, "detail_text") and conflict.detail_text:
        return str(conflict.detail_text)
    if isinstance(conflict, Mapping) and conflict.get("detail_text"):
        return str(conflict["detail_text"])
    return "Authoritative input conflict (LP-INPUT-CONFLICT)."


def issues_to_dicts(issues: Sequence[LogicIssue]) -> list[dict[str, Any]]:
    return [issue.to_dict() for issue in issues]


def _fmt_ul(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


__all__ = [
    "CoverageCounts",
    "IssueSeverity",
    "LogicIssue",
    "SUPPORTED_LEAF_SUBSET",
    "format_input_conflict_detail",
    "format_l1_detail",
    "format_l2_detail",
    "format_l3_detail",
    "format_l4_detail",
    "format_l5_detail",
    "format_l6_detail",
    "issues_to_dicts",
]
