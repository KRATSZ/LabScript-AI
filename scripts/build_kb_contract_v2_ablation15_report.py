#!/usr/bin/env python3
"""Build a unified review for the kb_contract_v2 ablation15 candidate rows."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from labscriptai.benchmark.analyze_authoring_run import analyze_run

TASKS_PATH = ROOT / "benchmarks" / "authoring" / "tasks.yaml"
RUN_ROOT = ROOT / "runs" / "kb_strong_followup"
REVIEW_ROOT = RUN_ROOT / "kb_contract_v2" / "ablation15_unified_review"
EXPECTED_TASK_COUNT = 15


@dataclass(frozen=True)
class CandidateSpec:
    model: str
    slot: str
    candidate_dir: Path
    baseline_dir: Path


@dataclass(frozen=True)
class CarryOverSpec:
    model: str
    slot: str
    source_dir: Path


CANDIDATES: tuple[CandidateSpec, ...] = (
    CandidateSpec(
        model="flash",
        slot="no_kb",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_flash_R1_unified_sim_no_kb_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "flash" / "no_kb",
    ),
    CandidateSpec(
        model="flash",
        slot="full_old",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_flash_R2_unified_full_old_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "flash" / "full_old",
    ),
    CandidateSpec(
        model="flash",
        slot="repair_patch_only",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_flash_R3_unified_kb_v2_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "flash" / "repair_patch_only",
    ),
    CandidateSpec(
        model="flash",
        slot="repair_rewrite",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_flash_R4_unified_kb_v2_rewrite",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "flash" / "repair_rewrite",
    ),
    CandidateSpec(
        model="pro",
        slot="no_kb",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_pro_R1_unified_sim_no_kb_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "pro" / "no_kb",
    ),
    CandidateSpec(
        model="pro",
        slot="full_old",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_pro_R2_unified_full_old_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "pro" / "full_old",
    ),
    CandidateSpec(
        model="pro",
        slot="repair_patch_only",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_pro_R3_unified_kb_v2_patch",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "pro" / "repair_patch_only",
    ),
    CandidateSpec(
        model="pro",
        slot="repair_rewrite",
        candidate_dir=RUN_ROOT / "kb_contract_v2" / "ablation15_pro_R4_unified_kb_v2_rewrite",
        baseline_dir=RUN_ROOT / "ablation15_clean" / "pro" / "repair_rewrite",
    ),
)

CARRY_OVERS: tuple[CarryOverSpec, ...] = (
    CarryOverSpec(
        model="flash",
        slot="kb_strong_compact",
        source_dir=RUN_ROOT / "ablation15_clean" / "flash" / "kb_strong_compact",
    ),
    CarryOverSpec(
        model="pro",
        slot="kb_strong_compact",
        source_dir=RUN_ROOT / "ablation15_clean" / "pro" / "kb_strong_compact",
    ),
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_analysis(run_dir: Path) -> dict[str, Any]:
    analysis_dir = run_dir / "analysis"
    analysis_path = analysis_dir / "attribution-summary.json"
    if analysis_path.exists():
        return _load_json(analysis_path)
    return analyze_run(run_dir / "summary.json", TASKS_PATH, analysis_dir)


def _provider_touched_tasks(analysis: dict[str, Any]) -> int:
    count = 0
    for row in analysis.get("per_task", []):
        if not isinstance(row, dict):
            continue
        if int(row.get("provider_error_count", 0)) > 0:
            count += 1
    return count


def _row_metrics(run_dir: Path, analysis: dict[str, Any]) -> dict[str, Any]:
    summary = _load_json(run_dir / "summary.json")
    task_count = int(analysis.get("task_count", 0))
    total_tokens = int(summary.get("total_tokens", 0))
    total_wall_time_sec = float(summary.get("total_wall_time_sec", 0.0))
    return {
        "run_dir": str(run_dir),
        "label": run_dir.name,
        "task_count": task_count,
        "task_pass_count": int(analysis.get("task_pass_count", 0)),
        "simulation_pass_count": int(analysis.get("simulation_pass_count", 0)),
        "validator_ok_count": int(analysis.get("validator_ok_count", 0)),
        "semantic_ok_count": int(analysis.get("semantic_ok_count", 0)),
        "param_sweep_ok_count": int(analysis.get("param_sweep_ok_count", 0)),
        "trace_present_count": int(analysis.get("trace_present_count", 0)),
        "provider_error_count": int(summary.get("provider_error_count", 0)),
        "provider_touched_tasks": _provider_touched_tasks(analysis),
        "total_tokens": total_tokens,
        "tokens_per_task": (total_tokens / task_count) if task_count else 0.0,
        "total_wall_time_sec": total_wall_time_sec,
        "wall_time_sec_per_task": (total_wall_time_sec / task_count) if task_count else 0.0,
    }


def _gate(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    quality_reasons: list[str] = []
    clean_reasons: list[str] = []

    if candidate["task_count"] != EXPECTED_TASK_COUNT:
        quality_reasons.append(f"task_count={candidate['task_count']} != {EXPECTED_TASK_COUNT}")
    if candidate["task_pass_count"] < baseline["task_pass_count"]:
        quality_reasons.append(
            f"task_pass {candidate['task_pass_count']} < clean {baseline['task_pass_count']}"
        )
    if candidate["semantic_ok_count"] < baseline["semantic_ok_count"]:
        quality_reasons.append(
            f"semantic_ok {candidate['semantic_ok_count']} < clean {baseline['semantic_ok_count']}"
        )

    quality_pass = not quality_reasons

    if not quality_pass:
        clean_reasons.extend(quality_reasons)
    if candidate["provider_error_count"] != 0:
        clean_reasons.append(f"provider_error_count={candidate['provider_error_count']}")
    if candidate["provider_touched_tasks"] != 0:
        clean_reasons.append(f"provider_touched_tasks={candidate['provider_touched_tasks']}")

    clean_pass = not clean_reasons
    return {
        "quality_pass": quality_pass,
        "quality_reasons": quality_reasons,
        "clean_pass": clean_pass,
        "clean_reasons": clean_reasons,
    }


def _selection_entry(spec: CandidateSpec, gate: dict[str, Any]) -> dict[str, Any]:
    selected_dir = spec.candidate_dir if gate["clean_pass"] else spec.baseline_dir
    return {
        "model": spec.model,
        "slot": spec.slot,
        "selected_source": "candidate" if gate["clean_pass"] else "baseline",
        "selected_dir": str(selected_dir),
        "candidate_dir": str(spec.candidate_dir),
        "baseline_dir": str(spec.baseline_dir),
    }


def _delta(candidate: dict[str, Any], baseline: dict[str, Any], key: str) -> int:
    return int(candidate[key]) - int(baseline[key])


def build_review() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    selection: list[dict[str, Any]] = []

    for spec in CANDIDATES:
        candidate_analysis = _ensure_analysis(spec.candidate_dir)
        baseline_analysis = _ensure_analysis(spec.baseline_dir)
        candidate = _row_metrics(spec.candidate_dir, candidate_analysis)
        baseline = _row_metrics(spec.baseline_dir, baseline_analysis)
        gate = _gate(candidate, baseline)
        rows.append(
            {
                "model": spec.model,
                "slot": spec.slot,
                "candidate": candidate,
                "baseline": baseline,
                "delta": {
                    "task_pass_count": _delta(candidate, baseline, "task_pass_count"),
                    "simulation_pass_count": _delta(candidate, baseline, "simulation_pass_count"),
                    "validator_ok_count": _delta(candidate, baseline, "validator_ok_count"),
                    "semantic_ok_count": _delta(candidate, baseline, "semantic_ok_count"),
                    "param_sweep_ok_count": _delta(candidate, baseline, "param_sweep_ok_count"),
                    "provider_error_count": _delta(candidate, baseline, "provider_error_count"),
                },
                "gate": gate,
            }
        )
        selection.append(_selection_entry(spec, gate))

    for carry in CARRY_OVERS:
        selection.append(
            {
                "model": carry.model,
                "slot": carry.slot,
                "selected_source": "baseline_carry_over",
                "selected_dir": str(carry.source_dir),
                "candidate_dir": None,
                "baseline_dir": str(carry.source_dir),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expected_task_count": EXPECTED_TASK_COUNT,
        "rows": rows,
        "selection": selection,
    }


def _format_gate(gate: dict[str, Any], level: str) -> str:
    passed = bool(gate[f"{level}_pass"])
    reasons = gate[f"{level}_reasons"]
    if passed:
        return "pass"
    return "fail: " + "; ".join(reasons)


def _to_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# Ablation15 Unified Review",
        "",
        f"- generated_at: `{review['generated_at']}`",
        f"- expected_task_count: `{review['expected_task_count']}`",
        "- quality gate: candidate must not drop `task_pass` or `semantic_ok` against the paired clean row.",
        "- clean gate: quality gate plus `provider_error_count == 0` and no provider-touched tasks.",
        "",
        "## Candidate rows",
        "",
        "| Model | Slot | Candidate | Clean | dBoB | dSem | dSim | Provider Err | Provider-Touched Tasks | Tokens/Task | Quality Gate | Clean Gate |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in review["rows"]:
        candidate = row["candidate"]
        baseline = row["baseline"]
        delta = row["delta"]
        gate = row["gate"]
        lines.append(
            "| {model} | {slot} | {cand_bob}/{cand_n} | {base_bob}/{base_n} | {d_bob:+d} | {d_sem:+d} | "
            "{d_sim:+d} | {provider_err} | {provider_touched} | {tokens_per_task:.0f} | {quality} | {clean} |".format(
                model=row["model"],
                slot=row["slot"],
                cand_bob=candidate["task_pass_count"],
                cand_n=candidate["task_count"],
                base_bob=baseline["task_pass_count"],
                base_n=baseline["task_count"],
                d_bob=delta["task_pass_count"],
                d_sem=delta["semantic_ok_count"],
                d_sim=delta["simulation_pass_count"],
                provider_err=candidate["provider_error_count"],
                provider_touched=candidate["provider_touched_tasks"],
                tokens_per_task=candidate["tokens_per_task"],
                quality="pass" if gate["quality_pass"] else "fail",
                clean="pass" if gate["clean_pass"] else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Gate details",
            "",
        ]
    )
    for row in review["rows"]:
        lines.append(f"### {row['model']} / {row['slot']}")
        lines.append("")
        lines.append(f"- candidate: `{row['candidate']['run_dir']}`")
        lines.append(f"- clean: `{row['baseline']['run_dir']}`")
        lines.append(f"- quality gate: {_format_gate(row['gate'], 'quality')}")
        lines.append(f"- clean gate: {_format_gate(row['gate'], 'clean')}")
        lines.append("")
    lines.extend(
        [
            "## Clean selection",
            "",
            "| Model | Slot | Selected Source | Selected Dir |",
            "|---|---|---|---|",
        ]
    )
    for entry in sorted(review["selection"], key=lambda item: (item["model"], item["slot"])):
        lines.append(
            "| {model} | {slot} | {selected_source} | `{selected_dir}` |".format(**entry)
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    review = build_review()
    (REVIEW_ROOT / "comparison.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (REVIEW_ROOT / "comparison.md").write_text(
        _to_markdown(review),
        encoding="utf-8",
    )
    print(REVIEW_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
