# Table S2A — External community generalization (66 held-out tasks)

**Takeaway.** On held-out community protocols never used for prompt or knowledge-base
engineering, the LabscriptAI scaffold raises best-of-budget composite pass from
**31/66** (direct LLM) to **56/66** and blind expert quality from **3.78** to **4.31/5**,
with gains on every source subset (Opentrons Library 7→14/18, OpenPlant 7→13/18,
PyLabRobot-style 17→29/30). This indicates the framework **generalizes beyond the
in-distribution 90-task set** (external adaptability), not only that it fits the
benchmark it was tuned on.

Both rows use the py-only contract (the model writes `protocol.py`; harness derives
`manifest.json` and `setup_card.html`) and base model **DeepSeek-V4-Pro**; the agent
row uses rewrite repair (budget 20; observed max 3). This is the v2 freeze
(2026-05-28); it was not rerun in the Table 1 v3 fair pass, so it shares the py-only
contract with the main-table anchor but differs in model variant and repair scaffold.
S2A is generalization side-evidence; the main conclusion rests on Table 1 / Table S1.

## Panel A — Overall (n = 66)

| Scaffold | BoB composite‡ | Sim | Validator | Semantic | Param-sweep | Expert§ | Tokens/task | $/task¶ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Direct (LLM-only, DeepSeek-V4-Pro) | 31/66 | 34/66 | 34/66 | 58/66 | 63/66 | 3.78 | 5,296 | $0.0044 |
| LabscriptAI authoring (light) | 56/66 | 60/66 | 60/66 | 64/66 | 64/66 | 4.31 | 69,399 | $0.0329 |

## Panel B — By source subset

| Subset | n | Scaffold | BoB composite‡ | Sim | Validator | Semantic | Param-sweep | Expert§ | Tokens/task | $/task¶ |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Opentrons Protocol Library (EOPL) | 18 | Direct | 7/18 | 8/18 | 8/18 | 14/18 | 17/18 | 3.56 | 7,094 | $0.0060 |
|  |  | LabscriptAI | 14/18 | 15/18 | 15/18 | 17/18 | 18/18 | 4.01 | 83,049 | $0.0401 |
| OpenPlant source-strict (EOPEN) | 18 | Direct | 7/18 | 8/18 | 8/18 | 15/18 | 16/18 | 3.84 | 6,918 | $0.0058 |
|  |  | LabscriptAI | 13/18 | 15/18 | 15/18 | 18/18 | 16/18 | 4.21 | 92,430 | $0.0442 |
| PyLabRobot-style (EPLR) | 30 | Direct | 17/30 | 18/30 | 18/30 | 29/30 | 30/30 | 3.89 | 3,244 | $0.0027 |
|  |  | LabscriptAI | 29/30 | 30/30 | 30/30 | 29/30 | 30/30 | 4.55 | 47,390 | $0.0217 |

## Table notes

- **‡ BoB composite (best-of-budget).** Authoring pass rate is the fraction of tasks
  whose **final** submitted package, produced within the unified budget (≤8 attempts,
  ≤30 min wall time, ≤24k output tokens, ≤80 tool calls), simultaneously satisfies four
  deterministic gates — `simulation_ok` (Opentrons simulator/analyze passes),
  `validator_ok` (three-piece package complete; deck/reagent/tip/manifest consistent;
  no critical failure), `semantic_ok` (semantic validator), and `param_sweep_ok`
  (parameter-sweep validator). Gates are computed per task in
  `src/labscriptai/benchmark/analyze_authoring_run.py`
  (`task_pass = simulation_ok ∧ validator_ok ∧ semantic_ok ∧ param_sweep_ok`) and
  aggregated as `task_pass_count`. BoB credits a correct final package regardless of
  whether it was produced first-shot or after repair, so systems with and without a
  repair loop are scored on the same four gates and the same budget. The separate
  first-shot (no-repair) FP composite and the FP→BoB repair-contribution gap are
  reported in the scaffold-ablation table (Table S1), not here. **Sim / Validator /
  Semantic / Param-sweep** columns are the four gates broken out (each x/N).
- **§ Expert.** Single blind LLM-reviewer mean over five dimensions (task alignment,
  biological reasonableness, liquid-handling quality, safety/control, code quality),
  n = 66 fully reviewed per row. This is **not** the three-LLM panel used for Table 1
  and is not directly comparable to the Table 1 Expert column. Per-subset Expert is the
  mean of that subset's tasks.
- **¶ $/task.** Per-task cost at DeepSeek-V4-Pro official list price (input
  $0.435/M tokens, output $0.87/M; source https://api-docs.deepseek.com/quick_start/pricing),
  computed from logged per-task input/output tokens. Per-subset $/task uses the same
  price and the subset's token sum.
- **Task set (provenance).** 66 = 18 EOPL (Opentrons Protocol Library public-protocol
  adaptations) + 18 EOPEN (OpenPlant source-strict adaptations) + 30 EPLR (PyLabRobot-
  style: 13 documentation/API concept adaptations + 17 project-authored backend-neutral
  stress tasks). **Only the 36 EOPL + EOPEN tasks trace to real public protocol
  entries**; the 30 EPLR tasks are documentation-derived or project-authored. Do not
  claim all 66 are real public protocol entries. Provenance audit:
  `benchmarks/external_community/OPENPLANT_PROVENANCE.md`.
- **Operational metrics (overall, not in panels).** Provider-error events 2 (Direct)
  and 3 (LabscriptAI) of 66; final API failures 0 and 0; tool calls 0 and 538;
  simulator calls 66 and 215; execution traces present 0/66 and 66/66. Both rows are
  below the 5% provider-error inclusion gate (3.0% and 4.5%) and are included.
- **Baseline scope.** External 66 was run with LabscriptAI + one LLM-only direct
  baseline (DeepSeek-V4-Pro); no coding-agent baseline was run on this set. Per the
  paper plan, external 66 is generalization side-evidence and the main systems
  comparison is on the 90-task set (Table 1).
- **Claim boundary.** S2A is side-evidence for external adaptability. The main
  authoring-quality conclusion rests on Table 1 / Table S1 (90 tasks). LabscriptAI
  authoring numbers here are from `labscriptai-authoring-light`, not
  `labscriptai-full` end-to-end.

## Source data (reproducibility)

- Per-metric JSON + tidy CSV + verification:
  `supplementary/table_s2a_external66_data.{json,csv,md}` (generated by
  `scripts/build_s2a_external66_data.py`; all numbers cross-checked against frozen
  anchors).
- Run artifacts: `runs/table1_v2_external66_llm_only_py_official_deepseek/`
  (Direct) and `runs/table1_v2_external66_unified_py_official_deepseek_pure/`
  (LabscriptAI agent); each holds `summary.json`, `analysis/attribution-summary.json`,
  and `expert_review/review-summary.json`.
- Metric decision (FP vs BoB): `supplementary/fp_vs_bob_recommendation.md`.
