#!/usr/bin/env python3
"""Build Table 1 v3 robustness evidence from completed authoring runs."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Any


TASK_COUNT = 90
DEFAULT_FLASH_SEEDS = ("flash_seed01", "flash_seed02", "flash_seed03")


@dataclass(frozen=True)
class RunData:
    label: str
    root: Path
    summary: dict[str, Any]
    analysis: dict[str, Any]

    @property
    def task_count(self) -> int:
        return int(self.analysis.get("task_count") or self.summary.get("task_count") or 0)

    @property
    def final_pass_count(self) -> int:
        return int(self.analysis.get("task_pass_count", 0))

    @property
    def simulation_pass_count(self) -> int:
        return int(self.summary.get("simulation_pass_count", self.analysis.get("simulation_pass_count", 0)) or 0)

    @property
    def provider_error_count(self) -> int:
        return int(self.summary.get("provider_error_count", 0) or 0)

    @property
    def final_provider_fail_count(self) -> int:
        return _final_provider_error_count(self.summary)

    @property
    def total_tokens(self) -> int:
        return int(self.summary.get("total_tokens", 0) or 0)

    @property
    def tokens_per_task(self) -> float:
        return self.total_tokens / self.task_count if self.task_count else 0.0

    @property
    def eligible_for_main_table(self) -> bool:
        if self.task_count <= 0:
            return False
        provider_rate = self.provider_error_count / self.task_count
        final_fail_rate = self.final_provider_fail_count / self.task_count
        return provider_rate <= 0.05 and final_fail_rate <= 0.05


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_run(label: str, root: Path) -> RunData:
    return RunData(
        label=label,
        root=root,
        summary=_load_optional_json(root / "summary.json"),
        analysis=_load_optional_json(root / "analysis" / "attribution-summary.json"),
    )


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


def _task_pass_map(run: RunData) -> dict[str, bool]:
    rows = run.analysis.get("per_task", [])
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("task_id")): bool(row.get("task_pass"))
        for row in rows
        if isinstance(row, dict) and row.get("task_id")
    }


def _first_pass_composite_count(run: RunData) -> int:
    gen_by_task = {
        str(record.get("task_id")): _as_int(record.get("generation_attempts"))
        for record in run.summary.get("records", [])
        if isinstance(record, dict) and record.get("task_id")
    }
    count = 0
    for row in run.analysis.get("per_task", []):
        if not isinstance(row, dict):
            continue
        task_id = str(row.get("task_id"))
        if gen_by_task.get(task_id, 1) != 1:
            continue
        if _as_int(row.get("simulation_repair_attempts")) != 0:
            continue
        if row.get("first_pass_simulation_ok") and row.get("task_pass"):
            count += 1
    return count


def _format_count_rate(count: int, total: int) -> str:
    if total <= 0:
        return "NA"
    return f"{count}/{total} ({count / total:.1%})"


def _ci95(values: list[float]) -> tuple[float, float, float] | None:
    if not values:
        return None
    center = mean(values)
    if len(values) == 1:
        return center, center, center
    t_crit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(len(values), 1.96)
    half_width = t_crit * stdev(values) / math.sqrt(len(values))
    return center, center - half_width, center + half_width


def _mcnemar_exact(a: dict[str, bool], b: dict[str, bool]) -> dict[str, Any]:
    common = sorted(set(a) & set(b))
    a_only = sum(1 for task_id in common if a[task_id] and not b[task_id])
    b_only = sum(1 for task_id in common if b[task_id] and not a[task_id])
    both_pass = sum(1 for task_id in common if a[task_id] and b[task_id])
    both_fail = sum(1 for task_id in common if not a[task_id] and not b[task_id])
    discordant = a_only + b_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = min(a_only, b_only)
        prob = sum(math.comb(discordant, i) for i in range(tail + 1)) / (2**discordant)
        p_value = min(1.0, 2.0 * prob)
    return {
        "paired_tasks": len(common),
        "a_only": a_only,
        "b_only": b_only,
        "both_pass": both_pass,
        "both_fail": both_fail,
        "p_value": p_value,
    }


def _load_holdout_ids(path: Path) -> set[str]:
    payload = _load_optional_json(path)
    ids = payload.get("holdout_task_ids", [])
    return {str(task_id) for task_id in ids if isinstance(task_id, str)}


def _group_ids(holdout_ids: set[str]) -> dict[str, set[str]]:
    legacy = {f"T{i:03d}" for i in range(1, 56)}
    new = {f"T{i:03d}" for i in range(56, 91)}
    return {
        "Legacy T001-T055": legacy,
        "New T056-T090": new,
        "Holdout 30": holdout_ids,
    }


def _group_count(pass_map: dict[str, bool], ids: set[str]) -> tuple[int, int]:
    common = sorted(set(pass_map) & ids)
    return sum(1 for task_id in common if pass_map[task_id]), len(common)


def _majority_map(runs: list[RunData]) -> dict[str, bool]:
    maps = [_task_pass_map(run) for run in runs]
    task_ids = sorted(set().union(*(set(item) for item in maps))) if maps else []
    threshold = math.ceil(len(maps) / 2)
    return {
        task_id: sum(1 for item in maps if item.get(task_id, False)) >= threshold
        for task_id in task_ids
    }


def _run_status(run: RunData) -> str:
    if run.task_count == 0:
        return "missing"
    flags: list[str] = []
    provider_rate = run.provider_error_count / run.task_count
    final_fail_rate = run.final_provider_fail_count / run.task_count
    if provider_rate > 0.05:
        flags.append(f"provider_error>{provider_rate:.1%}")
    if final_fail_rate > 0.05:
        flags.append(f"final_api_fail>{final_fail_rate:.1%}")
    return "eligible" if not flags else "exclude: " + ", ".join(flags)


def build_report(
    *,
    root: Path,
    flash_seed_names: tuple[str, ...],
    codex_fair: Path,
    deepseek_direct: Path,
    holdout_manifest: Path,
) -> str:
    flash_runs = [_load_run(name, root / name) for name in flash_seed_names]
    present_flash_runs = [run for run in flash_runs if run.task_count > 0]
    eligible_flash_runs = [run for run in present_flash_runs if run.eligible_for_main_table]
    codex_run = _load_run("codex_gpt55_fair", codex_fair)
    direct_run = _load_run("deepseek_direct", deepseek_direct)
    holdout_ids = _load_holdout_ids(holdout_manifest)
    groups = _group_ids(holdout_ids)

    lines = [
        "# Table 1 v3 robustness report",
        "",
        "Scope: py-only authoring runs. FinalPass means the composite `task_pass` from `analyze_authoring_run`.",
        "Runs with provider errors or final API failures above 5% are flagged out of the main table.",
        "",
        "## Run eligibility",
        "",
        "| Run | Tasks | FinalPass | FP composite | SimPass | Tokens/task | Provider errors | Final API fail | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for run in [*flash_runs, codex_run, direct_run]:
        lines.append(
            "| {label} | {tasks} | {final} | {fp} | {sim} | {tok:.0f} | {provider} | {final_fail} | {status} |".format(
                label=run.label,
                tasks=run.task_count or "NA",
                final=_format_count_rate(run.final_pass_count, run.task_count),
                fp=_format_count_rate(_first_pass_composite_count(run), run.task_count),
                sim=_format_count_rate(run.simulation_pass_count, run.task_count),
                tok=run.tokens_per_task,
                provider=run.provider_error_count,
                final_fail=run.final_provider_fail_count,
                status=_run_status(run),
            )
        )

    lines.extend(["", "## Flash 3-seed FinalPass", ""])
    flash_counts = [run.final_pass_count for run in eligible_flash_runs]
    if flash_counts:
        ci = _ci95([float(value) for value in flash_counts])
        assert ci is not None
        center, low, high = ci
        lines.append(
            f"- Eligible seeds: {len(flash_counts)}/{len(flash_runs)}; FinalPass mean = "
            f"{center:.2f}/90, 95% CI = [{low:.2f}, {high:.2f}]."
        )
        rates = [value / TASK_COUNT for value in flash_counts]
        rate_ci = _ci95(rates)
        if rate_ci is not None:
            r_center, r_low, r_high = rate_ci
            lines.append(
                f"- Rate mean = {r_center:.1%}, 95% CI = [{r_low:.1%}, {r_high:.1%}]."
            )
    else:
        lines.append("- No eligible Flash seed runs found yet.")

    lines.extend(["", "## McNemar paired tests", ""])
    if eligible_flash_runs:
        flash_map = _majority_map(eligible_flash_runs) if len(eligible_flash_runs) > 1 else _task_pass_map(eligible_flash_runs[0])
        flash_label = "Flash majority" if len(eligible_flash_runs) > 1 else eligible_flash_runs[0].label
        for other in [codex_run, direct_run]:
            if not other.eligible_for_main_table:
                lines.append(f"- {flash_label} vs {other.label}: skipped ({_run_status(other)}).")
                continue
            other_map = _task_pass_map(other)
            if not flash_map or not other_map:
                lines.append(f"- {flash_label} vs {other.label}: missing paired data.")
                continue
            stat = _mcnemar_exact(flash_map, other_map)
            lines.append(
                "- {flash} vs {other}: paired n={n}, Flash-only={a_only}, other-only={b_only}, "
                "both-pass={both_pass}, both-fail={both_fail}, exact p={p:.4g}.".format(
                    flash=flash_label,
                    other=other.label,
                    n=stat["paired_tasks"],
                    a_only=stat["a_only"],
                    b_only=stat["b_only"],
                    both_pass=stat["both_pass"],
                    both_fail=stat["both_fail"],
                    p=stat["p_value"],
                )
            )
    else:
        lines.append("- No Flash runs available for paired tests yet.")

    lines.extend(["", "## Stratified FinalPass", ""])
    strat_runs: list[tuple[str, dict[str, bool]]] = []
    for run in flash_runs:
        if run.task_count and run.eligible_for_main_table:
            strat_runs.append((run.label, _task_pass_map(run)))
    if len(eligible_flash_runs) > 1:
        strat_runs.append(("flash_majority", _majority_map(eligible_flash_runs)))
    skipped_stratified = [
        run
        for run in [*flash_runs, codex_run, direct_run]
        if run.task_count and not run.eligible_for_main_table
    ]
    if skipped_stratified:
        lines.append(
            "- Skipped excluded runs: "
            + ", ".join(f"{run.label} ({_run_status(run)})" for run in skipped_stratified)
            + "."
        )
    for run in [codex_run, direct_run]:
        if run.task_count and run.eligible_for_main_table:
            strat_runs.append((run.label, _task_pass_map(run)))
    if not strat_runs:
        lines.append("- No stratified data available yet.")
    else:
        lines.extend(
            [
                "| Run | Legacy T001-T055 | New T056-T090 | Holdout 30 |",
                "|---|---:|---:|---:|",
            ]
        )
        for label, pass_map in strat_runs:
            values = []
            for ids in groups.values():
                count, total = _group_count(pass_map, ids)
                values.append(_format_count_rate(count, total))
            lines.append(f"| {label} | {values[0]} | {values[1]} | {values[2]} |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("runs/table1_v3_fair"))
    parser.add_argument("--flash-seeds", default=",".join(DEFAULT_FLASH_SEEDS))
    parser.add_argument("--codex-fair", type=Path, default=Path("runs/table1_v3_fair/codex_gpt55_fair"))
    parser.add_argument(
        "--deepseek-direct",
        type=Path,
        default=Path("runs/table1_v2_llm_only_py90_official_deepseek_final"),
    )
    parser.add_argument(
        "--holdout-manifest",
        type=Path,
        default=Path("benchmarks/authoring/holdout_manifest.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("runs/table1_v3_fair/robustness_report.md"))
    args = parser.parse_args()

    flash_seed_names = tuple(name.strip() for name in args.flash_seeds.split(",") if name.strip())
    report = build_report(
        root=args.root,
        flash_seed_names=flash_seed_names,
        codex_fair=args.codex_fair,
        deepseek_direct=args.deepseek_direct,
        holdout_manifest=args.holdout_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
