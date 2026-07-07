#!/usr/bin/env python3
"""Build the Table 1 v3 markdown summary from frozen run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
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
    tools_budget: str = ""
    cost_model: str = ""


ROWS = (
    TableRow(
        task_set="Main 90",
        row_class="LLM-only",
        row_label="DeepSeek LLM-only py-only",
        root=Path("runs/table1_v2_llm_only_py90_official_deepseek_final"),
        tools_budget="LLM-only; retry=2; max_tokens=12000",
        cost_model="deepseek-v4-pro",
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
        tools_budget="Fix-loop; repair<=3; retry=2",
        cost_model="gpt-4",
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
        tools_budget="Official web chat; py-only; harness derive",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only (deepseek-v4-flash seed01)",
        root=Path("runs/table1_v3_fair/flash_seed01"),
        note=(
            "Table 1 v3 anchor seed; seed02/seed03 are summarized in "
            "runs/table1_v3_fair/robustness_report.md. KB v2 + compact_v2 + "
            "patch_only repair, repair<=3, provider_error_count=0."
        ),
        tools_budget="KB v2 compact; patch_only repair<=3; retry=2; max_tokens=12000",
        cost_model="deepseek-v4-flash",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only (Opus 4.8)",
        root=Path("runs/table1_v2_unified_opus_48"),
        note="Carry-over row; LabscriptAI Opus was not rerun in the Table 1 v3 fair pass.",
        tools_budget="KB v2 + repair; carry-over",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="GPT-5.5 direct py-only",
        root=Path("runs/authoring90/llm_only/gpt-5.5_vector"),
        tools_budget="LLM-only direct; py-only",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="Gemini 3.5 Flash direct py-only",
        root=Path("runs/authoring90/llm_only/gemini-3.5-flash"),
        tools_budget="LLM-only direct; py-only",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Frontier LLM",
        row_label="Claude Opus 4.8 direct py-only",
        root=Path("runs/authoring90/llm_only/claude-opus-4-8"),
        tools_budget="LLM-only direct; py-only",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Codex native agent fair py-only (gpt-5.5)",
        root=Path("runs/table1_v3_fair/codex_gpt55_fair"),
        note=(
            "Table 1 v3 fair baseline: Codex CLI authoring, harness derive, "
            "rewrite repair<=3 via LLM_ONLY gpt-5.5. Exclude from main table "
            "if provider/final API fail rate exceeds 5%."
        ),
        tools_budget="Codex CLI; rewrite repair<=3; retry=2; max_tokens=12000",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code A tight py-only (local GLM-5.1 codingplan)",
        root=Path("runs/authoring90_native_agents/claude_glm51_a_tight_22_90_v1"),
        note="A: preserved pre-Opus GLM evidence; py-only fair setting; empty scratch; empty MCP; Write/Bash tools only; no LabscriptAI sim/MCP.",
        tools_budget="Native agent; no sim repair; carry-over",
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code A tight fair py-only (Opus 4.8 vector)",
        root=Path("runs/table1_v3_fair/claude_opus48_tight_fair"),
        note=(
            "Table 1 v3 fair baseline: vector Anthropic-compatible Opus 4.8 route; "
            "empty scratch; empty MCP; Write/Bash tools only; harness derive; "
            "rewrite repair<=3 via LLM_ONLY claude-opus-4-8; no KB/patch_only."
        ),
        tools_budget="Claude Code tight; rewrite repair<=3; retry=2; max_tokens=12000",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="Claude Code B open native py-only (local GLM-5.1 codingplan)",
        root=Path("runs/authoring90_native_agents/claude_opus48_native_open_v1"),
        note="B: product default tools; empty scratch; empty MCP; no LabscriptAI sim/MCP; outer harness derives and simulates.",
        tools_budget="Native agent open; no sim repair; carry-over",
        panel_expected=True,
    ),
    TableRow(
        task_set="Main 90",
        row_class="Native agent",
        row_label="OpenClaw native agent py-only",
        root=Path("runs/authoring90_native_agents/openclaw_py_only_v1"),
        note="OpenClaw row is populated only when openclaw is installed and run.",
        tools_budget="Native agent; py-only",
    ),
    TableRow(
        task_set="External 66",
        row_class="LLM-only",
        row_label="DeepSeek LLM-only py-only",
        root=Path("runs/table1_v2_external66_llm_only_py_official_deepseek"),
        tools_budget="LLM-only; external 66",
    ),
    TableRow(
        task_set="External 66",
        row_class="LabscriptAI agent",
        row_label="Agent unified py-only",
        root=Path("runs/table1_v2_external66_unified_py_official_deepseek_pure"),
        tools_budget="KB + repair; external 66",
    ),
)

PANEL_TASK_COUNT = 30
API_FAIL_RATE_THRESHOLD = 0.05
OUTPUT_PATH = Path("runs/table1_v3_fair/table1_v3_summary.md")
TABLE1_LIST_PRICE_USD_PER_M = {
    # DeepSeek official list price as of 2026-06-15 (cache-miss input).
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    # VectorEngine / OpenAI-compatible list prices used in Table 1 Pareto plots (Jun 2026).
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-5.5": {"input": 5.0, "output": 30.0},
    "claude-opus-4-8": {"input": 5.0, "output": 25.0},
    "gemini-3.5-flash": {"input": 1.5, "output": 9.0},
}
# Back-compat alias for tests/docs that still mention DeepSeek-only pricing.
DEEPSEEK_OFFICIAL_PRICING_USD_PER_M = TABLE1_LIST_PRICE_USD_PER_M
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


def _fmt_usd(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"${value:.4f}"


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


def _api_fail_exclusion_reason(summary: dict[str, Any], total: int) -> str | None:
    if not summary:
        return "missing summary"
    if total <= 0:
        return "missing task count"
    provider_events = _as_int(summary.get("provider_error_count"))
    final_provider_failures = _final_provider_error_count(summary)
    provider_rate = provider_events / total
    final_rate = final_provider_failures / total
    reasons: list[str] = []
    if provider_rate > API_FAIL_RATE_THRESHOLD:
        reasons.append(f"provider_error_count={provider_events}/{total}")
    if final_rate > API_FAIL_RATE_THRESHOLD:
        reasons.append(f"final_api_fail={final_provider_failures}/{total}")
    return "; ".join(reasons) if reasons else None


def _cost_usd(summary: dict[str, Any], cost_model: str) -> float | None:
    pricing = TABLE1_LIST_PRICE_USD_PER_M.get(cost_model)
    if not summary or not pricing:
        return None
    input_tokens = _as_int(summary.get("input_tokens"))
    output_tokens = _as_int(summary.get("output_tokens"))
    if input_tokens <= 0 and output_tokens <= 0:
        return None
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


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
    if not review and not (panel_expected and panel_expert is not None):
        parts.append("expert_missing")
    if panel_expected and panel_expert is None:
        parts.append("expert_panel_missing")
    return "; ".join(parts)


def build_table(rows: tuple[TableRow, ...] = ROWS) -> str:
    lines = [
        "# Table 1 v3 fair benchmark summary",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "All rows use the py-only benchmark contract: the model writes `protocol.py`; "
        "benchmark tooling derives `manifest.json` and `setup_card.html` from that "
        "protocol before validation and simulation.",
        "",
        "Main-table gate: rows with `provider_error_count` or final API failures above "
        "5% of N are excluded from the main table and listed under Excluded evidence.",
        "",
        "Cost: DeepSeek rows use the official DeepSeek per-1M token list price "
        "(input cache-miss + output; source: https://api-docs.deepseek.com/quick_start/pricing). "
        "GPT-4 / frontier rows use the same VectorEngine list-price table as "
        "`scripts/plot_table1_pareto_pretty.py` (Jun 2026). "
        "Rows without a public or run-logged price show `NA`.",
        "",
        "Expert panel: n=30 stratified tasks; blind LLM reviewers (DeepSeek-V4-Pro, GPT-5.4, Gemini-3-Flash primary with Gemini-3.5-Flash fallback when required); DeepSeek via official API, GPT/Gemini via VectorEngine; scores final package only, no authoring trace; table value = mean of three reviewers.",
        "",
        "| Set | Class | Row | Tools/budget | N | FP | FinalPass | Expert | Tok/task | $/task | Provider events | Final API fail | Status |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    detail_lines = ["", "Detailed evidence:", ""]
    excluded_rows: list[str] = []
    for row in rows:
        summary = _load_optional(row.root / "summary.json")
        analysis = _load_optional(row.root / "analysis" / "attribution-summary.json")
        review = _load_optional(row.root / "expert_review" / "review-summary.json")
        panel_expert = _panel_expert_mean(row.root) if row.panel_expected else None
        total = _total(summary, analysis)
        fp = _first_pass_count(summary, analysis, total)
        final_pass = int(analysis.get("task_pass_count", 0)) if analysis else None
        expert = review.get("mean_scores", {}).get("expert_score_mean")
        expert_display = panel_expert if panel_expert is not None else expert
        tokens = int(summary.get("total_tokens", 0))
        tokens_per_task = f"{tokens / total:.0f}" if total else "NA"
        cost = _cost_usd(summary, row.cost_model)
        cost_per_task = (cost / total) if cost is not None and total else None
        provider_events = int(summary.get("provider_error_count", 0))
        final_provider_failures = _final_provider_error_count(summary)
        status = _status(
            summary,
            analysis,
            review,
            panel_expected=row.panel_expected,
            panel_expert=panel_expert,
        )
        exclusion_reason = _api_fail_exclusion_reason(summary, total)
        if exclusion_reason is None:
            lines.append(
                "| {task_set} | {row_class} | {row_label} | {tools_budget} | {total} | {fp} | {final_pass} | {expert} | {tokens_per_task} | {cost_per_task} | {provider_events} | {final_provider_failures} | {status} |".format(
                    task_set=row.task_set,
                    row_class=row.row_class,
                    row_label=row.row_label,
                    tools_budget=row.tools_budget or row.row_class,
                    total=total or "NA",
                    fp=_fmt_count(fp, total),
                    final_pass=_fmt_count(final_pass, total),
                    expert=_fmt_expert(expert_display),
                    tokens_per_task=tokens_per_task,
                    cost_per_task=_fmt_usd(cost_per_task),
                    provider_events=provider_events,
                    final_provider_failures=final_provider_failures,
                    status=status,
                )
            )
        else:
            excluded_rows.append(
                "| {task_set} | {row_class} | {row_label} | {total} | {reason} | {root} |".format(
                    task_set=row.task_set,
                    row_class=row.row_class,
                    row_label=row.row_label,
                    total=total or "NA",
                    reason=exclusion_reason,
                    root=f"`{row.root}`",
                )
            )
        note = f"; {row.note}" if row.note else ""
        panel_note = f"; panel={_panel_status(row.root)}" if row.panel_expected else ""
        detail_lines.append(
            f"- {row.task_set} {row.row_label}: `{row.root}`{note}{panel_note}"
        )
    if excluded_rows:
        excluded_lines = [
            "",
            "Excluded evidence:",
            "",
            "| Set | Class | Row | N | Reason | Root |",
            "| --- | --- | --- | ---: | --- | --- |",
            *excluded_rows,
        ]
    else:
        excluded_lines = ["", "Excluded evidence:", "", "- None"]
    smoke = Path("runs/table1_v2_historical_derive_smoke/summary.json")
    if smoke.exists():
        payload = _load(smoke)
        detail_lines.append(
            "- Historical derive smoke: `runs/table1_v2_historical_derive_smoke` "
            f"({payload.get('package_complete_count', 0)}/{payload.get('task_count', 0)} package-complete)"
        )
    lines.extend(excluded_lines)
    lines.extend(detail_lines)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    out = OUTPUT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_table(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
