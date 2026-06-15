"""Build the two-model, five-row Authoring90 ablation report."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODELS = ("flash", "pro")
ROWS = ("llm_direct", "no_kb_patch", "kb_v2_patch", "kb_v2_rewrite", "no_repair")
PANEL_TASK_COUNT = 30
PANEL_GPT_DIR = "expert_review_panel_gpt"
PANEL_GEMINI_DIR = "expert_review_panel_gemini"


@dataclass(frozen=True)
class RowMetrics:
    row: str
    task_count: int
    task_pass: int
    expert_mean: float | None
    expert_panel_gpt_mean: float | None
    expert_panel_gemini_mean: float | None
    review_ok_count: int
    panel_gpt_ok_count: int
    panel_gemini_ok_count: int
    simulation_pass: int
    semantic_ok: int
    validator_ok: int
    total_tokens: int
    tokens_per_task: float
    provider_error_count: int
    repair_tokens: int
    repair_tokens_mean: float
    patch_count: int
    patch_count_mean: float


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _records(summary: dict[str, Any]) -> list[dict[str, Any]]:
    records = summary.get("records", [])
    return [item for item in records if isinstance(item, dict)]


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _expert_mean(review_path: Path) -> float | None:
    if not review_path.exists():
        return None
    review = _load_json(review_path)
    expert_mean = review.get("mean_scores", {}).get("expert_score_mean")
    return float(expert_mean) if isinstance(expert_mean, (int, float)) else None


def _load_row(row_dir: Path, row: str) -> RowMetrics:
    summary = _load_json(row_dir / "summary.json")
    analysis = _load_json(row_dir / "analysis" / "attribution-summary.json")
    review_path = row_dir / "expert_review" / "review-summary.json"
    review = _load_json(review_path) if review_path.exists() else {}
    panel_gpt_path = row_dir / PANEL_GPT_DIR / "review-summary.json"
    panel_gemini_path = row_dir / PANEL_GEMINI_DIR / "review-summary.json"
    panel_gpt_review = _load_json(panel_gpt_path) if panel_gpt_path.exists() else {}
    panel_gemini_review = _load_json(panel_gemini_path) if panel_gemini_path.exists() else {}
    records = _records(summary)
    task_count = _int(summary.get("task_count"))
    total_tokens = _int(summary.get("total_tokens"))
    repair_tokens = sum(_int(record.get("repair_total_tokens")) for record in records)
    patch_count = sum(_int(record.get("repair_patch_count")) for record in records)
    return RowMetrics(
        row=row,
        task_count=task_count,
        task_pass=_int(analysis.get("task_pass_count")),
        expert_mean=_expert_mean(review_path),
        expert_panel_gpt_mean=_expert_mean(panel_gpt_path),
        expert_panel_gemini_mean=_expert_mean(panel_gemini_path),
        review_ok_count=_int(review.get("review_ok_count")),
        panel_gpt_ok_count=_int(panel_gpt_review.get("review_ok_count")),
        panel_gemini_ok_count=_int(panel_gemini_review.get("review_ok_count")),
        simulation_pass=_int(analysis.get("simulation_pass_count")),
        semantic_ok=_int(analysis.get("semantic_ok_count")),
        validator_ok=_int(analysis.get("validator_ok_count")),
        total_tokens=total_tokens,
        tokens_per_task=(total_tokens / task_count) if task_count else 0.0,
        provider_error_count=_int(summary.get("provider_error_count")),
        repair_tokens=repair_tokens,
        repair_tokens_mean=(repair_tokens / task_count) if task_count else 0.0,
        patch_count=patch_count,
        patch_count_mean=(patch_count / task_count) if task_count else 0.0,
    )


def _row_to_dict(row: RowMetrics) -> dict[str, Any]:
    return {
        "row": row.row,
        "task_count": row.task_count,
        "task_pass": row.task_pass,
        "expert_mean": row.expert_mean,
        "expert_panel_gpt_mean": row.expert_panel_gpt_mean,
        "expert_panel_gemini_mean": row.expert_panel_gemini_mean,
        "review_ok_count": row.review_ok_count,
        "panel_gpt_ok_count": row.panel_gpt_ok_count,
        "panel_gemini_ok_count": row.panel_gemini_ok_count,
        "simulation_pass": row.simulation_pass,
        "semantic_ok": row.semantic_ok,
        "validator_ok": row.validator_ok,
        "total_tokens": row.total_tokens,
        "tokens_per_task": row.tokens_per_task,
        "provider_error_count": row.provider_error_count,
        "repair_tokens": row.repair_tokens,
        "repair_tokens_mean": row.repair_tokens_mean,
        "patch_count": row.patch_count,
        "patch_count_mean": row.patch_count_mean,
    }


def _plain_conclusion(model: str, rows: dict[str, RowMetrics]) -> list[str]:
    r1 = rows["llm_direct"]
    r2 = rows["no_kb_patch"]
    r3 = rows["kb_v2_patch"]
    r4 = rows["kb_v2_rewrite"]
    r5 = rows["no_repair"]
    return [
        (
            f"{model}: 行2到行3看 KB，task_pass 从 {r2.task_pass}/90 到 {r3.task_pass}/90，"
            f"semantic_ok 从 {r2.semantic_ok}/90 到 {r3.semantic_ok}/90。"
        ),
        (
            f"{model}: 行3到行4看 patch vs rewrite，task_pass 是 {r3.task_pass}/90 vs "
            f"{r4.task_pass}/90，平均 repair tokens 是 {r3.repair_tokens_mean:.1f} vs "
            f"{r4.repair_tokens_mean:.1f}，平均 patch_count 是 {r3.patch_count_mean:.2f} vs "
            f"{r4.patch_count_mean:.2f}。"
        ),
        (
            f"{model}: 行3到行5看 fix-loop，repair 打开是 {r3.task_pass}/90，"
            f"repair 关闭是 {r5.task_pass}/90。"
        ),
        (
            f"{model}: 行1到行3看相对裸 LLM，直接生成是 {r1.task_pass}/90，"
            f"完整体是 {r3.task_pass}/90；token/task 是 {r1.tokens_per_task:.1f} vs "
            f"{r3.tokens_per_task:.1f}。"
        ),
    ]


def build_report(root: Path) -> dict[str, Any]:
    models: dict[str, Any] = {}
    for model in MODELS:
        model_dir = root / model
        if not model_dir.exists():
            continue
        row_metrics = {row: _load_row(model_dir / row, row) for row in ROWS}
        models[model] = {
            "rows": [_row_to_dict(row_metrics[row]) for row in ROWS],
            "conclusions": _plain_conclusion(model, row_metrics),
        }
    return {
        "run_root": str(root),
        "models": models,
        "acceptance": {
            model: {
                row.row: {
                    "task_count_is_90": row.task_count == 90,
                    "provider_error_count_is_0": row.provider_error_count == 0,
                    "review_ok_count_is_90": row.review_ok_count == 90,
                    "panel_gpt_ok_count_is_30": row.panel_gpt_ok_count == PANEL_TASK_COUNT,
                    "panel_gemini_ok_count_is_30": row.panel_gemini_ok_count == PANEL_TASK_COUNT,
                }
                for row in (RowMetrics(**item) for item in payload["rows"])
            }
            for model, payload in models.items()
        },
    }


def _format_count(value: int) -> str:
    return f"{value}/90"


def _format_expert(value: float | None) -> str:
    return "NA" if value is None else f"{value:.2f}/5"


def _markdown_table(model: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"## {model}",
        "",
        "| row | task_pass/90 | Expert | Expert GPT (30) | Expert Gemini (30) | simulation_pass/90 | semantic_ok | validator_ok | total_tokens | tokens/task | provider_error_count | repair tokens mean | patch_count mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        repair_mean = ""
        patch_mean = ""
        if row["row"] in {"kb_v2_patch", "kb_v2_rewrite"}:
            repair_mean = f"{row['repair_tokens_mean']:.1f}"
            patch_mean = f"{row['patch_count_mean']:.2f}"
        lines.append(
            "| {row} | {task_pass} | {expert} | {expert_gpt} | {expert_gemini} | {simulation_pass} | {semantic_ok} | {validator_ok} | "
            "{total_tokens} | {tokens_per_task:.1f} | {provider_error_count} | {repair_mean} | {patch_mean} |".format(
                row=row["row"],
                task_pass=_format_count(row["task_pass"]),
                expert=_format_expert(row["expert_mean"]),
                expert_gpt=_format_expert(row["expert_panel_gpt_mean"]),
                expert_gemini=_format_expert(row["expert_panel_gemini_mean"]),
                simulation_pass=_format_count(row["simulation_pass"]),
                semantic_ok=_format_count(row["semantic_ok"]),
                validator_ok=_format_count(row["validator_ok"]),
                total_tokens=row["total_tokens"],
                tokens_per_task=row["tokens_per_task"],
                provider_error_count=row["provider_error_count"],
                repair_mean=repair_mean,
                patch_mean=patch_mean,
            )
        )
    return lines


def _to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Authoring90 Ablation5 Report",
        "",
        "Table note: Task Pass means all four deterministic gates pass: simulation, validator, semantic, and param sweep. "
        "Expert is the mean 1-5 score from DeepSeek V4 Pro over all 90 tasks. "
        "Expert GPT (30) and Expert Gemini (30) are the same reviewer rubric on the frozen "
        f"{PANEL_TASK_COUNT}-task stratified panel (`benchmarks/authoring/review_panel_30.json`) via LLM_ONLY API.",
        "",
    ]
    for model in MODELS:
        payload = report["models"].get(model)
        if not payload:
            continue
        lines.extend(_markdown_table(model, payload["rows"]))
        lines.extend(["", "### Conclusion", ""])
        for sentence in payload["conclusions"]:
            lines.append(f"- {sentence}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()

    report = build_report(args.run_root)
    out_dir = args.run_root / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(_to_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
