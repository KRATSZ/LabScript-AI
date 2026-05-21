# Authoring Failure Audit

This audit summarizes the main failure modes from the 90-task `LabscriptAI authoring` run:

- Run summary: `runs/authoring-pilot/labscriptai-authoring/90-flash-v1/summary.json`
- Analysis summary: `runs/authoring-pilot/labscriptai-authoring/90-flash-v1-analysis/attribution-summary.json`
- Reviewer summary: `runs/authoring-pilot/labscriptai-authoring/90-flash-v1-review-v4pro/review-summary.json`

## Hard Failures

| Task | Difficulty | Simulation | Validator | Attempts | Repair attempts | Main failure | Initial reading |
|---|---|---:|---:|---:|---:|---|---|
| T020 | Medium | Fail | Fail | 4 | 3 | `OutOfTipsError` | Real agent planning failure: tip budget strategy did not match protocol behavior. |
| T027 | Medium | Fail | Fail | 4 | 3 | `TypeError: 'Parameters' object is not subscriptable` | Code/API mistake: parameter access style is wrong for the target Opentrons API. |
| T042 | Hard | Fail | Fail | 4 | 3 | `PipetteMovementRestrictedByHeaterShakerError` | Module-state planning failure: Heater-Shaker latch/state sequencing is not enforced correctly. |
| T073 | Hard | Fail | Fail | 4 | 3 | `IndexError: list index out of range` | Code/data-shape mistake: generated list indexing is not robust to the task layout. |
| T079 | Hard | Fail | Fail | 4 | 3 | `ValueError: target_volume_uL '' is not a positive number` | Input-validation/default-data mistake: fallback CSV contains an empty required volume. |
| T063 | Medium | Pass | Fail | 1 | 0 | `schema_invalid` / `json_parse_error` | Package-quality failure: protocol simulates, but at least one required JSON artifact is malformed. |

## Semantic Validator Flags

These tasks passed the main benchmark path but were flagged by the deterministic semantic analyzer:

| Task | Simulation | Validator | Semantic issue | Reading |
|---|---:|---:|---|---|
| T004 | Pass | Pass | `prompt_volume_missing` | Likely task/spec ambiguity or insufficient explicit volume extraction. |
| T067 | Pass | Pass | `missing_positive_control` | Possible biological-planning gap; inspect package before using as a clean pass. |
| T080 | Pass | Pass | `tip_quantity_missing` | Package metadata underreports tip usage even though the protocol simulates. |

## Reviewer Low-Score Cluster

DeepSeek Pro reviewer scores below 3.5/5 cluster around practical lab issues:

| Cluster | Example tasks | Common issue |
|---|---|---|
| Tip planning and cross-contamination | T007, T020, T023, T037, T041, T045, T052, T080, T083 | Single-tip reuse, too few loaded tips, or mismatch between tip plan and protocol. |
| Waste and capacity planning | T007, T020, T037, T041 | Reservoir or waste well capacity is too small for the planned run. |
| Module state and movement constraints | T042, T083 | Heater-Shaker / magnetic-module states are represented as pauses or assumptions instead of executable safeguards. |
| Dynamic calculation / input validation | T027, T069, T073, T079 | Parameter access, molar-ratio math, concentration normalization, or CSV default validation fails. |
| Package metadata quality | T063, T080 | JSON artifacts or runbook metadata are malformed or incomplete even when code is runnable. |

## Next Hardening Targets

1. Add a targeted pre-simulation check for tip budget consistency between `tip_plan.json` and `protocol.py`.
2. Add module-state rules for Heater-Shaker latch handling and magnetic-module safe movement.
3. Add schema recovery for malformed required JSON artifacts, not only `protocol.py` repair.
4. Extend semantic validator checks for controls, waste capacity, and single-tip reuse across biologically distinct wells.
5. Keep T020, T027, T042, T073, T079, and T063 as a small regression set after each authoring-agent change.
