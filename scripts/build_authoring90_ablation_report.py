"""Summarize a pro-only 90-task authoring ablation into one table."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROWS = ("no_kb", "new_kb", "kb_v2_patch", "kb_v2_rewrite", "full")


@dataclass(frozen=True)
class RowResult:
    row: str
    task_count: int
    task_pass_count: int
    semantic_ok_count: int
    simulation_pass_count: int
    validator_ok_count: int
    provider_error_count: int


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_row(run_root: Path, row: str) -> RowResult:
    row_dir = run_root / row
    summary = _load_json(row_dir / "summary.json")
    analysis = _load_json(row_dir / "analysis" / "attribution-summary.json")
    return RowResult(
        row=row,
        task_count=int(summary.get("task_count", 0)),
        task_pass_count=int(analysis.get("task_pass_count", 0)),
        semantic_ok_count=int(analysis.get("semantic_ok_count", 0)),
        simulation_pass_count=int(analysis.get("simulation_pass_count", 0)),
        validator_ok_count=int(analysis.get("validator_ok_count", 0)),
        provider_error_count=int(summary.get("provider_error_count", 0)),
    )


def build_report(run_root: Path) -> dict[str, Any]:
    rows = {row: _load_row(run_root, row) for row in ROWS}
    new_kb_gain_visible = rows["new_kb"].task_pass_count > rows["no_kb"].task_pass_count
    patch_beats_rewrite = rows["kb_v2_patch"].task_pass_count > rows["kb_v2_rewrite"].task_pass_count
    report = {
        "run_root": str(run_root),
        "rows": {
            row: {
                "task_count": rows[row].task_count,
                "task_pass_count": rows[row].task_pass_count,
                "semantic_ok_count": rows[row].semantic_ok_count,
                "simulation_pass_count": rows[row].simulation_pass_count,
                "validator_ok_count": rows[row].validator_ok_count,
                "provider_error_count": rows[row].provider_error_count,
            }
            for row in ROWS
        },
        "new_kb_gain_visible": new_kb_gain_visible,
        "patch_beats_rewrite": patch_beats_rewrite,
    }
    return report


def _markdown(report: dict[str, Any]) -> str:
    rows = report["rows"]
    lines = [
        "# Authoring90 Pro Ablation Report",
        "",
        "| 模型 | no_kb | 新 KB | kb_v2_patch | kb_v2_rewrite | full | 结论 |",
        "|---|---:|---:|---:|---:|---:|---|",
        (
            "| pro | {no_kb} | {new_kb} | {kb_v2_patch} | {kb_v2_rewrite} | {full} | "
            "新 KB>{no_kb_flag}; patch>rewrite={patch_flag} |"
        ).format(
            no_kb=rows["no_kb"]["task_pass_count"],
            new_kb=rows["new_kb"]["task_pass_count"],
            kb_v2_patch=rows["kb_v2_patch"]["task_pass_count"],
            kb_v2_rewrite=rows["kb_v2_rewrite"]["task_pass_count"],
            full=rows["full"]["task_pass_count"],
            no_kb_flag="yes" if report["new_kb_gain_visible"] else "no",
            patch_flag="yes" if report["patch_beats_rewrite"] else "no",
        ),
        "",
        "## Provider Errors",
        "",
        "| row | provider_error_count |",
        "|---|---:|",
    ]
    for row in ROWS:
        lines.append(f"| {row} | {rows[row]['provider_error_count']} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.run_root)
    out_dir = args.run_root / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
