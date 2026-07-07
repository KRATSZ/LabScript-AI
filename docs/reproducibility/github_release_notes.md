# v1.0-canonical — Canonical manuscript benchmark release

**Title:** LabScript-AI v1.0-canonical — manuscript Tables 1–2 reproduction

This release is the canonical implementation reproducing manuscript **Tables 1 and 2** on the 90-task Opentrons authoring benchmark. The benchmark stack uses pure Python agent loops (`LabscriptAgentLoop` for authoring; `RecoveryOrchestrator`, `RecoveryQueue`, and Gatekeeper for runtime recovery) with **no LangGraph** dependency on the reproduction path.

**Reproduce without LLM calls:** follow [`docs/reproducibility/manuscript_canonical_runbook.md`](docs/reproducibility/manuscript_canonical_runbook.md) — extract cached `runs/` artifacts from Zenodo, then run `scripts/build_table1_v2.py` and `scripts/build_authoring90_ablation5_report.py`.

**Zenodo:** [10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326) (benchmark tasks, frozen run logs, and analysis inputs).

**Citation:** see `CITATION.cff` at the repository root when present.

**Commit:** tag `v1.0-canonical` (resolve exact hash with: `git rev-list -n 1 v1.0-canonical`).
