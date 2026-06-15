#!/usr/bin/env python3
"""Audit Table 1 30-task panel reviewer completion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RUN_ROOTS = (
    "runs/table1_v2_unified_opus_48",
    "runs/authoring90/ablation5_20260529/flash/kb_v2_patch",
    "runs/authoring90/llm_only/claude-opus-4-8",
    "runs/authoring90_native_agents/codex_gpt55_py_only_v1",
    "runs/table1_v2_llm_only_py90_official_deepseek_final",
    "runs/authoring90/llm_only/gemini-3.5-flash",
    "runs/authoring90/llm_only/gpt-5.5_vector",
    "runs/authoring90_native_agents/claude_opus48_pyonly_tight_v2",
    "runs/authoring90_native_agents/claude_opus48_native_open_v1",
    "runs/authoring90/inagaki_style/gpt-4-fixloop-v2",
)

REVIEWERS = (
    ("deepseek", "expert_review_panel_deepseek"),
    ("gpt", "expert_review_panel_gpt"),
    ("gemini", "expert_review_panel_gemini"),
)

PANEL_TASK_COUNT = 30


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_score(value: Any) -> str:
    return "NA" if not isinstance(value, (int, float)) else f"{float(value):.2f}/5"


def _task_file_stats(review_dir: Path) -> dict[str, Any]:
    ok_count = 0
    bad_count = 0
    errors: list[str] = []
    for path in sorted(review_dir.glob("T*-review.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - audit should report malformed files.
            bad_count += 1
            errors.append(f"{path.name}: {type(exc).__name__}")
            continue
        if payload.get("ok") is True:
            ok_count += 1
        else:
            bad_count += 1
            error = payload.get("error")
            if error:
                errors.append(f"{path.name}: {str(error)[:160]}")
    return {
        "task_review_file_count": ok_count + bad_count,
        "task_review_ok_file_count": ok_count,
        "task_review_bad_file_count": bad_count,
        "sample_errors": errors[:5],
    }


def _reviewer_status(run_root: Path, dirname: str) -> dict[str, Any]:
    review_dir = run_root / dirname
    summary = _load_optional(review_dir / "review-summary.json")
    file_stats = _task_file_stats(review_dir)
    review_count = summary.get("review_count")
    ok_count = summary.get("review_ok_count")
    score = summary.get("mean_scores", {}).get("expert_score_mean") if summary else None
    complete = ok_count == PANEL_TASK_COUNT and review_count == PANEL_TASK_COUNT
    return {
        "dir": dirname,
        "review_summary": str(review_dir / "review-summary.json"),
        "status": "complete" if complete else ("incomplete" if summary or file_stats["task_review_file_count"] else "missing"),
        "review_count": review_count,
        "review_ok_count": ok_count,
        "model": summary.get("reviewer", {}).get("model") if summary else None,
        "expert_score_mean": score if isinstance(score, (int, float)) else None,
        **file_stats,
    }


def _panel_mean(reviewers: dict[str, dict[str, Any]]) -> float | None:
    scores: list[float] = []
    for payload in reviewers.values():
        if payload["status"] != "complete":
            return None
        summary = _load_optional(Path(payload["review_summary"]))
        for item in summary.get("per_task", []):
            if (
                isinstance(item, dict)
                and item.get("ok") is True
                and isinstance(item.get("expert_score_mean"), (int, float))
            ):
                scores.append(float(item["expert_score_mean"]))
    return (sum(scores) / len(scores)) if len(scores) == PANEL_TASK_COUNT * len(REVIEWERS) else None


def build_status(run_roots: tuple[str, ...] = RUN_ROOTS) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for root_value in run_roots:
        run_root = Path(root_value)
        reviewers = {
            name: _reviewer_status(run_root, dirname)
            for name, dirname in REVIEWERS
        }
        panel_mean = _panel_mean(reviewers)
        rows.append(
            {
                "run_root": root_value,
                "complete": panel_mean is not None,
                "expert_panel_3llm_mean": panel_mean,
                "reviewers": reviewers,
            }
        )
    return {
        "panel_task_count": PANEL_TASK_COUNT,
        "reviewer_count": len(REVIEWERS),
        "run_count": len(rows),
        "complete_run_count": sum(1 for row in rows if row["complete"]),
        "rows": rows,
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Table 1 Panel Review Status",
        "",
        f"Complete rows: {report['complete_run_count']}/{report['run_count']}",
        "",
        "| Run | DeepSeek | GPT | Gemini | Expert panel mean |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in report["rows"]:
        reviewers = row["reviewers"]
        lines.append(
            "| {run} | {deepseek} | {gpt} | {gemini} | {panel} |".format(
                run=row["run_root"],
                deepseek=_reviewer_cell(reviewers["deepseek"]),
                gpt=_reviewer_cell(reviewers["gpt"]),
                gemini=_reviewer_cell(reviewers["gemini"]),
                panel=_fmt_score(row["expert_panel_3llm_mean"]),
            )
        )
    incomplete = [row for row in report["rows"] if not row["complete"]]
    if incomplete:
        lines.extend(["", "## Incomplete Details", ""])
        for row in incomplete:
            lines.append(f"- `{row['run_root']}`")
            for name, payload in row["reviewers"].items():
                if payload["status"] == "complete":
                    continue
                errors = "; ".join(payload["sample_errors"]) or "none"
                lines.append(
                    f"  - {name}: {payload['status']}, summary={payload['review_ok_count']}/{payload['review_count']}, "
                    f"files={payload['task_review_ok_file_count']}/{payload['task_review_file_count']}, errors={errors}"
                )
    lines.append("")
    return "\n".join(lines)


def _reviewer_cell(payload: dict[str, Any]) -> str:
    if payload["status"] == "complete":
        return f"30/30 {payload['model']} {_fmt_score(payload['expert_score_mean'])}"
    if payload["review_count"] is not None or payload["review_ok_count"] is not None:
        return f"{payload['review_ok_count']}/{payload['review_count']} {payload['status']}"
    file_count = payload["task_review_file_count"]
    ok_count = payload["task_review_ok_file_count"]
    return f"{ok_count}/{file_count} {payload['status']}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 unless all 9 rows are complete.")
    parser.add_argument("--out-dir", type=Path, default=Path("runs"), help="Where to write status artifacts.")
    parser.add_argument("--no-write", action="store_true", help="Do not write status artifacts.")
    args = parser.parse_args()

    report = build_status()
    if not args.no_write:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "table1_panel_review_status.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (args.out_dir / "table1_panel_review_status.md").write_text(
            to_markdown(report),
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(to_markdown(report))
    if args.strict and report["complete_run_count"] != report["run_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
