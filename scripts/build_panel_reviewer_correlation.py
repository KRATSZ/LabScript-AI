#!/usr/bin/env python3
"""Correlate DeepSeek-90 Expert with GPT/Gemini 30-task panel scores across ablation rows."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_authoring90_ablation5_report import MODELS, ROWS, build_report


def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    for rank, index in enumerate(order, start=1):
        ranks[index] = float(rank)
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return _pearson(_rank(xs), _rank(ys))


def build_correlation_report(run_root: Path) -> dict[str, Any]:
    report = build_report(run_root)
    per_model: dict[str, Any] = {}
    for model in MODELS:
        payload = report["models"].get(model)
        if not payload:
            continue
        rows = payload["rows"]
        deepseek = [float(row["expert_mean"]) for row in rows if row.get("expert_mean") is not None]
        gpt = [
            float(row["expert_panel_gpt_mean"])
            for row in rows
            if row.get("expert_panel_gpt_mean") is not None
        ]
        gemini = [
            float(row["expert_panel_gemini_mean"])
            for row in rows
            if row.get("expert_panel_gemini_mean") is not None
        ]
        ensemble = [
            (gpt_value + gemini_value) / 2
            for gpt_value, gemini_value in zip(gpt, gemini)
        ]
        per_model[model] = {
            "rows": rows,
            "pearson": {
                "deepseek_vs_gpt_panel": _pearson(deepseek, gpt),
                "deepseek_vs_gemini_panel": _pearson(deepseek, gemini),
                "deepseek_vs_panel_ensemble": _pearson(deepseek, ensemble),
                "gpt_vs_gemini_panel": _pearson(gpt, gemini),
            },
            "spearman": {
                "deepseek_vs_gpt_panel": _spearman(deepseek, gpt),
                "deepseek_vs_gemini_panel": _spearman(deepseek, gemini),
                "deepseek_vs_panel_ensemble": _spearman(deepseek, ensemble),
            },
            "means": {
                "deepseek_90": sum(deepseek) / len(deepseek) if deepseek else None,
                "gpt_panel_30": sum(gpt) / len(gpt) if gpt else None,
                "gemini_panel_30": sum(gemini) / len(gemini) if gemini else None,
                "ensemble_panel_30": sum(ensemble) / len(ensemble) if ensemble else None,
            },
        }
    return {"run_root": str(run_root), "models": per_model}


def _to_markdown(report: dict[str, Any]) -> str:
    lines = ["# Panel reviewer correlation", ""]
    for model, payload in report["models"].items():
        lines.extend([f"## {model}", ""])
        lines.append("| row | Expert (90, DeepSeek) | Expert GPT (30) | Expert Gemini (30) |")
        lines.append("|---|---:|---:|---:|")
        for row in payload["rows"]:
            lines.append(
                "| {row} | {deepseek} | {gpt} | {gemini} |".format(
                    row=row["row"],
                    deepseek=_fmt(row.get("expert_mean")),
                    gpt=_fmt(row.get("expert_panel_gpt_mean")),
                    gemini=_fmt(row.get("expert_panel_gemini_mean")),
                )
            )
        lines.extend(
            [
                "",
                f"- Pearson DeepSeek vs GPT panel: {payload['pearson']['deepseek_vs_gpt_panel']}",
                f"- Pearson DeepSeek vs Gemini panel: {payload['pearson']['deepseek_vs_gemini_panel']}",
                f"- Pearson GPT vs Gemini panel: {payload['pearson']['gpt_vs_gemini_panel']}",
                f"- Spearman DeepSeek vs panel ensemble: {payload['spearman']['deepseek_vs_panel_ensemble']}",
                "",
            ]
        )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    return "NA" if value is None else f"{float(value):.2f}/5"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path, default=Path("runs/authoring90/ablation5_20260529"))
    args = parser.parse_args()
    report = build_correlation_report(args.run_root)
    out_dir = args.run_root / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "panel_correlation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "panel_correlation.md").write_text(_to_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
