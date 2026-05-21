# Authoring Benchmark Results

This page records the current 90-task authoring benchmark result used for the Table S3 scaffold comparison draft. The run fixes the author model to `deepseek-v4-flash` and the reviewer model to `deepseek-v4-pro`.

Evidence bundle:

- `runs/authoring-pilot/authoring-90-flash-comparison/comparison.md`
- `runs/authoring-pilot/authoring-90-flash-comparison/comparison.csv`
- `runs/authoring-pilot/authoring-90-flash-comparison/evidence-manifest.md`

Failure audit:

- `docs/research/authoring_failure_audit.md`

## Table S3 Draft: Same Base Model, Different Scaffolds

| Scaffold | Sim pass | Validator OK | Semantic OK | First-pass sim | Best-of-budget sim | Repaired sim | Reviewer mean | Bio | Liquid | Safety | Tokens/task | Wall min | Sim calls | Repair rounds | Tool calls | Skill loads |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 35/90 | 35/90 | 72/90 | 35/90 | 35/90 | 0/90 | 2.78 | 3.01 | 2.62 | 2.74 | 5,000 | 63.8 | 75 | 0 | 0 | 0 |
| direct DeepSeek + fix-loop | 77/90 | 73/90 | 86/90 | 37/90 | 77/90 | 40/90 | 3.46 | 3.67 | 3.21 | 3.41 | 9,588 | 112.5 | 189 | 99 | 0 | 0 |
| LabscriptAI authoring | 85/90 | 84/90 | 87/90 | 66/90 | 85/90 | 19/90 | 4.10 | 4.26 | 3.78 | 3.99 | 71,877 | 134.6 | 235 | 41 | 2009 | 583 |

## Reading

- Direct prompting is the lower bound: only 35/90 protocols simulate successfully, and reviewer mean is 2.78/5.
- The simulate-fail fix-loop is a strong middle baseline: simulation pass rises to 77/90, but first-pass success remains 37/90 and the scaffold spends 99 repair rounds.
- LabscriptAI authoring is the strongest scaffold in this run: 85/90 best-of-budget simulation pass, 66/90 first-pass simulation pass, and 4.10/5 reviewer mean.
- The cost tradeoff is real: LabscriptAI authoring uses many more tokens and tool calls. The paper should present this as stronger reliability and package quality at higher deliberation cost, not as a free improvement.

## hard35 v2 Preliminary Rerun

This run uses the revised hard subset `T056`-`T090`, keeping the author model fixed to `deepseek-v4-flash`. The subset replaces six softer/redundant tasks with four trap tasks and two PRE-style repair tasks, then scores with stricter deterministic semantic checks.

Evidence bundle:

- `runs/authoring-pilot/deepseek-direct-hard35-v2-flash/summary.json`
- `runs/authoring-pilot/deepseek-direct-hard35-v2-flash-analysis/attribution-summary.json`
- `runs/authoring-pilot/deepseek-fixloop-hard35-v2-flash/summary.json`
- `runs/authoring-pilot/deepseek-fixloop-hard35-v2-flash-analysis/attribution-summary.json`
- `runs/authoring-pilot/labscriptai-authoring/hard35-v2-flash/summary.json`
- `runs/authoring-pilot/labscriptai-authoring/hard35-v2-flash-analysis/attribution-summary.json`

| Scaffold | Sim pass | Validator OK | Semantic OK | First-pass sim | Best-of-budget sim | Repaired sim | Provider errors | Tokens/task | Wall min | Sim calls | Repair rounds | Tool calls | Skill loads | Failed sim tasks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| direct DeepSeek | 9/35 | 9/35 | 7/35 | 9/35 | 9/35 | 0/35 | 5 | 6,101 | 37.1 | 30 | 0 | 0 | 0 | T056, T057, T059, T060, T061, T062, T064, T065, T067, T068, T069, T071, T072, T073, T074, T075, T076, T077, T078, T079, T080, T082, T083, T084, T085, T087 |
| direct DeepSeek + fix-loop | 26/35 | 25/35 | 6/35 | 12/35 | 26/35 | 14/35 | 3 | 10,859 | 59.9 | 84 | 49 | 0 | 0 | T057, T061, T065, T076, T077, T079, T081, T083, T084 |
| LabscriptAI authoring | 34/35 | 34/35 | 12/35 | 26/35 | 34/35 | 8/35 | 0 | 86,477 | 60.8 | 96 | 15 | 836 | 230 | T079 |

Reading:

- The revised hard subset creates clear separation: direct prompting drops to 9/35, fix-loop reaches 26/35, and LabscriptAI reaches 34/35.
- The fix-loop rescues many runnable protocols, but its semantic score stays low. This is expected: repairing `protocol.py` can fix syntax/API failures without fixing cross-file experiment planning.
- LabscriptAI has the strongest best-of-budget and first-pass performance, but the semantic score shows the evaluator is now catching more than simulation success.
- Waste capacity is only checked when the task asks for a liquid-waste container or capacity. Generic fixed trash or waste-chute routing is not assigned a hard-coded liter capacity.

## hard35 v2 Composite Rescore

After the manual audit of LabscriptAI false negatives, the semantic validator was updated to accept real package-schema variants:

- `tip_plan.json`: nested totals, dict/list `tip_racks`, `pipettes.*.tips_used`, and `tip_usage[*].total_tips`.
- `reagent_plan.json`: alias keys such as `total_volume_required`, `total_volume_required_ul`, `total_volume_needed_ul`, and dict-form `reagents`.
- dynamic tasks: static reagent-total matching is deferred when the task depends on runtime parameters or CSV input.

The analysis pass now reports `task_pass = simulation_ok ∧ validator_ok ∧ semantic_ok ∧ param_sweep_ok`. The `param_sweep` hook is a deterministic v1 check: dynamic tasks must expose the expected runtime parameters and document how package plans change with those parameters. It does not yet inject two runtime values into the Opentrons simulator.

Evidence bundle:

- `runs/authoring-pilot/deepseek-direct-hard35-v2-flash-analysis-v3/attribution-summary.json`
- `runs/authoring-pilot/deepseek-fixloop-hard35-v2-flash-analysis-v3/attribution-summary.json`
- `runs/authoring-pilot/labscriptai-authoring/hard35-v2-flash-analysis-v3/attribution-summary.json`

| Scaffold | Sim pass | Validator OK | Semantic OK fixed | Param-sweep OK | Composite task pass | First-pass sim | Repair rounds | Tool calls | Skill loads |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 9/35 | 9/35 | 16/35 | 30/35 | 3/35 | 9/35 | 0 | 0 | 0 |
| direct DeepSeek + fix-loop | 26/35 | 25/35 | 14/35 | 35/35 | 9/35 | 12/35 | 49 | 0 | 0 |
| LabscriptAI authoring | 34/35 | 34/35 | 23/35 | 35/35 | 22/35 | 26/35 | 15 | 836 | 230 |

Decision:

- LabscriptAI composite is `22/35` (`63%`), below the pre-agreed stop threshold `≤24/35`.
- Therefore hard35 v2 does not need more task replacement before the next model rerun. The main issue was not that LabscriptAI needed to be artificially pushed down; the scoring ruler needed to measure experiment planning, not only whether Python simulates.
- The next paper-facing run should keep this composite metric and move to stronger author models or external mini-benchmarks.

## hard35 v2 Live Rerun With Composite Metric

This rerun regenerates all `T056`-`T090` packages with the same author model, `deepseek-v4-flash`, after the semantic validator alias fixes and deterministic `param_sweep` hook were added. It is the current weak-model hard35 table.

Evidence bundle:

- `runs/authoring-pilot/deepseek-direct-hard35-v2-flash-rerun-composite/summary.json`
- `runs/authoring-pilot/deepseek-direct-hard35-v2-flash-rerun-composite-analysis/attribution-summary.json`
- `runs/authoring-pilot/deepseek-fixloop-hard35-v2-flash-rerun-composite/summary.json`
- `runs/authoring-pilot/deepseek-fixloop-hard35-v2-flash-rerun-composite-analysis/attribution-summary.json`
- `runs/authoring-pilot/labscriptai-authoring/hard35-v2-flash-rerun-composite/summary.json`
- `runs/authoring-pilot/labscriptai-authoring/hard35-v2-flash-rerun-composite-analysis/attribution-summary.json`

| Scaffold | Sim pass | Validator OK | Semantic OK fixed | Param-sweep OK | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Sim calls | Tokens/task | Wall min | Tool calls | Skill loads | Provider errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 10/35 | 10/35 | 13/35 | 33/35 | 4/35 | 10/35 | 0/35 | 0 | 33 | 6,145 | 36.2 | 0 | 0 | 2 |
| direct DeepSeek + fix-loop | 28/35 | 27/35 | 14/35 | 35/35 | 11/35 | 12/35 | 16/35 | 51 | 86 | 11,931 | 61.9 | 0 | 0 | 3 |
| LabscriptAI authoring | 34/35 | 32/35 | 19/35 | 35/35 | 17/35 | 29/35 | 5/35 | 10 | 91 | 82,634 | 52.2 | 784 | 225 | 0 |

Decision:

- LabscriptAI composite is `17/35` (`49%`), below the pre-agreed `≤24/35` stop threshold.
- Do not harden tasks further before the next paper-facing model run. The current benchmark already separates "code can run" from "experiment package is coherent".
- The main result to show in the paper should be composite task pass plus sub-metrics. Simulation pass remains an auxiliary metric because it is too easy to saturate.

Interpretation:

- Direct prompting is still weak: only `4/35` tasks satisfy runnable code, package validation, semantic checks, and param-sweep together.
- The protocol-only fix-loop is useful but limited: it raises simulation to `28/35`, yet composite only reaches `11/35` because metadata and experimental planning remain inconsistent.
- LabscriptAI is best but not saturated: `17/35` leaves enough headroom for stronger models, package-level repair, and better planning tools.

## hard35 v2 Clean Codex Coding-Agent Baseline

These Codex runs treat Codex as a fourth comparison point. Each task was executed in a fresh empty `/tmp` working directory with repository instructions, user config, memories, plugins, apps, browser/computer-use, image generation, and tool search disabled. The child Codex process only received the task JSON and package requirements. Simulation and validation were run post-hoc by the outer benchmark runner, not forced inside the child Codex prompt.

Evidence bundle:

- `scripts/run_codex_authoring_baseline.py`
- `runs/authoring-pilot/coding-agent-codex/hard35-clean-v1/summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-clean-v1-analysis/attribution-summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-smoke5/summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-smoke5-analysis/attribution-summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-remaining30/summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-remaining30-analysis/attribution-summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-rerun-t089-t090/summary.json`
- `runs/authoring-pilot/coding-agent-codex/hard35-direct-aligned-repair-v1-rerun-t089-t090-analysis/attribution-summary.json`

| Scaffold | Sim pass | Validator OK | Semantic OK fixed | Param-sweep OK | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Sim calls | Tokens/task | Wall min | Tool calls | Skill loads | Provider errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clean Codex coding-agent raw minimal prompt | 21/35 | 0/35 | 2/35 | 35/35 | 0/35 | 21/35 | 0/35 | 0 | 35 | 18,852 | 65.5 | 0 | 0 | 0 |
| clean Codex coding-agent direct-aligned + metadata-repair | 19/35 | 19/35 | 6/35 | 35/35 | 4/35 | 19/35 | 0/35 | 0 | 35 | 22,557 | 69.0 | 0 | 0 | 0 |

Reading:

- The raw minimal-prompt run is intentionally harsh. It only gave Codex the seven filenames, task text, and manifest requirements. It is useful as a very clean general coding-agent baseline, but it is not prompt-aligned with direct DeepSeek.
- The direct-aligned run adds the same package rules that direct DeepSeek received and then applies the same deterministic metadata repair externally. That moves Codex from `0/35` validator pass to `19/35` validator pass and reaches `4/35` composite task pass, which is the fairer comparison point.
- After quota refresh, `T089` and `T090` were rerun successfully. The final direct-aligned Codex row is now a complete `35/35` result with `0` provider errors. The remaining gap is content quality, not infrastructure availability.

## External Community Bench: 66 Tasks

This expanded external bench checks whether the same author model, `deepseek-v4-flash`, can turn outside protocol descriptions into execution packages. The set now contains 18 Opentrons Protocol Library-style tasks, 18 OpenPlant Automation Protocols-style tasks, and 30 PyLabRobot community/backend-neutral tasks.

The merged table reuses the earlier external runs where task definitions were unchanged, then adds the new `external-expanded-v2` run for `EOPEN007`-`EOPEN018` and `EPLR021`-`EPLR030`. When task IDs overlap, the newer source-specific run is treated as canonical.

Evidence bundle:

- `benchmarks/external_community/tasks.yaml`
- `runs/authoring-pilot/external-30/deepseek-direct-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-30/deepseek-direct-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-30/deepseek-fixloop-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-30/deepseek-fixloop-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-30/labscriptai-authoring-flash/summary.json`
- `runs/authoring-pilot/external-30/labscriptai-authoring-flash-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/deepseek-direct-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/deepseek-direct-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/deepseek-fixloop-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/deepseek-fixloop-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/labscriptai-authoring-flash/summary.json`
- `runs/authoring-pilot/external-pylabrobot-20/labscriptai-authoring-flash-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-expanded-v2/deepseek-direct-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-expanded-v2/deepseek-direct-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-expanded-v2/deepseek-fixloop-flash-maxtok12k/summary.json`
- `runs/authoring-pilot/external-expanded-v2/deepseek-fixloop-flash-maxtok12k-analysis/attribution-summary.json`
- `runs/authoring-pilot/external-expanded-v2/labscriptai-authoring-flash/summary.json`
- `runs/authoring-pilot/external-expanded-v2/labscriptai-authoring-flash-analysis/attribution-summary.json`

Paper-facing source breakdown, composite task pass:

| Scaffold | Opentrons Library 18 | OpenPlant 18 | PyLabRobot community/backend 30 |
|---|---:|---:|---:|
| direct DeepSeek | 10/18 | 9/18 | 16/30 |
| direct DeepSeek + fix-loop | 14/18 | 16/18 | 30/30 |
| LabscriptAI authoring | 18/18 | 15/18 | 29/30 |

OpenPlant 18 detail:

| Scaffold | Sim pass | Validator OK | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Failed task IDs |
|---|---:|---:|---:|---:|---:|---:|---|
| direct DeepSeek | 10/18 | 9/18 | 9/18 | 10/18 | 0/18 | 0 | EOPEN002, EOPEN003, EOPEN004, EOPEN005, EOPEN006, EOPEN007, EOPEN015, EOPEN017, EOPEN018 |
| direct DeepSeek + fix-loop | 16/18 | 16/18 | 16/18 | 7/18 | 9/18 | 22 | EOPEN005, EOPEN018 |
| LabscriptAI authoring | 15/18 | 15/18 | 15/18 | 5/18 | 10/18 | 23 | EOPEN008, EOPEN009, EOPEN017 |

PyLabRobot community/backend 30 detail:

| Scaffold | Sim pass | Validator OK | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Failed task IDs |
|---|---:|---:|---:|---:|---:|---:|---|
| direct DeepSeek | 16/30 | 16/30 | 16/30 | 16/30 | 0/30 | 0 | EPLR004, EPLR005, EPLR008, EPLR009, EPLR011, EPLR013, EPLR015, EPLR018, EPLR021, EPLR022, EPLR025, EPLR027, EPLR029, EPLR030 |
| direct DeepSeek + fix-loop | 30/30 | 30/30 | 30/30 | 18/30 | 12/30 | 19 | - |
| LabscriptAI authoring | 29/30 | 29/30 | 29/30 | 17/30 | 12/30 | 20 | EPLR030 |

New 22-task expansion aggregate:

| Scaffold | Sim pass | Validator OK | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Provider errors | Tokens/task | Wall min | Tool calls | Skill loads |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 12/22 | 12/22 | 12/22 | 12/22 | 0/22 | 0 | 1 | 2,932 | 14.3 | 0 | 0 |
| direct DeepSeek + fix-loop | 21/22 | 21/22 | 21/22 | 10/22 | 11/22 | 19 | 1 | 5,463 | 19.1 | 0 | 0 |
| LabscriptAI authoring | 18/22 | 18/22 | 18/22 | 6/22 | 12/22 | 29 | 0 | 91,224 | 77.3 | 464 | 148 |

### External Failure Regression: Deterministic Lint/Patch

After the first external run, four LabscriptAI failures were traced to simple engineering problems rather than missing biological reasoning. The authoring runner now applies deterministic package/protocol repairs before spending LLM repair budget:

- Guard `pick_up_tip()` with a tiprack reset fallback for known out-of-tips simulator failures.
- Split common oversized aspirate/dispense pairs that use `pipette.current_volume`.
- Open thermocycler lids immediately after thermocycler labware loading when later pipetting into that labware.
- Make reagent `slot`/`well` lookup tolerant of common plan aliases.
- Sync package JSON plan files into `/tmp` before simulation when generated protocols read `/tmp/deck_plan.json`, `/tmp/reagent_plan.json`, or `/tmp/tip_plan.json`.

Targeted regression evidence uses the previous failed packages copied from `runs/authoring-pilot/external-expanded-v2/labscriptai-authoring-flash/*/attempt4/package`, without any new model calls:

| Task | Previous failure | Deterministic repair hit | Targeted simulate after patch |
|---|---|---|---:|
| EOPEN008 | `OutOfTipsError` | guarded `pick_up_tip()` | pass |
| EOPEN009 | `InvalidAspirateVolumeError` | split oversized aspirate/current-volume dispense | pass |
| EOPEN017 | `ThermocyclerNotOpenError` | inserted `tc_mod.open_lid()` before thermocycler plate access | pass |
| EPLR030 | `KeyError: 'slot'` / stale `/tmp` plan state | alias-tolerant lookup + `/tmp` JSON sync | pass |

Projected paper-facing impact if only these known failures change and all other rows stay fixed:

| Scaffold | OpenPlant 18 | PyLabRobot community/backend 30 | New 22-task expansion |
|---|---:|---:|---:|
| direct DeepSeek | 9/18 | 16/30 | 12/22 |
| direct DeepSeek + fix-loop | 16/18 | 30/30 | 21/22 |
| LabscriptAI authoring before patch | 15/18 | 29/30 | 18/22 |
| LabscriptAI authoring targeted projection | 18/18 | 30/30 | 22/22 |

This projection should be labeled as targeted regression evidence until a live rerun confirms it. It is still useful because it shows the fix is not "more agent thinking"; it is a smaller loop with deterministic lint for repeated simulator failure classes.

### Three-Piece Package Live A/B: OpenPlant 6 Tasks

This live rerun checks the v0.4 three-piece package format:

- `protocol.py`
- `setup_card.html`
- `manifest.json`

The rerun uses the current LabscriptAI authoring path, light skill mode, and DeepSeek API credentials from the local environment. `deepseek-v4-pro` was too slow for this batch smoke test, so the completed run uses `deepseek-v4-flash` with the same 12k max-token setting used by earlier weak-model benchmark rows.

Evidence bundle:

- `runs/authoring-pilot/three-piece-labscriptai-ab6-flash-rerun/summary.json`

Task selection:

- Previous LabscriptAI OpenPlant failures: `EOPEN008`, `EOPEN009`, `EOPEN017`
- Light-mode controls that previously passed: `EOPEN001`, `EOPEN002`, `EOPEN003`

| Format | Tasks | Package complete | Validator OK | Sim pass | First-pass sim | Provider errors | Generation attempts | Tokens | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.4 three-piece | 6 | 6/6 | 6/6 | 6/6 | 6/6 | 0 | 6 | 491,233 | 6.5 min |

Decision:

- The three-piece compatibility layer is live enough for the next broader benchmark stage.
- The legacy seven-file reader stays in place because historical 90-task baselines still need to load old packages.
- Do not delete old readers until the 90-task baseline has either been migrated or regenerated.

### Three-Piece Package Full Rerun: OpenPlant 18

This live rerun regenerates all `EOPEN001`-`EOPEN018` tasks with the v0.4 three-piece format:

- `protocol.py`
- `setup_card.html`
- `manifest.json`

The direct row was run as one batch. The fix-loop and LabscriptAI rows were split into 9 total parallel shards to reduce wall-clock time while keeping each shard in its own output directory. The table reports summed work for tokens/tool calls and the observed parallel wall time for sharded rows.

Evidence bundle:

- `runs/authoring-pilot/openplant18-threepiece/direct-flash/summary.json`
- `runs/authoring-pilot/openplant18-threepiece/direct-flash-analysis/attribution-summary.json`
- `runs/authoring-pilot/openplant18-threepiece-sharded/fixloop-flash-merged/summary.json`
- `runs/authoring-pilot/openplant18-threepiece-sharded/fixloop-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/openplant18-threepiece-sharded/labscriptai-authoring-light-flash-merged/summary.json`
- `runs/authoring-pilot/openplant18-threepiece-sharded/labscriptai-authoring-light-flash-merged-analysis/attribution-summary.json`

| Scaffold | Tasks | Package complete | Validator OK | Sim pass | Composite task pass | First-pass sim | Repaired sim | Repair rounds | Provider errors | Tokens/task | Wall min | Tool calls | Skill loads | Failed task IDs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| direct DeepSeek | 18 | 18/18 | 8/18 | 9/18 | 8/18 | 9/18 | 0/18 | 0 | 0 | 2,979 | 6.2 | 0 | 0 | EOPEN002, EOPEN003, EOPEN004, EOPEN006, EOPEN007, EOPEN008, EOPEN011, EOPEN012, EOPEN013, EOPEN014 |
| direct DeepSeek + fix-loop | 18 | 18/18 | 13/18 | 14/18 | 13/18 | 10/18 | 4/18 | 16 | 0 | 7,099 | 4.4 | 0 | 0 | EOPEN002, EOPEN008, EOPEN009, EOPEN016, EOPEN018 |
| LabscriptAI authoring light | 18 | 18/18 | 17/18 | 17/18 | 17/18 | 16/18 | 1/18 | 4 | 0 | 86,302 | 5.3 | 287 | 37 | EOPEN018 |

Reading:

- The new v0.4 three-piece format does not hurt the main scaffold result. LabscriptAI reaches `17/18` composite task pass on the full OpenPlant subset.
- The fix-loop remains useful but weaker: it improves direct prompting from `8/18` to `13/18`, mostly by repairing simulator failures, not by improving package planning.
- The LabscriptAI row costs much more token budget. This should be presented as a reliability/cost tradeoff, not a free win.
- The only remaining LabscriptAI OpenPlant failure is `EOPEN018`, so the next debugging target is narrow.

### Freeze v0.4 Full Rerun: Authoring 90 + External 66

Date: 2026-05-20.

Freeze rule: no benchmark-code, prompt, validator, or task patch was made from failures observed in this run. The only allowed action was sharded execution and result aggregation.

Execution setup:

- Model: `deepseek-v4-flash` from `.env`.
- Max concurrency: 9 shards.
- Repair cap: `--simulation-repair-attempts 3` for fix-loop and LabscriptAI rows.
- LabscriptAI skill mode: `--authoring-skill-mode light`.
- Opentrons simulator: `/Users/gaoyuan/Downloads/opentrons/api/.venv/bin/python`.
- Workspace root: `/Users/gaoyuan/Downloads/opentrons`.

Evidence bundle:

- `runs/authoring-pilot/freeze-v04-20260520/authoring90/direct-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/authoring90/direct-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/authoring90/fixloop-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/authoring90/fixloop-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/authoring90/labscriptai-authoring-light-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/authoring90/labscriptai-authoring-light-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/direct-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/direct-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/fixloop-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/fixloop-flash-merged-analysis/attribution-summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/labscriptai-authoring-light-flash-merged/summary.json`
- `runs/authoring-pilot/freeze-v04-20260520/external66/labscriptai-authoring-light-flash-merged-analysis/attribution-summary.json`

#### Authoring 90 Table

| Scaffold | Tasks | Validator OK | Sim pass | Semantic OK | Param sweep OK | Composite task pass | Trace present | Tokens/task | Summed work min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 90 | 37/90 | 38/90 | 56/90 | 85/90 | 23/90 | 0/90 | 4,779 | 54.6 |
| direct DeepSeek + fix-loop | 90 | 72/90 | 80/90 | 60/90 | 87/90 | 45/90 | 0/90 | 8,982 | 88.2 |
| LabscriptAI authoring light | 90 | 84/90 | 85/90 | 63/90 | 87/90 | 56/90 | 90/90 | 84,260 | 106.4 |

#### External 66 Table

| Scaffold | Tasks | Validator OK | Sim pass | Semantic OK | Param sweep OK | Composite task pass | Trace present | Tokens/task | Summed work min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct DeepSeek | 66 | 58/66 | 62/66 | 65/66 | 66/66 | 57/66 | 0/66 | 5,729 | 40.8 |
| direct DeepSeek + fix-loop | 66 | 61/66 | 62/66 | 66/66 | 66/66 | 61/66 | 0/66 | 5,990 | 41.0 |
| LabscriptAI authoring light | 66 | 61/66 | 63/66 | 65/66 | 66/66 | 60/66 | 66/66 | 74,577 | 69.3 |

Reading:

- On the harder internal 90-task set, LabscriptAI light is clearly strongest: `56/90` composite versus `45/90` for fix-loop and `23/90` for direct.
- On the external 66-task set, the protocol-only fix-loop is slightly ahead: `61/66` versus `60/66` for LabscriptAI light. The honest reading is that these external tasks are easier and mostly reward simulator/package repair.
- LabscriptAI light is still much more expensive in tokens. Its value is stronger on the main 90-task benchmark where task structure is richer; it is not a free win on every external task.

### Skill Ablation Plan

The authoring CLI now supports `--authoring-skill-mode full|light|off` for `--provider labscriptai-authoring`.

| Mode | What changes | Expected use | Expected token effect |
|---|---|---|---:|
| `full` | all skills exposed, current default | main 90-task run and biology-heavy tasks | baseline |
| `light` | only `common_errors` and `deck_layout` are loadable | external tasks with mostly API/deck failures | lower |
| `off` | no `load_skill` tool exposed | ablation: test whether external simulator failures need skills | lowest |

Recommended ablation command shape:

```bash
PYTHONPATH=src DEEPSEEK_MODEL=deepseek-v4-flash \
uv run python -m labscriptai.benchmark.authoring_pilot \
  --tasks benchmarks/external_community/tasks.yaml \
  --task-ids EOPEN001,EOPEN002,EOPEN003,EOPEN004,EOPEN005,EOPEN006,EOPEN007,EOPEN008,EOPEN009,EOPEN010,EOPEN011,EOPEN012,EOPEN013,EOPEN014,EOPEN015,EOPEN016,EOPEN017,EOPEN018 \
  --provider labscriptai-authoring \
  --authoring-skill-mode off \
  --simulate \
  --opentrons-python .venv-protocol/bin/python \
  --simulation-repair-attempts 3 \
  --agent-max-steps 8 \
  --output-dir runs/authoring-pilot/external-skill-ablation/openplant18-off
```

Run the same command with `light` and `full`, then analyze each summary with `benchmark.analyze_authoring_run`. The expected paper table is:

| Skill mode | OpenPlant 18 task pass | Tokens/task | Tool calls/task | Skill loads/task | Interpretation |
|---|---:|---:|---:|---:|---|
| full | TBD rerun | TBD | TBD | TBD | current rich agent baseline |
| light | TBD rerun | lower than full | lower | near 0-2 | likely best external tradeoff |
| off | TBD rerun | lowest | lower | 0 | tests whether deterministic lint is enough |

PyLabRobot software/backend-layer sanity:

- Command: `PYTHONPATH=src:tests uv run --with pylabrobot python -m unittest tests.test_pylabrobot_smoke`
- Result: 3 tests passed.
- Interpretation: the local LabFlow IR can drive real PyLabRobot APIs through a serializing backend, platform resource mappings for Opentrons/Hamilton/Tecan, and an OT-2 simulator backend. This is software/backend compatibility evidence, not physical Hamilton/Tecan/Opentrons hardware execution.

Legacy reading:

- The older external-66 aggregate above is superseded by the frozen v0.4 rerun table. Do not cite the old `35/66` aggregate as the current result.
- The still-valid caution is that external tasks have looser structured `spec` fields, so this table is best treated as external generalization evidence dominated by simulation and package validation, not as the main biological-correctness table.
- Physical cross-workstation execution still requires a real backend, connection details, deck/resource config, and a safety plan from the target workstation.

## Current Gaps Before Paper Freeze

- Add at least one non-DeepSeek reviewer or human blind-review subset before treating reviewer scores as final expert evidence.
- Use the current failure audit to harden tip planning, module-state handling, malformed JSON recovery, and dynamic input validation before another full run.
- Keep the deterministic semantic validator separate from the LLM reviewer in all tables; they answer different questions.
