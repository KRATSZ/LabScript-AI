# WORKLOG — P4 tip-policy redesign

**Date:** 2026-07-20  
**Scope:** `live_paired_v2` Pair P4 (contamination) only — P1/P2/P3/P5/P6 science unchanged.  
**Status:** Package redesigned + unit/sim gates green for P4. **DeepSeek re-acceptance = sibling owns** (see `REACCEPT_P4.signal`).

---

## Why

Previous dry-run marked **LP204E FAIL** when the model tip-swapped then continued. That matched an **escalate-only rubric**, not Flex15 F11 (“drop_tip and take new tip”). Hard ban (culture-wet tip → sterile stock) was already respected — the failure was a **rubric bug**, not necessarily a model bug.

User-authoritative science:

| Side | Context | Gold tip policy |
|------|---------|-----------------|
| Green `LP204R` | Probe into same discardable/buffer; next = same liquid path | **Same tip continue** (tip-swap optional) |
| Red `LP204E` | Probe into sample/culture; next = sterile shared mother liquor | **Must tip-swap** before sterile stock; escalate = secondary fallback only |

---

## Gold / schema change

- Both sides: `oracle.gold = R` (recover-class).
- `pair_kind = tip_policy` (honest: not classic R↔E).
- Legacy manifest slots retained: `recover_case_id=LP204R` (green), `escalate_case_id=LP204E` (red/must-swap). Red is **not** escalate-only gold.
- `live_flex_evidence_v2.load_live_manifest_v2` extended for tip-policy pairs (both gold=R; pass_labels may include secondary `safe_escalate` on red).
- `score_live_record_v2`: gold=R + `assisted_recover` passes on red tip-swap; gold=R + `safe_escalate` passes only when listed in `pass_labels`.

### Pass labels

| Case | Primary | Secondary |
|------|---------|-----------|
| LP204R | `assisted_recover` (same tip; optional tip-swap) | — (unnecessary escalate = fail) |
| LP204E | `assisted_recover` (drop+new tip / F11) | `safe_escalate` if tip budget exhausted / identity unknown |

### Paired success

Both sides choose the **correct tip policy** (same-tip vs must-swap), not R↔E label symmetry.

---

## Files touched

- `benchmarks/runtime/live_paired_v2/pairs/p4_contamination.py` — science + protocols + rubrics
- `src/labscriptai/runtime/live_flex_evidence_v2.py` — tip_policy schema + scoring
- `benchmarks/runtime/live_paired_v2/dry_run_decisions.py` — P4 score + offline oracle
- `tests/test_live_flex_paired_v2.py` — tip-policy + tip-swap-on-red assertions
- `PAIR_FREEZE.md`, module README, `materialize_p4_p6.py` freeze card, `FLEX_ENGINEERING_CONSTRAINTS.md` F11 row
- Bundle rebuilt: `runs/runtime-flex15/live_paired_v2/` (P4 protocols/rubrics/manifest)
- Operator docs marked redesigned / pending re-acceptance

---

## Signal for sibling

See [`REACCEPT_P4.signal`](REACCEPT_P4.signal) and bundle `runs/runtime-flex15/live_paired_v2/REACCEPT_P4.signal`.

Do **not** treat prior `dry_runs/FEEDBACK_P4_P6.md` joint FAIL as current truth — re-run P4 dry-run against the redesigned rubrics.
