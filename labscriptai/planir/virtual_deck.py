"""BPL-style virtual deck: overflow / empty / tip. This is the LogicPass branch for Plan IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from labscriptai.planir.schema import PlanDocument, PlanStep


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
    unevaluable: bool = False

    def to_logicpass(self) -> dict[str, Any]:
        if not self.ok:
            return {
                "outcome": "fail",
                "logic_pass": False,
                "final_pass_v2": False,
                "issues": [issue.to_dict() for issue in self.issues],
                "reason": self.issues[0].code if self.issues else "virtual_deck_failed",
            }
        if self.unevaluable:
            return {
                "outcome": "unevaluable",
                "logic_pass": False,
                "final_pass_v2": False,
                "issues": [issue.to_dict() for issue in self.issues],
                "reason": self.issues[0].code if self.issues else "capacity_unknown",
            }
        return {
            "outcome": "pass",
            "logic_pass": True,
            "final_pass_v2": True,
            "issues": [],
        }


def _max_for(plan: PlanDocument, loc: str) -> float | None:
    plate = loc.split(":", 1)[0]
    for resource in plan.resources:
        if resource.id == plate:
            if resource.max_volume_ul is None:
                return None
            return float(resource.max_volume_ul)
    return None


def evaluate_virtual_deck(plan: PlanDocument) -> VirtualDeckResult:
    """Deterministic volume/tip ledger. No vendor SDK."""
    wells = dict(plan.initial_volumes_ul)
    pipette = 0.0
    has_tip = False
    issues: list[DeckIssue] = []
    unknown_locs: dict[str, str] = {}
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

    def touch(loc: str, step: PlanStep) -> float | None:
        cap = _max_for(plan, loc)
        if cap is None and loc and loc not in unknown_locs:
            unknown_locs[loc] = step.step_id
        return cap

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
            touch(loc, step)
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
            cap = touch(loc, step)
            have = wells.get(loc, 0.0)
            if cap is not None and have + volume > cap + 1e-9:
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
            touch(loc, step)
            have = wells.get(loc, 0.0)
            if have + 1e-9 < volume:
                return fail(
                    "LP-EMPTY",
                    f"mix {volume} µL at {loc} but only {have} µL",
                    step,
                )
            continue
    if unknown_locs:
        return VirtualDeckResult(
            ok=True,
            unevaluable=True,
            issues=[
                DeckIssue(
                    code="LP-CAPACITY-UNKNOWN",
                    detail_text=f"capacity unknown for {loc} — cannot verify overflow",
                    step_id=unknown_locs[loc],
                )
                for loc in sorted(unknown_locs)
            ],
            wells=wells,
            pipette_ul=pipette,
            has_tip=has_tip,
            steps_run=ran,
        )
    return VirtualDeckResult(ok=True, wells=wells, pipette_ul=pipette, has_tip=has_tip, steps_run=ran)
