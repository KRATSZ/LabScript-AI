#!/usr/bin/env python3
"""Plot Table 1 runs as tokens/task vs FinalPass Pareto points."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_RUNS = (
    ("Flash seed01", "runs/table1_v3_fair/flash_seed01"),
    ("Flash seed02", "runs/table1_v3_fair/flash_seed02"),
    ("Flash seed03", "runs/table1_v3_fair/flash_seed03"),
    ("Codex fair", "runs/table1_v3_fair/codex_gpt55_fair"),
    ("Claude fair", "runs/table1_v3_fair/claude_opus48_tight_fair"),
    ("DeepSeek direct", "runs/table1_v2_llm_only_py90_official_deepseek_final"),
)


@dataclass(frozen=True)
class Point:
    label: str
    root: Path
    task_count: int
    final_pass_count: int
    tokens_per_task: float
    provider_error_count: int
    final_api_fail_count: int

    @property
    def final_pass_rate(self) -> float:
        return self.final_pass_count / self.task_count if self.task_count else 0.0

    @property
    def eligible(self) -> bool:
        if self.task_count <= 0:
            return False
        return (
            self.provider_error_count / self.task_count <= 0.05
            and self.final_api_fail_count / self.task_count <= 0.05
        )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _record_final_provider_error(record: dict[str, Any]) -> bool:
    if record.get("error"):
        return True
    for key, value in record.items():
        if key.endswith("_returncode") and value is not None and _as_int(value) != 0:
            return True
    return _as_int(record.get("provider_error_count")) > 0 and _as_int(record.get("total_tokens")) <= 0


def _final_api_fail_count(summary: dict[str, Any]) -> int:
    records = summary.get("records", [])
    if not isinstance(records, list):
        return 0
    return sum(1 for record in records if isinstance(record, dict) and _record_final_provider_error(record))


def _load_point(label: str, root: Path) -> Point | None:
    summary = _load_json(root / "summary.json")
    analysis = _load_json(root / "analysis" / "attribution-summary.json")
    task_count = int(analysis.get("task_count") or summary.get("task_count") or 0)
    if task_count <= 0:
        return None
    total_tokens = int(summary.get("total_tokens", 0) or 0)
    return Point(
        label=label,
        root=root,
        task_count=task_count,
        final_pass_count=int(analysis.get("task_pass_count", 0) or 0),
        tokens_per_task=total_tokens / task_count if task_count else 0.0,
        provider_error_count=int(summary.get("provider_error_count", 0) or 0),
        final_api_fail_count=_final_api_fail_count(summary),
    )


def _parse_run_specs(values: list[str]) -> list[tuple[str, Path]]:
    if not values:
        return [(label, Path(path)) for label, path in DEFAULT_RUNS]
    specs: list[tuple[str, Path]] = []
    for value in values:
        if "=" not in value:
            path = Path(value)
            specs.append((path.name, path))
            continue
        label, path = value.split("=", 1)
        specs.append((label.strip(), Path(path.strip())))
    return specs


def _scale_log(value: float, min_log: float, max_log: float, left: float, right: float) -> float:
    if max_log <= min_log:
        return (left + right) / 2
    return left + (math.log10(max(value, 1.0)) - min_log) / (max_log - min_log) * (right - left)


def _scale_linear(value: float, bottom: float, top: float) -> float:
    return bottom - value * (bottom - top)


def _write_csv(points: list[Point], output: Path) -> None:
    csv_path = output.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "label",
                "root",
                "task_count",
                "final_pass_count",
                "final_pass_rate",
                "tokens_per_task",
                "provider_error_count",
                "final_api_fail_count",
                "eligible",
            ]
        )
        for point in points:
            writer.writerow(
                [
                    point.label,
                    point.root,
                    point.task_count,
                    point.final_pass_count,
                    f"{point.final_pass_rate:.6f}",
                    f"{point.tokens_per_task:.3f}",
                    point.provider_error_count,
                    point.final_api_fail_count,
                    point.eligible,
                ]
            )


def _write_svg(points: list[Point], output: Path) -> None:
    width, height = 980, 620
    left, right = 96, 920
    top, bottom = 64, 520
    eligible_points = [point for point in points if point.tokens_per_task > 0]
    token_values = [point.tokens_per_task for point in eligible_points] or [1.0, 10.0]
    min_log = math.floor(math.log10(max(min(token_values), 1.0)))
    max_log = math.ceil(math.log10(max(token_values)))
    if min_log == max_log:
        max_log += 1

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#1f2933} .axis{stroke:#394b59;stroke-width:1.4} .grid{stroke:#d8dee6;stroke-width:1} .label{font-size:14px} .small{font-size:12px;fill:#52616f} .title{font-size:20px;font-weight:700}",
        "</style>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="34" class="title">Table 1 v3 Pareto: cost vs FinalPass</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" class="axis"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" class="axis"/>',
    ]
    for i in range(6):
        rate = i / 5
        y = _scale_linear(rate, bottom, top)
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="grid"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="small">{rate:.0%}</text>')
    for exponent in range(int(min_log), int(max_log) + 1):
        value = 10**exponent
        x = _scale_log(value, min_log, max_log, left, right)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" class="grid"/>')
        lines.append(f'<text x="{x:.1f}" y="{bottom + 24}" text-anchor="middle" class="small">{value:g}</text>')
    lines.append(f'<text x="{(left + right) / 2:.1f}" y="{height - 30}" text-anchor="middle" class="label">tokens per task (log scale)</text>')
    lines.append(f'<text x="28" y="{(top + bottom) / 2:.1f}" transform="rotate(-90 28 {(top + bottom) / 2:.1f})" text-anchor="middle" class="label">FinalPass / task count</text>')

    palette = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#ff7f0e", "#111827", "#17becf"]
    for index, point in enumerate(points):
        if point.tokens_per_task <= 0:
            continue
        x = _scale_log(point.tokens_per_task, min_log, max_log, left, right)
        y = _scale_linear(point.final_pass_rate, bottom, top)
        color = palette[index % len(palette)]
        opacity = "1" if point.eligible else "0.32"
        stroke = "#111827" if point.eligible else "#9aa5b1"
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="1.5"/>')
        lines.append(f'<text x="{x + 10:.1f}" y="{y - 8:.1f}" class="small">{point.label}</text>')
        lines.append(
            f'<text x="{x + 10:.1f}" y="{y + 8:.1f}" class="small">'
            f'{point.final_pass_count}/{point.task_count}, {point.tokens_per_task:.0f} tok/task'
            f'{" excluded" if not point.eligible else ""}</text>'
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", default=[], help="Label=path. Defaults to Table 1 v3 paths.")
    parser.add_argument("--output", type=Path, default=Path("runs/table1_v3_fair/table1_pareto.svg"))
    args = parser.parse_args()

    points = [
        point
        for label, root in _parse_run_specs(args.run)
        for point in [_load_point(label, root)]
        if point is not None
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(points, args.output)
    _write_svg(points, args.output)
    print(args.output)
    print(args.output.with_suffix(".csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
