#!/usr/bin/env python3
"""Build TABLE_LLM_ONLY.md from llm_only benchmark summaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_pass_count(summary: dict[str, Any], analysis: dict[str, Any]) -> int:
    gen_by_task = {
        str(r.get("task_id")): int(r.get("generation_attempts", 0))
        for r in summary.get("records", [])
        if isinstance(r, dict) and r.get("task_id")
    }
    count = 0
    for row in analysis.get("per_task", []):
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("task_id"))
        if gen_by_task.get(task_id, 99) != 1:
            continue
        if (
            row.get("simulation_ok")
            and row.get("validator_ok")
            and row.get("semantic_ok")
            and row.get("param_sweep_ok")
        ):
            count += 1
    return count


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


def _final_provider_error_count(summary: dict[str, Any]) -> int:
    records = summary.get("records", [])
    if not isinstance(records, list):
        return 0
    return sum(1 for record in records if isinstance(record, dict) and _record_final_provider_error(record))


def _model_row(
    label: str,
    model_dir: Path,
    *,
    setting: str,
) -> dict[str, str]:
    summary = _load(model_dir / "summary.json")
    analysis = _load(model_dir / "analysis" / "attribution-summary.json")
    n = int(analysis.get("task_count", 0)) or int(summary.get("task_count", 0))
    fp = _first_pass_count(summary, analysis)
    tokens = int(summary.get("total_tokens", 0))
    tpt = f"{tokens / n:.0f}" if n else "?"
    shard_summary = model_dir / "shard01" / "summary.json"
    meta = _load(shard_summary) if shard_summary.exists() else summary
    model_id = str(meta.get("model_id", summary.get("model_id", model_dir.name)))
    generated_at = str(meta.get("generated_at", ""))
    notes = f"run: `{model_dir}`; model_id={model_id}"
    if generated_at:
        notes += f"; generated_at={generated_at}"
    return {
        "System": label,
        "Class": "Frontier LLM",
        "Setting": setting,
        "Authoring FP": f"{fp}/{n}",
        "Authoring BoB": f"{analysis.get('task_pass_count', '?')}/{n}",
        "Sim†": f"{analysis.get('simulation_pass_count', '?')}/{n}",
        "Val": f"{analysis.get('validator_ok_count', '?')}/{n}",
        "Sem": f"{analysis.get('semantic_ok_count', '?')}/{n}",
        "Param": f"{analysis.get('param_sweep_ok_count', '?')}/{n}",
        "Tokens/task": tpt,
        "Provider events": str(int(summary.get("provider_error_count", 0))),
        "Final API fail": str(_final_provider_error_count(summary)),
        "Notes": notes,
    }


def _pending_model_row(label: str, model_dir: Path, *, setting: str) -> dict[str, str]:
    return {
        "System": label,
        "Class": "Frontier LLM",
        "Setting": setting,
        "Authoring FP": "NA",
        "Authoring BoB": "NA",
        "Sim†": "NA",
        "Val": "NA",
        "Sem": "NA",
        "Param": "NA",
        "Tokens/task": "NA",
        "Provider events": "NA",
        "Final API fail": "NA",
        "Notes": f"run: `{model_dir}`; missing summary/analysis",
    }


def _model_row_or_pending(label: str, model_dir: Path, *, setting: str) -> dict[str, str]:
    if not (model_dir / "summary.json").is_file():
        return _pending_model_row(label, model_dir, setting=setting)
    if not (model_dir / "analysis" / "attribution-summary.json").is_file():
        return _pending_model_row(label, model_dir, setting=setting)
    return _model_row(label, model_dir, setting=setting)


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("runs/authoring90/llm_only")
    setting = (
        "90 tasks; direct py-only; local sim; no agent/fix-loop; base gen retry≤4; targeted API retry≤6 where noted"
    )
    rows = [
        _model_row_or_pending("GPT-5.5 direct", root / "gpt-5.5_vector", setting=setting),
        _model_row_or_pending(
            "Gemini 3.5 Flash direct",
            root / "gemini-3.5-flash",
            setting=setting,
        ),
        _model_row_or_pending(
            "Claude Opus 4.8 direct",
            root / "claude-opus-4-8",
            setting=setting,
        ),
    ]
    headers = list(rows[0].keys())
    lines = [
        "# Table 1 — Frontier LLM direct (llm_only)",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[h] for h in headers) + " |")
    lines.extend(["", "Expert / Runtime / Memory: — (not measured in this run).", ""])
    out = root / "TABLE_LLM_ONLY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
