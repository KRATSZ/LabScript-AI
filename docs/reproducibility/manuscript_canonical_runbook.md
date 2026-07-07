# Manuscript canonical reproduction runbook

Canonical release: GitHub tag `v1.0-canonical` on [LabScript-AI](https://github.com/KRATSZ/LabScript-AI) (resolve exact hash with: `git rev-list -n 1 v1.0-canonical`), Zenodo [10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326).

This runbook reproduces manuscript **Table 1** and **Table 2** from the 90-task authoring benchmark (`benchmarks/authoring/tasks.yaml`). The canonical implementation is pure Python agent loops — **no LangGraph** — with `LabscriptAgentLoop` (authoring) and `RecoveryOrchestrator` + `RecoveryQueue` + Gatekeeper `evaluate_action` (runtime).

## 1. Clone and checkout

```bash
git clone https://github.com/KRATSZ/LabScript-AI
cd LabScript-AI
git checkout v1.0-canonical
# resolve exact commit hash with: git rev-list -n 1 v1.0-canonical
```

## 2. Install

**Python:** `>=3.10` (`pyproject.toml`; package name `opentrons-lab-agent`).

**Main project venv** (agent, benchmarks, tests):

```bash
uv venv .venv
uv sync
# optional extras as needed:
# uv sync --extra protocol   # opentrons pins for simulate
# uv sync --extra vision     # deck vision (not required for Tables 1–2)
```

**Dual-venv pattern for Opentrons simulation:** benchmark runners default to a separate protocol interpreter so the main agent venv stays lightweight. Create `.venv-protocol` with `opentrons==8.8.1` (see `[project.optional-dependencies] protocol` in `pyproject.toml`), then point runners at it:

```bash
uv venv .venv-protocol
uv pip install --python .venv-protocol/bin/python "opentrons==8.8.1"
export OPENTRONS_PYTHON="$PWD/.venv-protocol/bin/python"
```

Benchmark shells (`scripts/run_table1_v2_py_benchmark.sh`, native-agent runners) read `OPENTRONS_PYTHON` and default to `$REPO_ROOT/.venv-protocol/bin/python`.

### LLM stack (Methods vs benchmark backbone)

| Role | Model / service | Where used |
|------|-----------------|------------|
| **Table 1 / Table 2 authoring backbone** | `deepseek-v4-flash` | `scripts/run_table1_v2_py_benchmark.sh` unified mode; ablation rows under `runs/authoring90/ablation5_*` |
| **Production / Methods LLM operations** | Gemini 2.5 Pro via OpenRouter API | Web product and Methods description (`.paper/main0706.md` Online Methods) |
| **CODE_EXAMPLES retrieval** | Qwen3-Embedding-8B in Chroma DB | Knowledge-base RAG in unified authoring |

Table rebuild from cached artifacts does **not** call any LLM. Live re-runs require API keys (Section 5).

## 3. Benchmark tiers (N = 90)

| Tier | Count |
|------|------:|
| Easy | 15 |
| Medium | 39 |
| Hard | 29 |
| Expert | 7 |
| **Total** | **90** |

## 4. Metrics (Table 1 footnotes)

**SimPass:** fraction of tasks passing the platform-specific simulator (headline metric, comparable to ref. 9 and OpentronsAI).

**FinalPass:** stricter composite additionally requiring semantic-fidelity and parameter-sweep validation; identical validators applied to all systems, narrowing inter-system gaps.

**LLM reviewer (3×):** mean score (0–5) from three independent LLM-judge evaluations of semantic fidelity, reported for reference only and not used for pass/fail.

### Expected manuscript numbers

**Table 1** (SimPass / FinalPass out of 90):

| Class | System | SimPass | FinalPass |
|-------|--------|--------:|----------:|
| LabscriptAI | deepseek-v4-flash | 87/90 | 59/90 |
| Commercial | OpentronsAI | 69/90 | 51/90 |
| LLM | Claude Opus 4.8 | 74/90 | 54/90 |
| LLM | Gemini 3.5 Flash | 59/90 | 42/90 |
| LLM | DeepSeek v4-flash (direct) | 55/90 | 39/90 |
| LLM | GPT-5.5 | 43/90 | 36/90 |
| Coding agent | Codex (GPT-5.5) | 83/90 | 58/90 |
| Coding agent | Claude Code (Opus 4.8) | 73/90 | 50/90 |
| Literature | GPT-4 + fix-loop (Inagaki) | 59/90 | 38/90 |
| Human‡ | Domain expert | 2/2 | 2/2 |

**Table 2** (deepseek-v4-flash ablation; SimPass / FinalPass):

| Configuration | SimPass | FinalPass |
|---------------|--------:|----------:|
| Full (PRE+RAG+repair) | 87/90 | 59/90 |
| w/o Knowledge | 83/90 | 57/90 |
| w/ Rewrite repair | 84/90 | 60/90 |
| w/o Repair | 77/90 | 53/90 |
| Direct LLM | 43/90 | 30/90 |

## 5. Reproduce Tables **without** LLM calls (primary path)

Cached benchmark artifacts ship with the Zenodo record ([10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)). Extract them so the repository contains the frozen `runs/` tree expected by the table builders. The `runs/` directory is gitignored and is NOT included in the git tag — obtain it from the Zenodo shard bundle. Manuscript Table 1 and Table 2 both live under `runs/table1_v3_fair/` (Table 1 in `flash_seed01/`, Table 2 in `ablation_unified_flash/`; see row roots in `scripts/build_table1_v2.py`). If your bundle uses a different mount point, set:

```bash
export REPO_ROOT="$PWD"
# Shard root for the manuscript tables (Table 1 in flash_seed01/, Table 2 in ablation_unified_flash/):
# CACHED_RUNS_ROOT=runs/table1_v3_fair/
```

When the standard layout is present, `runs/` lives at the repo root (no extra env var required).

### 5.1 Rebuild Table 1 summary

`scripts/build_table1_v2.py` has no CLI flags; it aggregates `summary.json` and `analysis/attribution-summary.json` from each frozen row root and writes `runs/table1_v3_fair/table1_v3_summary.md`.

```bash
cd "$REPO_ROOT"
PYTHONPATH=src uv run python scripts/build_table1_v2.py
```

Inspect `runs/table1_v3_fair/table1_v3_summary.md`. The builder's **FinalPass** column (LabscriptAI 59/90) matches Table 1 FinalPass. Its **FP** column is first-pass-only simulation (stricter, LabscriptAI 54/90) and is **not** Table 1 SimPass — manuscript Table 1 **SimPass** (LabscriptAI 87/90) is the post-repair `simulation_pass_count` in `runs/table1_v3_fair/flash_seed01/analysis/attribution-summary.json`. Key LabscriptAI anchor row root: `runs/table1_v3_fair/flash_seed01`.

Optional — re-aggregate raw shards if you only have per-shard `record.json` trees and need fresh `summary.json` files:

```bash
PYTHONPATH=src uv run python scripts/summarize_authoring_shards.py runs/table1_v3_fair/flash_seed01
```

(`summarize_authoring_shards.py` accepts one `shard_root` positional argument; it scans `shard*/` subdirectories or flat `*/record.json` layouts.)

Optional — regenerate attribution analysis for a row (requires existing `summary.json`):

```bash
PYTHONPATH=src uv run python -m labscriptai.benchmark.analyze_authoring_run \
  runs/table1_v3_fair/flash_seed01/summary.json \
  --tasks benchmarks/authoring/tasks.yaml \
  --output-dir runs/table1_v3_fair/flash_seed01/analysis
```

### 5.2 Rebuild Table 2 ablation

Manuscript Table 2 is sourced from the `runs/table1_v3_fair/ablation_unified_flash/` ablation run, with the **Full** row taken from the Table 1 anchor `runs/table1_v3_fair/flash_seed01/` (same `deepseek-v4-flash` unified run). Each row's SimPass/FinalPass are pre-computed in its frozen `analysis/attribution-summary.json` (`simulation_pass_count` = SimPass, `task_pass_count` = FinalPass).

Manuscript row mapping (`deepseek-v4-flash`):

| Table 2 label | Frozen row root |
|---------------|-----------------|
| Full (PRE+RAG+repair) | `runs/table1_v3_fair/flash_seed01` |
| w/o Knowledge | `runs/table1_v3_fair/ablation_unified_flash/no_kb` |
| w/ Rewrite repair | `runs/table1_v3_fair/ablation_unified_flash/rewrite` |
| w/o Repair | `runs/table1_v3_fair/ablation_unified_flash/no_repair` |
| Direct LLM | `runs/table1_v3_fair/ablation_unified_flash/direct_llm` |

Extract the five rows from the frozen attribution files (no LLM, no re-run):

```bash
cd "$REPO_ROOT"
uv run python - <<'PY'
import json
from pathlib import Path
rows = {
    "Full (PRE+RAG+repair)": "runs/table1_v3_fair/flash_seed01",
    "w/o Knowledge": "runs/table1_v3_fair/ablation_unified_flash/no_kb",
    "w/ Rewrite repair": "runs/table1_v3_fair/ablation_unified_flash/rewrite",
    "w/o Repair": "runs/table1_v3_fair/ablation_unified_flash/no_repair",
    "Direct LLM": "runs/table1_v3_fair/ablation_unified_flash/direct_llm",
}
print(f"{'Configuration':26}{'SimPass':>8}  {'FinalPass':>8}  {'Tok/task':>9}")
for label, root in rows.items():
    r = Path(root)
    s = json.loads((r / "summary.json").read_text())
    a = json.loads((r / "analysis" / "attribution-summary.json").read_text())
    tc = s.get("task_count") or a.get("task_count") or 90
    tpt = s.get("total_tokens", 0) / tc
    print(f"{label:26}{a.get('simulation_pass_count')}/90  {a.get('task_pass_count')}/90  {tpt:>9.0f}")
PY
```

Expected output matches manuscript Table 2: SimPass Full 87/90 (96.7%), w/o Knowledge 83/90 (92.2%), w/ Rewrite repair 84/90 (93.3%), w/o Repair 77/90 (85.6%), Direct LLM 43/90 (47.8%); FinalPass 59/57/60/53/30; Tok/task 87,650 / 94,525 / 92,476 / 87,265 / 4,193.

Optional — regenerate a row's attribution analysis from its `summary.json`:

```bash
PYTHONPATH=src uv run python -m labscriptai.benchmark.analyze_authoring_run \
  runs/table1_v3_fair/ablation_unified_flash/no_kb/summary.json \
  --tasks benchmarks/authoring/tasks.yaml \
  --output-dir runs/table1_v3_fair/ablation_unified_flash/no_kb/analysis
```

> **Note on `scripts/build_authoring90_ablation5_report.py`.** That script targets a *separate, earlier* ablation run at `runs/authoring90/ablation5_20260529` (row layout `flash/{llm_direct,no_kb_patch,kb_v2_patch,kb_v2_rewrite,no_repair}`, plus a `pro/` model). Its `flash` numbers (e.g. `kb_v2_patch` 89/90, `no_repair` 82/90, `llm_direct` 41/90) do **not** match manuscript Table 2 and it is documented here only for completeness. The manuscript Table 2 is the `ablation_unified_flash` run above.

### 5.3 Verify tests (no LLM)

```bash
uv run python -m unittest discover -s tests -v
```

## 6. Full **live** re-run path

> **Requires user-provided API keys and budget; not executed in this release.**

Live runs invoke LLM providers and Opentrons simulation. Source `.env` in the repo root if present; `scripts/run_table1_v2_py_benchmark.sh` loads unset keys from `.env`.

### Environment variables read by benchmark scripts

| Variable | Used by | Purpose |
|----------|---------|---------|
| `DEEPSEEK_API_KEY` | `run_table1_v2_py_benchmark.sh` (`API_PREFIX=DEEPSEEK`) | Official DeepSeek API for unified / llm-only DeepSeek rows |
| `DEEPSEEK_BASE_URL` | same | API base (default `https://api.deepseek.com`) |
| `DEEPSEEK_MODEL` | same | Model id (e.g. `deepseek-v4-flash`) |
| `LLM_ONLY_API_KEY` | `run_authoring90_llm_only_parallel.sh`, native-agent repair, panel scripts | OpenAI-compatible gateway (VectorEngine) for frontier models |
| `LLM_ONLY_BASE_URL` | same | Gateway base URL |
| `LLM_ONLY_MODEL` | same | Per-run model id |
| `LLM_ONLY_MAX_TOKENS`, `LLM_ONLY_TIMEOUT_SEC`, `LLM_ONLY_RETRY_ATTEMPTS`, `LLM_ONLY_TRANSPORT_RETRIES` | same | Transport tuning |
| `OPENTRONS_PYTHON` | all simulate runners | Path to Opentrons-capable Python (default `.venv-protocol/bin/python`) |
| `API_PREFIX` | `run_table1_v2_py_benchmark.sh` | `DEEPSEEK` or `LLM_ONLY` |
| `TASKS` | benchmark shells | Task YAML (default `benchmarks/authoring/tasks.yaml`) |
| `SHARD_SIZE`, `PARALLEL`, `RESUME_TASKS`, `REQUIRE_PROVIDER_CLEAN`, `CLEAN_RERUNS` | `run_table1_v2_py_benchmark.sh` | Sharding and resume |
| `SIMULATION_REPAIR_ATTEMPTS` | benchmark shells | `0` llm-only / no-repair; `3` unified default |
| `REPAIR_EDIT_MODE` | benchmark shells | `patch_only` (unified) or `rewrite` (llm-only / rewrite ablation) |
| `UNIFIED_TOOL_PROFILE`, `UNIFIED_KB_CONTEXT_MODE` | unified mode | e.g. `UNIFIED_KB_CONTEXT_MODE=none` for w/o Knowledge ablation |
| `REPAIR_API_PREFIX`, `REPAIR_MODEL`, `REPAIR_MAX_TOKENS` | native-agent runners | Simulation repair model for Codex / Claude Code |

**Not referenced by these benchmark scripts:** `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY` (Claude Code uses the `claude` CLI; repair routes may set `ANTHROPIC_*` from `LLM_ONLY_*` inside `scripts/native_agent_baseline_common.py`).

### Table 1 live commands

```bash
# LabscriptAI unified (deepseek-v4-flash) — manuscript anchor
API_PREFIX=DEEPSEEK DEEPSEEK_MODEL=deepseek-v4-flash \
  scripts/run_table1_v2_py_benchmark.sh unified runs/table1_v3_fair/flash_seed01

# DeepSeek LLM-only direct
scripts/run_table1_v2_py_benchmark.sh llm-only runs/table1_v2_llm_only_py90_official_deepseek_final

# Frontier direct LLM (LLM_ONLY_* required)
scripts/run_authoring90_llm_only_parallel.sh gpt-5.5 runs/authoring90/llm_only/gpt-5.5_vector
scripts/run_authoring90_llm_only_parallel.sh gemini-3.5-flash runs/authoring90/llm_only/gemini-3.5-flash
scripts/run_authoring90_llm_only_parallel.sh claude-opus-4-8 runs/authoring90/llm_only/claude-opus-4-8

# Native coding agents
scripts/run_authoring90_codex_native_parallel.sh runs/table1_v3_fair/codex_gpt55_fair
scripts/run_authoring90_claude_opus48_parallel.sh runs/table1_v3_fair/claude_opus48_tight_fair tight
```

Each runner finishes by calling `scripts/summarize_authoring_shards.py` on its output root. Rebuild the manuscript table with Section 5.1.

### Table 2 live ablation (unified mode variants)

Use `scripts/run_table1_v2_py_benchmark.sh unified <output-root>` with overrides:

```bash
# w/o Knowledge
UNIFIED_KB_CONTEXT_MODE=none scripts/run_table1_v2_py_benchmark.sh unified runs/ablation/no_kb

# w/ Rewrite repair
REPAIR_EDIT_MODE=rewrite scripts/run_table1_v2_py_benchmark.sh unified runs/ablation/rewrite

# w/o Repair
SIMULATION_REPAIR_ATTEMPTS=0 scripts/run_table1_v2_py_benchmark.sh unified runs/ablation/no_repair

# Direct LLM (llm-only mode)
scripts/run_table1_v2_py_benchmark.sh llm-only runs/ablation/llm_direct
```

Then run `analyze_authoring_run` per output root and `build_authoring90_ablation5_report.py` on the parent directory layout from Section 5.2.

## 7. Related artifacts

- Freeze metadata: [`freeze_record.md`](freeze_record.md)
- GitHub release text: [`github_release_notes.md`](github_release_notes.md)
- Zenodo deposition draft: [`zenodo_metadata.json`](zenodo_metadata.json)
