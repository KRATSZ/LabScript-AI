"""BPL-style virtual deck: overflow / empty / tip. This is the LogicPass branch for Plan IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from labscriptai.planir.schema import PlanDocument, PlanStep

DEFAULT_MAX_UL = 200.0


@dataclass
class DeckIssue:
    code: str
    detail_text: str
    step_id: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail_text": self.detail_text, "step_id": self.step_id}


@dataclass
class VirtualDeckResult:
    ok: bool
    issues: list[DeckIssue] = field(default_factory=list)
    wells: dict[str, float] = field(default_factory=dict)
    pipette_ul: float = 0.0
    has_tip: bool = False
    steps_run: int = 0

    def to_logicpass(self) -> dict[str, Any]:
        if not self.ok:
            return {
                "outcome": "fail",
                "logic_pass": False,
                "final_pass_v2": False,
                "issues": [issue.to_dict() for issue in self.issues],
                "reason": self.issues[0].code if self.issues else "virtual_deck_failed",
            }
        return {
            "outcome": "pass",
            "logic_pass": True,
            "final_pass_v2": True,
            "issues": [],
        }


def _max_for(plan: PlanDocument, loc: str) -> float:
    plate = loc.split(":", 1)[0]
    for resource in plan.resources:
        if resource.id == plate and resource.max_volume_ul is not None:
            return float(resource.max_volume_ul)
    return DEFAULT_MAX_UL


def evaluate_virtual_deck(plan: PlanDocument) -> VirtualDeckResult:
    """Deterministic volume/tip ledger. No vendor SDK."""
    wells = dict(plan.initial_volumes_ul)
    pipette = 0.0
    has_tip = False
    issues: list[DeckIssue] = []
    ran = 0

    def fail(code: str, text: str, step: PlanStep) -> VirtualDeckResult:
        issues.append(DeckIssue(code=code, detail_text=text, step_id=step.step_id))
        return VirtualDeckResult(
            ok=False,
            issues=issues,
            wells=wells,
            pipette_ul=pipette,
            has_tip=has_tip,
            steps_run=ran,
        )

    for step in plan.ordered_steps():
        ran += 1
        kind = step.primitive_type
        if kind == "WAIT":
            continue
        if kind == "PICK_TIPS":
            has_tip = True
            continue
        if kind == "DROP_TIPS":
            if pipette > 1e-9:
                return fail(
                    "LP-TIP-LIQUID",
                    f"drop tip while pipette still holds {pipette:.1f} µL",
                    step,
                )
            has_tip = False
            continue
        if not has_tip:
            return fail("LP-NO-TIP", f"{kind} without a tip", step)
        volume = float(step.volume_ul or 0)
        if kind == "ASPIRATE":
            loc = step.source or ""
            have = wells.get(loc, 0.0)
            if have + 1e-9 < volume:
                return fail(
                    "LP-EMPTY",
                    f"aspirate {volume} µL from {loc} but only {have} µL",
                    step,
                )
            wells[loc] = have - volume
            pipette += volume
            continue
        if kind == "DISPENSE":
            loc = step.destination or ""
            if pipette + 1e-9 < volume:
                return fail(
                    "LP-PIPETTE-EMPTY",
                    f"dispense {volume} µL but pipette holds {pipette:.1f} µL",
                    step,
                )
            cap = _max_for(plan, loc)
            have = wells.get(loc, 0.0)
            if have + volume > cap + 1e-9:
                return fail(
                    "LP-OVERFLOW",
                    f"dispense {volume} µL into {loc} would exceed {cap} µL",
                    step,
                )
            wells[loc] = have + volume
            pipette -= volume
            continue
        if kind == "MIX":
            loc = step.location or step.source or step.destination or ""
            have = wells.get(loc, 0.0)
            if have + 1e-9 < volume:
                return fail(
                    "LP-EMPTY",
                    f"mix {volume} µL at {loc} but only {have} µL",
                    step,
                )
            continue
    return VirtualDeckResult(ok=True, wells=wells, pipette_ul=pipette, has_tip=has_tip, steps_run=ran)
