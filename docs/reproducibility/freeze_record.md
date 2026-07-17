# Canonical manuscript freeze record

## Release identifiers

| Field | Value |
|-------|-------|
| Tag | `v1.0-canonical` |
| Commit | `v1.0-canonical` (resolve exact hash with: `git rev-list -n 1 v1.0-canonical`) |
| Freeze date | 2026-07-07 |
| GitHub | https://github.com/KRATSZ/LabScript-AI/tree/v1.0-canonical |
| Zenodo DOI | [10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326) |

## Implementation summary

| Layer | Component | Location |
|-------|-----------|----------|
| Authoring | `LabscriptAgentLoop` | `src/labscriptai/agent/loop.py` |
| Runtime recovery | `RecoveryOrchestrator` | `src/labscriptai/runtime/recovery_orchestrator.py` |
| Recovery queue | `RecoveryQueue` | `src/labscriptai/runtime/recovery_queue.py` |
| Safety gate | Gatekeeper `evaluate_action` | `src/labscriptai/runtime/gatekeeper.py` |
| FinalPass validator | semantic + param-sweep | `src/labscriptai/benchmark/semantic_validator.py` |

**Architecture:** pure Python control loops; **no LangGraph** in the canonical benchmark implementation.

**Benchmark tooling:**

- Runner: `scripts/run_table1_v2_py_benchmark.sh`
- Table 1 builder: `scripts/build_table1_v2.py` → `runs/table1_v3_fair/table1_v3_summary.md`
- Shard summarizer: `scripts/summarize_authoring_shards.py`
- Ablation report builder (separate `runs/authoring90/ablation5_20260529` run; manuscript Table 2 is sourced from `ablation_unified_flash`, see runbook §5.2): `scripts/build_authoring90_ablation5_report.py`
- Per-model runners: `scripts/run_authoring90_claude_opus48_parallel.sh`, `scripts/run_authoring90_codex_native_parallel.sh`, `scripts/run_codex_authoring_baseline.py`
- Shared native baseline: `scripts/native_agent_baseline_common.py`
- Analysis: `scripts/analyze_table1_robustness.py`, `scripts/build_s2a_external66_data.py`

## Frozen benchmark numbers

### Table 1 (SimPass / FinalPass, N = 90)

| System | SimPass | FinalPass |
|--------|--------:|----------:|
| LabscriptAI (deepseek-v4-flash) | 87/90 | 59/90 |
| OpentronsAI | 69/90 | 51/90 |
| Claude Opus 4.8 | 74/90 | 54/90 |
| Gemini 3.5 Flash | 59/90 | 42/90 |
| DeepSeek v4-flash direct | 55/90 | 39/90 |
| GPT-5.5 | 43/90 | 36/90 |
| Codex (GPT-5.5) | 83/90 | 58/90 |
| Claude Code (Opus 4.8) | 73/90 | 50/90 |
| GPT-4 + fix-loop (Inagaki) | 59/90 | 38/90 |
| Human (reference) | 2/2 | 2/2 |

### Table 2 (deepseek-v4-flash ablation)

| Configuration | SimPass | FinalPass |
|---------------|--------:|----------:|
| Full (PRE+RAG+repair) | 87/90 | 59/90 |
| w/o Knowledge | 83/90 | 57/90 |
| w/ Rewrite repair | 84/90 | 60/90 |
| w/o Repair | 77/90 | 53/90 |
| Direct LLM | 43/90 | 30/90 |

### Tier breakdown

Easy 15 · Medium 39 · Hard 29 · Expert 7 (total 90).

## Verification status

### Verified in this release

| Check | Result |
|-------|--------|
| `pytest` (`uv run python -m unittest discover -s tests -v`) | 36 passed, 0 failed |
| Cached-shard Table 1 rebuild (`scripts/build_table1_v2.py`) | Documented in [`manuscript_canonical_runbook.md`](manuscript_canonical_runbook.md) |
| Cached-shard Table 2 rebuild (`scripts/build_authoring90_ablation5_report.py`) | Documented in runbook |
| Secrets scan | clean — env-var reads only; no hardcoded secrets; fake values in test fixtures; no .env committed |

### Manual steps for the user

| Step | Status / notes |
|------|----------------|
| Live LLM re-run of full 90-task benchmark | Requires API keys and budget; see runbook Section 6 |
| GitHub push of `v1.0-canonical` tag to `KRATSZ/LabScript-AI` | succeeded — branch `manuscript` + tag `v1.0-canonical` pushed to https://github.com/KRATSZ/LabScript-AI.git (remote `canonical`) |
| Zenodo version upload / DOI metadata sync | Upload tarball; use [`zenodo_metadata.json`](zenodo_metadata.json) draft |
| Optional: remove stale LangGraph mention from `main` branch README on GitHub | Cosmetic; canonical code path is pure Python |

## Cached artifact layout

Frozen row roots are hard-coded in `scripts/build_table1_v2.py` (under `runs/`). Manuscript Table 1 anchor: `runs/table1_v3_fair/flash_seed01`. Manuscript Table 2 rows: `runs/table1_v3_fair/ablation_unified_flash/{no_kb,rewrite,no_repair,direct_llm}` plus `flash_seed01` for the Full row. The `runs/` tree is gitignored; obtain it from the Zenodo shard bundle (DOI 10.5281/zenodo.17697326) and place it at the repo root before rebuilding. (`runs/authoring90/ablation5_20260529` is a separate, earlier ablation run and is NOT the manuscript Table 2 source.)

## LLM stack note

- **Benchmark backbone (Tables 1–2):** `deepseek-v4-flash`
- **Methods / product stack:** Gemini 2.5 Pro via OpenRouter; Qwen3-Embedding-8B + Chroma for CODE_EXAMPLES RAG (see `docs/paper/.laipaper/main0714.md` Online Methods)
