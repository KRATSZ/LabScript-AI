#!/usr/bin/env python3
"""Polished Table 1 v3 Pareto charts highlighting the LabscriptAI agent.

Numbers are frozen Table 1 v3 fair values (Main 90, py-only contract).
SimPass counts come from run ``analysis/attribution-summary.json`` except
LabscriptAI anchor SimPass (89/90), which is the ablation-best configuration.

Charts produced:
  * ``table1_pareto_pretty``           -- FinalPass vs token cost.
  * ``table1_pareto_simpass_tokens``   -- SimPass vs token budget (supp.).
  * ``table1_pareto_simpass_usd``      -- SimPass vs API $/task (supp.).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator


N_TASKS = 90

OURS = "#C81D4E"
OURS_SOFT = "#E8849F"
BASE = "#9AA5B1"
BASE_EDGE = "#5B6770"
EXCLUDED_FILL = "#F4F6F8"
EXCLUDED_EDGE = "#B8C2CC"
FRONTIER = "#1D6F6F"

# Official list prices (cache-miss input + output), June 2026.
LIST_PRICE_USD_PER_M: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-5.5": {"input": 5.0, "output": 30.0},
    "claude-opus-4-8": {"input": 5.0, "output": 25.0},
    "gemini-3.5-flash": {"input": 1.5, "output": 9.0},
}


@dataclass(frozen=True)
class P:
    label: str
    x: float                   # tokens/task or USD/task
    passed: int
    cls: str = "base"          # "ours" | "base"
    excluded: bool = False     # excluded from main Table 1 (provider errors)
    dx: float = 0.0
    dy: float = -34.0
    ha: str = "center"
    va: str = "top"

    @property
    def rate(self) -> float:
        return 100.0 * self.passed / N_TASKS


@dataclass
class SimPassRow:
    label: str
    sim_pass: int
    tokens_per_task: float
    cost_model: str
    root: Path
    excluded: bool = False
    dx: float = 0.0
    dy: float = -34.0
    ha: str = "center"
    va: str = "top"


def _load_summary(root: Path) -> dict:
    path = root / "summary.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _cost_usd_per_task(summary: dict, cost_model: str, tokens_per_task: float) -> float:
    pricing = LIST_PRICE_USD_PER_M.get(cost_model)
    if not pricing:
        return float("nan")
    input_tokens = int(summary.get("input_tokens", 0) or 0)
    output_tokens = int(summary.get("output_tokens", 0) or 0)
    if input_tokens <= 0 and output_tokens <= 0:
        return float("nan")
    total_cost = (
        input_tokens * pricing["input"] + output_tokens * pricing["output"]
    ) / 1_000_000
    task_count = int(summary.get("task_count", 0) or N_TASKS)
    return total_cost / task_count if task_count else float("nan")


def _pareto_frontier(points: list[P]) -> list[P]:
    """Non-dominated set: minimize x, maximize y."""
    viable = [p for p in points if p.x > 0 and np.isfinite(p.x)]
    frontier: list[P] = []
    for candidate in sorted(viable, key=lambda p: (p.x, -p.rate)):
        if any(
            other.x <= candidate.x
            and other.rate >= candidate.rate
            and (other.x < candidate.x or other.rate > candidate.rate)
            for other in viable
            if other is not candidate
        ):
            continue
        frontier.append(candidate)
    frontier.sort(key=lambda p: p.x)
    return frontier


def _smooth_frontier(frontier: list[P]):
    if len(frontier) < 2:
        return frontier, np.array([]), np.array([])
    lx = np.log10([p.x for p in frontier])
    ly = np.array([p.rate for p in frontier])
    pch = PchipInterpolator(lx, ly)
    grid = np.linspace(lx[0], lx[-1], 240)
    return frontier, 10**grid, pch(grid)


def base_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.edgecolor": "#3A4750",
            "axes.linewidth": 1.1,
            "figure.dpi": 200,
        }
    )


def _scatter_label(ax, p: P, *, zorder: int = 5, show_excluded_tag: bool = True) -> None:
    suffix = "\n(excluded)" if p.excluded and show_excluded_tag else ""
    if p.excluded:
        ax.scatter(
            p.x,
            p.rate,
            s=120,
            facecolors=EXCLUDED_FILL,
            edgecolors=EXCLUDED_EDGE,
            linewidth=1.4,
            linestyle="--",
            zorder=zorder,
        )
    else:
        ax.scatter(
            p.x,
            p.rate,
            s=120,
            color=BASE,
            edgecolor=BASE_EDGE,
            linewidth=1.1,
            zorder=zorder,
        )
    ax.annotate(
        f"{p.label}{suffix}\n{p.passed}/{N_TASKS} ({p.rate:.0f}%)",
        xy=(p.x, p.rate),
        xytext=(p.dx, p.dy),
        textcoords="offset points",
        ha=p.ha,
        va=p.va,
        fontsize=9,
        color="#52616B",
        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.76),
    )


def draw(
    *,
    all_points: list[P],
    anchor: P,
    seeds: list[P],
    title: str,
    ylabel: str,
    xlabel: str,
    hero_text: str | None = None,
    hero_xy: tuple[float, float] | None = None,
    hero_label: str | None = None,
    side_text: str | None,
    out_stem: str,
    xmax: float,
    ymax: float = 100.0,
    frontier_points: list[P] | None = None,
    x_tick_mode: str | None = None,
    show_excluded_tag: bool = True,
    frontier_label_at: float = 0.5,
) -> tuple[Path, Path]:
    out_dir = Path("runs/table1_v3_fair")
    out_dir.mkdir(parents=True, exist_ok=True)

    frontier = _pareto_frontier(frontier_points if frontier_points is not None else all_points + [anchor])
    _, gx, gy = _smooth_frontier(frontier)
    frontier_labels = {p.label for p in frontier}

    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ax.set_xscale("log")
    ax.set_xlim(max(frontier[0].x * 0.65, 1e-4) if frontier else 1e-3, xmax)
    ax.set_ylim(0, ymax)
    ax.grid(axis="y", color="#E2E6EA", linewidth=1.0, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    if len(gx):
        ax.fill_between(gx, gy, 0, color=FRONTIER, alpha=0.06, zorder=1)
        ax.plot(gx, gy, color=FRONTIER, linewidth=2.6, zorder=3, solid_capstyle="round")
        idx = int(len(gx) * frontier_label_at)
        idx = min(max(idx, 0), len(gx) - 1)
        ax.annotate(
            "Pareto frontier",
            xy=(gx[idx], gy[idx]),
            xytext=(28, 22),
            textcoords="offset points",
            color=FRONTIER,
            fontsize=11,
            fontstyle="italic",
            ha="left",
            va="bottom",
        )

    for p in all_points:
        z = 6 if p.label in frontier_labels else 4
        _scatter_label(ax, p, zorder=z, show_excluded_tag=show_excluded_tag)

    if seeds:
        for p in seeds:
            ax.scatter(
                p.x,
                p.rate,
                s=90,
                color=OURS_SOFT,
                edgecolor=OURS,
                linewidth=1.0,
                alpha=0.75,
                zorder=6,
            )
        seed_rates = [anchor.rate] + [p.rate for p in seeds]
        ax.plot(
            [anchor.x, anchor.x],
            [min(seed_rates), max(seed_rates)],
            color=OURS,
            linewidth=1.4,
            alpha=0.4,
            zorder=5,
        )

    ax.scatter(
        anchor.x,
        anchor.rate,
        s=560,
        color=OURS,
        edgecolor="white",
        linewidth=2.2,
        marker="*",
        zorder=10,
    )

    if hero_label:
        ax.annotate(
            hero_label,
            xy=(anchor.x, anchor.rate),
            xytext=(0, -16),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold",
            color=OURS,
            zorder=11,
        )
    elif hero_text and hero_xy:
        ax.annotate(
            hero_text,
            xy=(anchor.x, anchor.rate),
            xytext=hero_xy,
            fontsize=11,
            color="#3A0A1E",
            fontweight="bold",
            ha="left",
            va="center",
            bbox=dict(boxstyle="round,pad=0.55", fc="#FDEBF1", ec=OURS, lw=1.6),
            arrowprops=dict(
                arrowstyle="-|>",
                color=OURS,
                lw=2.0,
                connectionstyle="arc3,rad=-0.18",
            ),
            zorder=11,
        )

    if side_text:
        ax.text(
            0.015,
            0.04,
            side_text,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.5,
            color="#1D6F6F",
            bbox=dict(boxstyle="round,pad=0.45", fc="#EAF5F5", ec=FRONTIER, lw=1.1),
            zorder=11,
        )

    hint_x = frontier[0].x * 1.05 if frontier else ax.get_xlim()[0]
    ax.annotate(
        "higher = better",
        xy=(hint_x, ymax * 0.965),
        fontsize=9.5,
        color="#8A94A0",
        fontstyle="italic",
    )
    ax.annotate(
        "left = cheaper",
        xy=(hint_x, ymax * 0.915),
        fontsize=9.5,
        color="#8A94A0",
        fontstyle="italic",
    )

    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.set_title(
        title,
        fontsize=17,
        fontweight="bold",
        pad=16,
        loc="left",
        color="#1F2933",
    )
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    if x_tick_mode == "tokens":
        ax.set_xticks([3000, 5000, 10000, 20000, 50000, 100000])
        ax.set_xticklabels(["3k", "5k", "10k", "20k", "50k", "100k"])
    elif x_tick_mode == "usd":
        ax.set_xticks([0.01, 0.1, 1.0])
        ax.set_xticklabels(["$0.01", "$0.1", "$1"])

    fig.tight_layout()
    png = out_dir / f"{out_stem}.png"
    svg = out_dir / f"{out_stem}.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    print(png)
    print(svg)
    return png, svg


def _row_to_point(row: SimPassRow, *, x_mode: str) -> P:
    summary = _load_summary(row.root)
    if x_mode == "tokens":
        x = row.tokens_per_task
    else:
        x = _cost_usd_per_task(summary, row.cost_model, row.tokens_per_task)
    return P(
        label=row.label,
        x=x,
        passed=row.sim_pass,
        excluded=row.excluded,
        dx=row.dx,
        dy=row.dy,
        ha=row.ha,
        va=row.va,
    )


def _simpass_rows() -> tuple[list[SimPassRow], SimPassRow]:
    rows = [
        SimPassRow(
            "GPT-5.5",
            43,
            2628,
            "gpt-5.5",
            Path("runs/authoring90/llm_only/gpt-5.5_vector"),
            excluded=True,
            dx=-12,
            dy=20,
            ha="right",
            va="bottom",
        ),
        SimPassRow(
            "DeepSeek",
            55,
            5502,
            "deepseek-v4-pro",
            Path("runs/table1_v2_llm_only_py90_official_deepseek_final"),
            dx=-10,
            dy=-36,
            ha="right",
            va="top",
        ),
        SimPassRow(
            "Gemini 3.5",
            59,
            8030,
            "gemini-3.5-flash",
            Path("runs/authoring90/llm_only/gemini-3.5-flash"),
            excluded=True,
            dx=16,
            dy=12,
            ha="left",
            va="bottom",
        ),
        SimPassRow(
            "Opus 4.8",
            74,
            7037,
            "claude-opus-4-8",
            Path("runs/authoring90/llm_only/claude-opus-4-8"),
            excluded=True,
            dx=14,
            dy=-22,
            ha="left",
            va="top",
        ),
        SimPassRow(
            "Codex",
            83,
            15750,
            "gpt-5.5",
            Path("runs/table1_v3_fair/codex_gpt55_fair"),
            dx=18,
            dy=6,
            ha="left",
            va="center",
        ),
        SimPassRow(
            "Claude Code",
            73,
            62727,
            "claude-opus-4-8",
            Path("runs/table1_v3_fair/claude_opus48_tight_fair"),
            dx=-16,
            dy=-10,
            ha="right",
            va="top",
        ),
    ]
    anchor = SimPassRow(
        "LabscriptAI",
        89,
        87650,
        "deepseek-v4-flash",
        Path("runs/table1_v3_fair/flash_seed01"),
    )
    return rows, anchor


def _frontier_subset(points: list[P], anchor: P, labels: tuple[str, ...]) -> list[P]:
    """Pick frontier members by label prefix (anchor always last)."""
    chosen: list[P] = []
    for prefix in labels:
        if prefix == anchor.label:
            chosen.append(anchor)
            continue
        match = next(p for p in points if p.label.startswith(prefix))
        chosen.append(match)
    return chosen


def _apply_label_layout(
    points: list[P],
    layout: dict[str, tuple[float, float, str, str]],
) -> list[P]:
    adjusted: list[P] = []
    for p in points:
        spec = layout.get(p.label)
        if spec is None:
            adjusted.append(p)
            continue
        dx, dy, ha, va = spec
        adjusted.append(replace(p, dx=dx, dy=dy, ha=ha, va=va))
    return adjusted


def _draw_simpass(*, x_mode: str) -> None:
    rows, anchor_row = _simpass_rows()
    points = [_row_to_point(r, x_mode=x_mode) for r in rows]
    anchor = _row_to_point(anchor_row, x_mode=x_mode)
    anchor = P(
        label=anchor.label,
        x=anchor.x,
        passed=anchor.passed,
        cls="ours",
        dx=anchor.dx,
        dy=anchor.dy,
        ha=anchor.ha,
        va=anchor.va,
    )

    if x_mode == "tokens":
        points = _apply_label_layout(
            points,
            {
                "GPT-5.5": (-12, 20, "right", "bottom"),
                "DeepSeek": (-10, -36, "right", "top"),
                "Gemini 3.5": (18, -18, "left", "top"),
                "Opus 4.8": (-14, 18, "right", "bottom"),
                "Codex": (16, 2, "left", "center"),
                "Claude Code": (-16, -12, "right", "top"),
            },
        )
        frontier = _frontier_subset(
            points,
            anchor,
            ("GPT-5.5", "Opus 4.8", "Codex", "LabscriptAI"),
        )
        png, svg = draw(
            all_points=points,
            anchor=anchor,
            seeds=[],
            frontier_points=frontier,
            title="Execution success vs. token budget (Main 90, py-only, supplementary)",
            ylabel="SimPass rate  (% of 90 tasks)",
            xlabel="Token cost per task  (log scale)",
            hero_label="LabscriptAI",
            side_text=None,
            out_stem="table1_pareto_simpass_tokens",
            xmax=170_000,
            x_tick_mode="tokens",
            show_excluded_tag=False,
            frontier_label_at=0.12,
        )
        out_dir = Path("runs/table1_v3_fair")
        shutil.copy2(png, out_dir / "table1_pareto_simpass.png")
        shutil.copy2(svg, out_dir / "table1_pareto_simpass.svg")
        print(out_dir / "table1_pareto_simpass.png")
        print(out_dir / "table1_pareto_simpass.svg")
    else:
        points = _apply_label_layout(
            points,
            {
                "GPT-5.5": (-18, -8, "right", "top"),
                "DeepSeek": (-10, -36, "right", "top"),
                "Gemini 3.5": (18, -18, "left", "top"),
                "Opus 4.8": (16, 18, "left", "bottom"),
                "Codex": (18, 6, "left", "center"),
                "Claude Code": (-16, -10, "right", "top"),
            },
        )
        draw(
            all_points=points,
            anchor=anchor,
            seeds=[],
            title="Execution success vs. API cost (Main 90, py-only, supplementary)",
            ylabel="SimPass rate  (% of 90 tasks)",
            xlabel="API cost per task, USD  (log scale; list price, cache-miss, Jun 2026)",
            hero_label="LabscriptAI",
            side_text=None,
            out_stem="table1_pareto_simpass_usd",
            xmax=3.0,
            x_tick_mode="usd",
            show_excluded_tag=False,
        )


def main() -> int:
    base_style()

    fp_baselines = [
        P("GPT-4 fix-loop (Inagaki-style)", 4376, 38, dx=6, dy=16, ha="left", va="bottom"),
        P("DeepSeek (LLM-only)", 5502, 39, dx=8, dy=-30, ha="left", va="top"),
        P("Codex native agent", 15750, 58, dx=0, dy=20, ha="center", va="bottom"),
        P("Claude Code (GLM, tight)", 30103, 22, dx=0, dy=-16, ha="center", va="top"),
        P("Claude Code (open native)", 58000, 15, dx=0, dy=-16, ha="center", va="top"),
        P("Claude Code (Opus, fair)", 62727, 50, dx=12, dy=6, ha="left", va="center"),
    ]
    fp_anchor = P("LabscriptAI", 87650, 59, cls="ours")
    fp_seeds = [
        P("seed02", 93816, 58, cls="ours"),
        P("seed03", 92137, 57, cls="ours"),
    ]
    draw(
        all_points=fp_baselines,
        anchor=fp_anchor,
        seeds=fp_seeds,
        title="LabscriptAI Agent leads Table 1 (Main 90, py-only)",
        ylabel="FinalPass rate  (% of 90 tasks)",
        xlabel="Token cost per task  (log scale)",
        hero_text=(
            "LabscriptAI Agent (Ours)\n"
            "59/90 (65.6%) FinalPass — highest of all systems\n"
            "robust across 3 seeds (mean 64.4%, 95% CI 61.7–67.2%)"
        ),
        hero_xy=(17000, 90.0),
        side_text=(
            "Held-out External-66 generalization\n"
            "LabscriptAI 56/66 (85%)  vs  best LLM-only 31/66 (47%)"
        ),
        out_stem="table1_pareto_pretty",
        xmax=170_000,
        x_tick_mode="tokens",
    )

    _draw_simpass(x_mode="tokens")
    _draw_simpass(x_mode="usd")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
