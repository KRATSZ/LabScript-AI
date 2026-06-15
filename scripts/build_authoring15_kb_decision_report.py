"""Summarize the py-only 15-task KB ablation into a short decision table."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ROOT = Path("runs/kb_strong_followup/kb_contract_v2_pyonly")
OUT_DIR = RUN_ROOT / "decision_report"
ROWS = ("no_kb", "full_old", "kb_v2_patch", "kb_v2_rewrite")
MODELS = ("flash", "pro")


@dataclass(frozen=True)
class RowResult:
    model: str
    row: str
    task_pass_count: int
    semantic_ok_count: int
    provider_error_count: int
    validator_ok_count: int
    simulation_pass_count: int


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_row(model: str, row: str) -> RowResult:
    row_dir = RUN_ROOT / model / row
    analysis = _load_json(row_dir / "analysis" / "attribution-summary.json")
    summary = _load_json(row_dir / "summary.json")
    return RowResult(
        model=model,
        row=row,
        task_pass_count=int(analysis.get("task_pass_count", 0)),
        semantic_ok_count=int(analysis.get("semantic_ok_count", 0)),
        provider_error_count=int(summary.get("provider_error_count", 0)),
        validator_ok_count=int(analysis.get("validator_ok_count", 0)),
        simulation_pass_count=int(analysis.get("simulation_pass_count", 0)),
    )


def build_report() -> dict[str, Any]:
    rows = {(model, row): _load_row(model, row) for model in MODELS for row in ROWS}
    by_model: list[dict[str, Any]] = []
    all_provider_clean = True
    all_signals_clear = True

    for model in MODELS:
        no_kb = rows[(model, "no_kb")]
        full_old = rows[(model, "full_old")]
        kb_v2_patch = rows[(model, "kb_v2_patch")]
        kb_v2_rewrite = rows[(model, "kb_v2_rewrite")]
        provider_clean = all(item.provider_error_count == 0 for item in (no_kb, full_old, kb_v2_patch, kb_v2_rewrite))
        kb_gain_visible = kb_v2_patch.task_pass_count > max(no_kb.task_pass_count, full_old.task_pass_count)
        patch_beats_rewrite = kb_v2_patch.task_pass_count > kb_v2_rewrite.task_pass_count
        all_provider_clean = all_provider_clean and provider_clean
        all_signals_clear = all_signals_clear and kb_gain_visible and patch_beats_rewrite
        by_model.append(
            {
                "model": model,
                "scores": {
                    row: {
                        "task_pass_count": rows[(model, row)].task_pass_count,
                        "semantic_ok_count": rows[(model, row)].semantic_ok_count,
                        "provider_error_count": rows[(model, row)].provider_error_count,
                    }
                    for row in ROWS
                },
                "kb_gain_visible": kb_gain_visible,
                "patch_beats_rewrite": patch_beats_rewrite,
                "provider_clean": provider_clean,
            }
        )

    ready_for_90 = all_provider_clean and all_signals_clear
    report = {
        "run_root": str(RUN_ROOT),
        "models": by_model,
        "ready_for_90": ready_for_90,
        "decision": (
            "advance_to_90"
            if ready_for_90
            else "keep_on_15_and_fix_contract_or_stability"
        ),
    }
    return report


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Authoring15 KB Decision Report",
        "",
        "## Gate Scope",
        "",
        "| 项目 | 目标 |",
        "|---|---|",
        "| 输出口径 | `protocol.py only` |",
        "| 消融对象 | `no_kb / full_old / kb_v2`，并比较 `patch_only / rewrite` |",
        "| 模型 | `flash`、`pro` |",
        "| 通过条件 | 15题结果能清楚回答“新 KB 有没有增益”“patch_only 是否优于 rewrite” |",
        "",
        "## Results",
        "",
        "| model | no_kb | full_old | kb_v2_patch | kb_v2_rewrite | kb gain visible | patch beats rewrite | provider clean |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for item in report["models"]:
        scores = item["scores"]
        lines.append(
            "| {model} | {no_kb} | {full_old} | {kb_v2_patch} | {kb_v2_rewrite} | {kb_gain} | {patch} | {clean} |".format(
                model=item["model"],
                no_kb=scores["no_kb"]["task_pass_count"],
                full_old=scores["full_old"]["task_pass_count"],
                kb_v2_patch=scores["kb_v2_patch"]["task_pass_count"],
                kb_v2_rewrite=scores["kb_v2_rewrite"]["task_pass_count"],
                kb_gain="yes" if item["kb_gain_visible"] else "no",
                patch="yes" if item["patch_beats_rewrite"] else "no",
                clean="yes" if item["provider_clean"] else "no",
            )
        )
    lines.extend(
        [
            "",
            f"- decision: `{report['decision']}`",
            f"- ready_for_90: `{str(report['ready_for_90']).lower()}`",
        ]
    )
    if report["ready_for_90"]:
        lines.extend(
            [
                "",
                "## 90-task Table",
                "",
                "| 模型 | no_kb | full_old | kb_v2_patch | kb_v2_rewrite | 结论 |",
                "|---|---:|---:|---:|---:|---|",
                "| flash |  |  |  |  | 新 KB 是否更强 |",
                "| pro |  |  |  |  | 新 KB 是否更强 |",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## 90-task Table",
                "",
                "当前不进入 `90题 × 两个模型`。先继续修稳定性或 provider 污染，再决定是否放大。",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_DIR / "report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
