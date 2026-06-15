# Workspace management

This page is for humans and AI agents working in a dirty repo. It explains what
to read, what to avoid, and where new files should go. It is not runtime policy;
runtime policy remains `docs/rules/`.

## First read

1. `AGENTS.md` for the short agent entry.
2. `docs/README.md` for doc priority.
3. `docs/REPO_LAYOUT.md` for code, benchmark, docs, and output folders.
4. `docs/rules/` only when the task touches live robot behavior, simulation
   gates, safety, or recovery.

## Current core map

| Area | Main paths | Use |
|------|------------|-----|
| Agent loop | `src/labscriptai/agent/loop.py`, `src/labscriptai/agent/registry.py`, `src/labscriptai/agent/state.py` | One tool-gated loop and shared state |
| Runtime chat | `src/labscriptai/runtime/unified_chat_bridge.py`, `src/labscriptai/runtime/cli.py` | Human-facing runtime conversation and TUI route |
| Authoring | `src/labscriptai/agent/facade.py`, `src/labscriptai/authoring/` | Protocol package generation |
| Benchmark runners | `src/labscriptai/benchmark/`, `scripts/run_*authoring*`, `scripts/build_table*` | Experiments and paper tables |
| Robot/MCP | `mcp-servers/opentrons-mcp/`, `skills/opentrons-robot-lan/` | MCP tools and explicit HTTP fallback |
| Operator skills | `skills/*/SKILL.md` | Scenario routing; link to rules instead of copying policy |

## Dirty workspace rule

Do not treat a dirty worktree as a blocker by itself. Classify files first:

| Class | Examples | Default action |
|-------|----------|----------------|
| Tracked source/docs/tests | `src/`, `tests/`, `docs/`, `AGENTS.md` | Read diff before editing; preserve user changes |
| Candidate source/test/script additions | new `src/labscriptai/...`, `tests/test_*.py`, maintained `scripts/*.py` | Keep visible in `git status`; do not ignore automatically |
| Benchmark task inputs | `benchmarks/**/*.yaml`, benchmark panel JSON | Treat as curated inputs; do not edit during active runs |
| Active run outputs | `runs/**`, shard logs, per-task packages | Read-only while a benchmark is running |
| Local scratch/output | `outputs/`, `backups/`, `protocol_data/`, `artifacts/local-run-logs/`, root checkpoint/log CSV files | Gitignored local material |

Never run `git reset --hard`, `git checkout --`, mass formatters, or cleanup
scripts just because the tree is noisy.

## Active benchmark no-touch check

Before changing benchmark code, scripts, or task files, check for running jobs:

```bash
ps -axo pid,ppid,lstart,command | rg -i "authoring90|benchmark|authoring_pilot|run_table1|run_authoring90|review_authoring|summarize_authoring|monitor_authoring"
```

If a job is running, treat these as read-only until the owner stops or finishes
the run:

- the run root under `runs/`;
- shard logs and per-task packages under that root;
- the exact runner script in the process command;
- `benchmarks/authoring/tasks.yaml` when the process uses it;
- protocol verification scripts used by active simulation commands.

Observed during this 2026-06-05 cleanup, active roots included:

- `runs/authoring90/inagaki_style/gpt-4-fixloop-v1`
- `runs/authoring90/llm_only/gpt-5_reference_v1`
- `runs/authoring90_native_agents/claude_opus48_pyonly_tight_v1_smoke_T001_T020_T056`

Refresh with `ps` before relying on this dated note.

## Table 1 anchor (2026-06-08)

- Combined summary: `runs/table1_v2_combined_summary.md` (regenerate via `PYTHONPATH=src python3 scripts/build_table1_v2.py`).
- LabscriptAI flash anchor row: `runs/authoring90/ablation5_20260529/flash/kb_v2_patch` (BoB 62/90, Sim 89/90).
- Superseded for Table 1 (keep as audit only): `runs/table1_v2_unified_py90_official_deepseek_pure` (58/90 BoB).

## Where new work goes

| New work | Put it here |
|----------|-------------|
| Runtime or agent implementation | `src/labscriptai/runtime/` or `src/labscriptai/agent/` |
| Protocol authoring logic | `src/labscriptai/authoring/` |
| Benchmark scoring/runners | `src/labscriptai/benchmark/` plus maintained `scripts/` |
| Unit tests | `tests/test_*.py` |
| Human/AI operating guidance | `AGENTS.md`, `docs/README.md`, `docs/REPO_LAYOUT.md`, or this page |
| Live robot procedure | `docs/rules/` only for binding policy; `docs/runbooks/` for procedure |
| Scratch scripts | `scripts/local/` unless they are meant to be maintained |
| Generated outputs | `runs/`, `artifacts/`, `outputs/`, `backups/`, or `protocol_data/` |

## Practical cleanup order

1. Protect active benchmark roots first.
2. Separate ignored local outputs from source/test/script candidates.
3. Keep benchmark rows, paper tables, and live robot changes in separate commits
   or review batches.
4. Run small tests before broader benchmark work.
5. Only move or rename scripts after no benchmark process depends on them.
