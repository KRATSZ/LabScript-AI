# Paper Deliverables Index

投稿图表与证据的单页索引。详细叙事与口径见 [`paper_execution_plan.md`](paper_execution_plan.md)。

Updated: 2026-05-21

## Main text

| ID | Deliverable | Answers | Status |
| --- | --- | --- | --- |
| Fig1 | Dual-loop architecture (authoring + runtime + memory) | What is LabscriptAI? | Draft |
| Table1 | Systems × Evidence (8 columns, no Sim) | Barbara: vs existing LLM / coding agents | Partial (LabscriptAI freeze; others TBD) |
| ExtFig | Runtime recovery + memory reuse panels | Real robot + episodic reuse | Pending ≥3 paired cases |

Videos: tip recovery contrast (Video 1); memory round 1 vs 2 (Video 2).

## Supplementary numbered tables (only these two)

| ID | Deliverable | Data source |
| --- | --- | --- |
| S1 | Scaffold ablation, 90 tasks, fixed `deepseek-v4-flash` | `runs/authoring-pilot/freeze-v04-20260520/authoring90/` |
| S2A | External 66 generalization (3 subsets) | `freeze-v04-20260520/external66/`; OpenPlant rerun per `OPENPLANT_PROVENANCE.md` |
| S2B | LabFlow IR portability (5–10 tasks) | `tests/test_pylabrobot_smoke`; software/backend only |

## Methods / Data (not numbered as S tables)

| Artifact | Path (planned) | Was |
| --- | --- | --- |
| Baseline manifest | `supplementary/baseline_manifest.csv` | old S1 |
| Runtime per-case | `supplementary/runtime_cases.csv` from frozen `benchmarks/runtime/runtime20.yaml` | old S4 |
| Capability matrix | Discussion prose | old S5 |
| Per-task scores | `supplementary/authoring90_scores.csv` | — |

## Claim boundaries (do not mix)

- **Table1 / S1 authoring**: `labscriptai-authoring-light` only — not `labscriptai-full` 90-task end-to-end.
- **Table1 Runtime/Memory + ExtFig**: independent case studies — not derived from 56/90 composite.
- **S2A**: generalization side evidence; fix-loop may edge LabscriptAI on easy external tasks.
- **S2B**: PyLabRobot API compatibility — not Hamilton/Tecan hardware.

## Evidence bundle

- Numbers: [`authoring_benchmark_results.md`](authoring_benchmark_results.md) → section **Paper-facing tables**
- Implementation: [`rollout_12_status.md`](rollout_12_status.md)
- Runtime code status: [`runtime_build_plan.md`](runtime_build_plan.md) §2.1
- HTML dashboards (local open in browser): [`dashboards/status.html`](dashboards/status.html), [`dashboards/benchmark_freeze_review.html`](dashboards/benchmark_freeze_review.html)
- Run artifact pointers (before cleaning `runs/`): [`evidence/README.md`](evidence/README.md)

## Export checklist (before manuscript freeze)

- [ ] Table1: all systems run on 90 tasks with same budget
- [ ] Table1: LabscriptAI footnotes authoring-light vs ExtFig runtime
- [ ] S1: FP composite aggregated from freeze runs
- [ ] S2A: OpenPlant source-strict 18 rerun; provider errors reported
- [ ] S2B: fill X001–X007 from IR compile runs
- [ ] ExtFig: ≥3 physical paired cases from frozen Runtime20 + 1 memory two-round case
