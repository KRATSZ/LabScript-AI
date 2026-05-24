# NBT Revision Log

This log records benchmark changes made for the 2026 Q2 NBT revision. Keep entries short and evidence-oriented so they can be reused in reviewer rebuttal and supplement notes.

## 2026-05-15

- Created revision branch `bench/nbt-revision-2026q2`.
- Froze the v0.1 authoring benchmark task manifest as `benchmarks/authoring/tasks.v0.1.yaml`.
- Forked new benchmark work into `benchmarks/authoring/tasks.yaml` (schema v0.2; previously a separate `tasks.v0.2.yaml` file).
- Froze the v0.1 hold-out manifest as `benchmarks/authoring/holdout_manifest.v0.1.json`.
- Verified upstream `labauto/Inagaki_2023_GPT4OT2` license as MIT at commit `0ef14a3a83254a7bd0eb908e28810ee8583f7fdc`.
- Added v0.2 upstream metadata and per-task `upstream_id` / `upstream_question_index` attribution for legacy tasks `T001-T055`.
- Renamed the v0.2 task contract from `seven_file_protocol_package` to `execution_package` and added `adapter_default: opentrons`.
- Added minimum scoring `spec` blocks to new tasks `T056-T090`, including default sample counts, reagent volumes, controls, and expected risk flags.
- Added deterministic `risk_flag_recall` scoring support to the package validator and score record schema.
- Added `src/labscriptai/benchmark/contamination_probe.py` with verbatim completion, source attribution, and canary negative-control probes for OpenAI-compatible model APIs.
- Rewrote off-platform instrument tasks `T039`, `T041`, `T047`, `T051`, `T052`, and `T053` to stop at handoff and added `off_platform_handoff` fields in `tasks.yaml`.
- Added deterministic `handoff_declared_score` validation for expected off-platform handoffs.
- Added the `level` x `difficulty` allowed matrix to `docs/research/benchmark_taxonomy.md` and locked v0.2 taxonomy corrections (`T013`, `T036`, `T045`, `T050`, `T051`, `T086-T090`) with tests.

## 2026-05-17

- Split package validation into `src/labscriptai/benchmark/validators/core.py` (platform-agnostic) and `validators/opentrons.py` (protocol AST vs deck).
- `package_validator` CLI: `--task-manifest` and `--task-id` merge `spec.expected_risk_flags` and `off_platform_handoff` from `tasks.yaml`.
- Added `schemas/adapters/opentrons.schema.json` stub for adapter metadata.
- `contamination_probe`: `--deepseek-smoke` fixed 6-task run; skips cleanly when `DEEPSEEK_API_KEY` is unset.
- `contamination_probe`: legacy verbatim probe skips shared boilerplate line so ROUGE-L is not degenerate across all 55 legacy tasks.
- Wrote `benchmarks/authoring/contamination_readiness.json` (local stats; no LLM) for A1 probe design.
- Fixed DeepSeek V4 chat parsing: send `thinking: {type: disabled}` and fall back to `reasoning_content` if needed so `contamination_probe` records non-empty completions.
- Ran full 90-task DeepSeek contamination probe (`contamination_report.deepseek_v4_full_90.json` + `.summary.json`); ~8.2 min wall time with 0.12s inter-call sleep.

## 2026-05-18

- **Taxonomy**: Removed the `level` (L1–L6) dimension from tasks, the task loader, stratified sampling, analyze reports, and tests; tasks now use only `difficulty ∈ {Easy, Medium, Hard, Expert}` (the 2026-05-15 bullet about a `level` × `difficulty` matrix is historical—see git history if you need that matrix text).
- **Documentation sync**: Refreshed `docs/research/runtime_build_plan.md` §2 so “gaps” match the code that already exists under `src/labscriptai/` (see that file’s §2.1 / §6 progress note).
- **Canonical authoring paths (this checkout)**: Active manifest is `benchmarks/authoring/tasks.yaml` (header: schema `0.2`, single canonical file). Companion files in the same directory: `holdout_manifest.json` (schema `0.2`, 90 tasks / 30 hold-out), `UPSTREAM.md`, and `tasks_catalog.pdf`.
- **Task catalog PDF**: Regenerated from the manifest using `scripts/render_authoring_tasks_catalog_pdf.py` (requires third-party `fpdf2`; not pinned in core `pyproject.toml` dependencies). Run the script after manifest edits to refresh `benchmarks/authoring/tasks_catalog.pdf`.
- **Vendor-neutral prompts (T056-T090)**: Reworded new-task `prompt` text to bench-generic language (no product names; no `protocol.pause`-style API hints). Execution-package contract unchanged: main script is still delivered as `protocol.py` alongside the six JSON/MD files. Legacy `T001-T055` prompts unchanged. Renamed new task `T056` internal tag `legacy_type` from `flex_basic_transfer` to `basic_transfer` so the PDF catalog header stays vendor-neutral.
- **Frozen v0.1 snapshots**: The 2026-05-15 log still records `tasks.v0.1.yaml` / `holdout_manifest.v0.1.json` as the freeze names; they may be absent in a minimal working tree—recover from git history or the revision branch if you need the exact frozen bytes.
- **Contamination reports**: Full-run JSON summaries are produced next to the chosen output prefix by `src/labscriptai/benchmark/contamination_probe.py`; treat them as local evidence artifacts unless explicitly committed.
- **Generated artifacts vs checkout**: Paths named on 2026-05-17 (for example `benchmarks/authoring/contamination_readiness.json`) are tool outputs and may be absent from a minimal clone; re-run the corresponding script to regenerate.
- **Authoring hard35 v2**: Bumped `benchmarks/authoring/tasks.yaml` to schema `0.3` and replaced six soft/redundant hard35 tasks in place: `T056`, `T065`, `T074`, `T076` are trap tasks; `T086`, `T088` are PRE-style package repair tasks. The total task count stays 90 and hard35 remains `T056-T090`.
- **Semantic validator v2 hooks**: Added deterministic checks for task reagent totals, fresh-tip counts, waste route/capacity planning, and module-state wording. Waste capacity is not hard-coded to a robot trash-bin size: liquid waste capacity is checked only when the task asks for a liquid-waste container; generic tip trash/waste-chute handling only needs a declared route.
- **Benchmark runner selection**: `authoring_pilot` now accepts exact comma-separated `--task-ids` so hard35 v2 can be rerun as `T056-T090` without depending on hold-out sampling order.
- **Composite hard35 scoring**: Updated semantic scoring to accept observed package-schema variants for tip and reagent totals, added deterministic dynamic-task `param_sweep` checks, and changed the headline hard35 metric to `task_pass = simulation_ok ∧ validator_ok ∧ semantic_ok ∧ param_sweep_ok`. On the existing `deepseek-v4-flash` hard35 v2 runs, LabscriptAI scores `22/35`, below the pre-set `≤24/35` stop threshold for further task hardening.
- **Composite hard35 live rerun**: Regenerated `T056-T090` with `deepseek-v4-flash` for direct, direct+fix-loop, and LabscriptAI authoring. Composite task pass is direct `4/35`, fix-loop `11/35`, LabscriptAI `17/35`; LabscriptAI remains below the `≤24/35` stop threshold, so no additional hard35 task replacement is needed before stronger-model or external mini-bench runs.
- **External community mini-bench smoke**: Added `benchmarks/external_community/tasks.yaml` with Opentrons Protocol Library, OpenPlant, and PyLabRobot-style tasks. With `deepseek-v4-flash`, direct prompting scores `4/6` composite, direct+fix-loop scores `5/6`, and LabscriptAI authoring scores `6/6`; the final table uses the corrected `EOPEN001` OpenPlant glycerol-stock rerun.

## 2026-05-21

- **Paper deliverable restructure**: Main text = Figure 1 + Table 1 (8 columns, no Sim) + Extended Data Fig (runtime + memory). SI numbered tables reduced to **S1** (scaffold ablation, 90 tasks) + **S2A** (external 66) + **S2B** (LabFlow IR). Old S1–S7 manifest/runtime/capability tables moved to Methods/Data files. See `docs/research/paper_execution_plan.md` §2、§8 and `docs/research/paper_deliverables.md`.
- **Implementation doc sync**: `runtime_build_plan.md` §2.1 aligned with `rollout_12_status.md` (MCP bridge, shadow benchmark, memory MVP, PyLabRobot proof Done). Claim boundary: do not present `56/90` authoring-light as `labscriptai-full` or as runtime/memory evidence.
- **Permission matrix**: P2/P3 shadow updated to 2026-05-21; table IDs now reference Table 1 / S1 / S2B / ExtFig instead of deprecated S2–S7 numbering.
