# v1.0-canonical — Canonical manuscript benchmark release

**Title:** LabScript-AI v1.0-canonical — manuscript Tables 1–2 reproduction

This release is the canonical implementation reproducing manuscript **Tables 1 and 2** on the 90-task Opentrons authoring benchmark. The benchmark stack uses pure Python agent loops (`LabscriptAgentLoop` for authoring; `RecoveryOrchestrator`, `RecoveryQueue`, and Gatekeeper for runtime recovery) with **no LangGraph** dependency on the reproduction path.

**Reproduce without LLM calls:** follow [`docs/reproducibility/manuscript_canonical_runbook.md`](docs/reproducibility/manuscript_canonical_runbook.md) — extract cached `runs/` from Zenodo (gitignored; lives under `runs/table1_v3_fair/`), then run `PYTHONPATH=src uv run python scripts/build_table1_v2.py`. Table 2 ablation rows are read from `runs/table1_v3_fair/ablation_unified_flash/` (not `ablation5_20260529`).

**Zenodo:** [10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326) (benchmark tasks, frozen run logs, and analysis inputs).

**Citation:** see `CITATION.cff` at the repository root.

**Branch:** `manuscript` · **Tag:** `v1.0-canonical`
