#!/usr/bin/env python3
"""Build the Table 1 v2 markdown summary from frozen run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TableRow:
    task_set: str
    row_class: str
    row_label: str
    root: Path
    note: str = ""
    panel_expected: bool = False


ROWS = (
    TableRow(
        task_set="Main 90",
        row_class="LLM-only",
        row_label="DeepSeek LLM-only py-only",
        root=Path("runs/table1_v2_llm_only_py90_official_deepseek_final"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Literature",
        row_label="GPT-4 + fix-loop (Inagaki-style)",
        root=Path("runs/authoring90/inagaki_style/gpt-4-fixloop-v2"),
        note=(
            "LLM_ONLY_MODEL=gpt-4 via VectorEngine; quota-failed and missing tasks resumed "
            "from retry root; SIMULATION_REPAIR_ATTEMPTS=3; provider_error_count=0."
        ),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Official tool",
        row_label="OpentronsAI (web chat)",
        root=Path("runs/authoring90/opentrons_ai_v1"),
        note=(
            "Official NL tool via ai.opentrons.com; flattened py-only prompt "
            "(no system role); single session/task; sidecars harness-derived; "
            "unsupported/no-code responses retained in denominator."
        ),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only (deepseek-v4-flash)",
        root=Path("runs/authoring90/ablation5_20260529/flash/kb_v2_patch"),
        note=(
            "Table 1 anchor: ablation5 flash best unified py-only row "
            "(KB v2 + patch repair, repair_edit_mode=patch_only, provider_error_count=0). "
            "Supersedes runs/table1_v2_unified_py90_official_deepseek_pure (58/90 BoB, rewrite repair)."
        ),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only (Opus 4.8)",
        root=Path("runs/table1_v2_unified_opus_48"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="GPT-5.5 direct py-only",
        root=Path("runs/authoring90/llm_only/gpt-5.5_vector"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="Gemini 3.5 Flash direct py-only",
        root=Path("runs/authoring90/llm_only/gemini-3.5-flash"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="Claude Opus 4.8 direct py-only",
        root=Path("runs/authoring90/llm_only/claude-opus-4-8"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Codex native agent py-only",
        root=Path("runs/authoring90_native_agents/codex_gpt55_py_only_v1"),
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code A tight py-only (local GLM-5.1 codingplan)",
        root=Path("runs/authoring90_native_agents/claude_glm51_a_tight_22_90_v1"),
        note="A: preserved pre-Opus GLM evidence; py-only fair setting; empty scratch; empty MCP; Write/Bash tools only; no LabscriptAI sim/MCP.",
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code A tight py-only (Opus 4.8 vector)",
        root=Path("runs/authoring90_native_agents/claude_opus48_pyonly_tight_v2"),
        note="A: py-only fair setting; vector Anthropic-compatible Opus 4.8 route; empty scratch; empty MCP; Write/Bash tools only; no LabscriptAI sim/MCP.",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code B open native py-only (local GLM-5.1 codingplan)",
        root=Path("runs/authoring90_native_agents/claude_opus48_native_open_v1"),
        note="B: product default tools; empty scratch; empty MCP; no LabscriptAI sim/MCP; outer harness derives and simulates.",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="OpenClaw native agent py-only",
        root=Path("runs/authoring90_native_agents/openclaw_py_only_v1"),
        note="OpenClaw row is populated only when openclaw is installed and run.",
    ),
    TableRow(
        task_set="External 66",
        row_class="LLM-only",
        row_label="DeepSeek LLM-only py-only",
        root=Path("runs/table1_v2_external66_llm_only_py_official_deepseek"),
    ),
    TableRow(
        task_set="External 66",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only",
        root=Path("runs/table1_v2_external66_unified_py_official_deepseek_pure"),
    ),
)

PANEL_TASK_COUNT = 30
PANEL_REVIEW_DIRS = (
    ("DeepSeek", "expert_review_panel_deepseek"),
    ("GPT", "expert_review_panel_gpt"),
    ("Gemini", "expert_review_panel_gemini"),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return _load(path)


def _fmt_count(value: int | None, total: int) -> str:
    if total <= 0:
        return "NA"
    return f"{0 if value is None else value}/{total}"


def _fmt_expert(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2f}/5"
    return "NA"


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _panel_task_scores(review: dict[str, Any]) -> list[float]:
    rows = review.get("per_task", [])
    if not isinstance(rows, list):
        return []
    scores: list[float] = []
    for item in rows:
        if not isinstance(item, dict) or item.get("ok") is not True:
            continue
        score = _numeric(item.get("expert_score_mean"))
        if score is not None:
            scores.append(score)
    return scores


def _panel_expert_mean(root: Path) -> float | None:
    scores: list[float] = []
    for _label, dirname in PANEL_REVIEW_DIRS:
        review = _load_optional(root / dirname / "review-summary.json")
        if int(review.get("review_ok_count", 0)) != PANEL_TASK_COUNT:
            return None
        reviewer_scores = _panel_task_scores(review)
        if len(reviewer_scores) != PANEL_TASK_COUNT:
            return None
        scores.extend(reviewer_scores)
    return (sum(scores) / len(scores)) if scores else None


def _panel_status(root: Path) -> str:
    parts: list[str] = []
    for label, dirname in PANEL_REVIEW_DIRS:
        review = _load_optional(root / dirname / "review-summary.json")
        if not review:
            parts.append(f"{label}: missing")
            continue
        ok_count = int(review.get("review_ok_count", 0))
        review_count = int(review.get("review_count", 0))
        model = review.get("reviewer", {}).get("model")
        model_note = f" {model}" if model else ""
        parts.append(f"{label}: {ok_count}/{review_count}{model_note}")
    return ", ".join(parts)


def _first_pass_count(summary: dict[str, Any], analysis: dict[str, Any], total: int) -> int | None:
    if not analysis:
        value = summary.get("first_pass_simulation_pass_count")
        if value is None:
            return None
        return int(value)
    gen_by_task = {
        str(record.get("task_id")): int(record.get("generation_attempts", 0))
        for record in summary.get("records", [])
        if isinstance(record, dict) and record.get("task_id")
    }
    count = 0
    saw_rows = False
    for item in analysis.get("per_task", []):
        if not isinstance(item, dict):
            continue
        saw_rows = True
        task_id = str(item.get("task_id"))
        if gen_by_task.get(task_id, 99) != 1:
            continue
        if int(item.get("simulation_repair_attempts", 0)) != 0:
            continue
        if not item.get("first_pass_simulation_ok"):
            continue
        if (
            item.get("simulation_ok")
            and item.get("validator_ok")
            and item.get("semantic_ok")
            and item.get("param_sweep_ok")
        ):
            count += 1
    if saw_rows:
        return count
    if total:
        return int(summary.get("first_pass_simulation_pass_count", 0))
    return None


def _total(summary: dict[str, Any], analysis: dict[str, Any]) -> int:
    return int(summary.get("task_count") or analysis.get("task_count") or 0)


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


def _status(
    summary: dict[str, Any],
    analysis: dict[str, Any],
    review: dict[str, Any],
    *,
    panel_expected: bool = False,
    panel_expert: float | None = None,
) -> str:
    if not summary:
        return "missing"
    parts = ["complete" if int(summary.get("task_count", 0)) else "partial"]
    if not analysis:
        parts.append("analysis_missing")
    if not review:
        parts.append("expert_missing")
    if panel_expected and panel_expert is None:
        parts.append("expert_panel_missing")
    return "; ".join(parts)


def build_table(rows: tuple[TableRow, ...] = ROWS) -> str:
    lines = [
        "# Table 1 v2 combined benchmark summary",
        "",
        "Date: 2026-06-11",
        "",
        "All rows use the py-only benchmark contract: the model writes `protocol.py`; "
        "benchmark tooling derives `manifest.json` and `setup_card.html` from that "
        "protocol before validation and simulation.",
        "",
        "Expert panel: n=30 stratified tasks; blind LLM reviewers (DeepSeek-V4-Pro, GPT-5.4, Gemini-3-Flash primary with Gemini-3.5-Flash fallback when required); DeepSeek via official API, GPT/Gemini via VectorEngine; scores final package only, no authoring trace; table value = mean of three reviewers.",
        "",
        "| Set | Class | Row | N | FP | BoB | Sim | Val | Expert | Expert panel (3-LLM mean) | Tokens | Tokens/task | Provider events | Final API fail | Tool calls | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    detail_lines = ["", "Detailed evidence:", ""]
    for row in rows:
        summary = _load_optional(row.root / "summary.json")
        analysis = _load_optional(row.root / "analysis" / "attribution-summary.json")
        review = _load_optional(row.root / "expert_review" / "review-summary.json")
        panel_expert = _panel_expert_mean(row.root) if row.panel_expected else None
        total = _total(summary, analysis)
        fp = _first_pass_count(summary, analysis, total)
        bob = int(analysis.get("task_pass_count", 0)) if analysis else None
        sim = int(summary.get("simulation_pass_count", 0)) if summary else None
        val = int(summary.get("validator_ok_count", analysis.get("validator_ok_count", 0))) if summary or analysis else None
        expert = review.get("mean_scores", {}).get("expert_score_mean")
        tokens = int(summary.get("total_tokens", 0))
        tokens_per_task = f"{tokens / total:.0f}" if total else "NA"
        provider_events = int(summary.get("provider_error_count", 0))
        final_provider_failures = _final_provider_error_count(summary)
        tool_calls = int(summary.get("tool_calls", 0))
        status = _status(
            summary,
            analysis,
            review,
            panel_expected=row.panel_expected,
            panel_expert=panel_expert,
        )
        lines.append(
            "| {task_set} | {row_class} | {row_label} | {total} | {fp} | {bob} | {sim} | {val} | {expert} | {panel_expert} | {tokens} | {tokens_per_task} | {provider_events} | {final_provider_failures} | {tool_calls} | {status} |".format(
                task_set=row.task_set,
                row_class=row.row_class,
                row_label=row.row_label,
                total=total or "NA",
                fp=_fmt_count(fp, total),
                bob=_fmt_count(bob, total),
                sim=_fmt_count(sim, total),
                val=_fmt_count(val, total),
                expert=_fmt_expert(expert),
                panel_expert=_fmt_expert(panel_expert),
                tokens=tokens,
                tokens_per_task=tokens_per_task,
                provider_events=provider_events,
                final_provider_failures=final_provider_failures,
                tool_calls=tool_calls,
                status=status,
            )
        )
        note = f"; {row.note}" if row.note else ""
        panel_note = f"; panel={_panel_status(row.root)}" if row.panel_expected else ""
        detail_lines.append(f"- {row.task_set} {row.row_label}: `{row.root}`{note}{panel_note}")
    smoke = Path("runs/table1_v2_historical_derive_smoke/summary.json")
    if smoke.exists():
        payload = _load(smoke)
        detail_lines.append(
            "- Historical derive smoke: `runs/table1_v2_historical_derive_smoke` "
            f"({payload.get('package_complete_count', 0)}/{payload.get('task_count', 0)} package-complete)"
        )
    lines.extend(detail_lines)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    out = Path("runs/table1_v2_combined_summary.md")
    out.write_text(build_table(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
