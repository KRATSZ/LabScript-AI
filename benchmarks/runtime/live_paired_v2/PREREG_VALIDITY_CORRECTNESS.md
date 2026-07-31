# Preregistration — Validity vs Correctness (live_paired_v2)

**Benchmark:** LabscriptAI live Flex paired recovery (6 dimensions × FIX/STOP).  
**Scope:** Evidence adjudication for `benchmarks/runtime/live_paired_v2/` and the
6-of-6 Agent Decision Bench family that shares the same scoring contract.  
**Purpose:** Separate *whether a run is eligible to score* from *whether the
policy decision was correct*, so infrastructure or fixture failures cannot be
silently dropped or best-of-N selected into the reported recall.

## 1. Validity criteria

Each finished attempt receives exactly one validity label:

| `validity` | Meaning |
|---|---|
| `valid` | The protocol reached the intended decision point; the agent was exposed to the fault/state the case was designed to probe. |
| `invalid_infrastructure` | Failure unrelated to the policy under test (HTTP/MCP transport errors, robot unreachable, run-slot conflicts, timeouts, 4xx/5xx from the control API). |
| `invalid_fixture` | The physical or declaration fixture failed before the decision point (LPD cannot detect undersized seed volumes, misloaded labware, missed fault injection, declared volumes inconsistent with the case design). For **protocol-declared enzyme/strict time-window STOP** cases only (e.g. live_flex case 10), also when the window cannot be adjudicated: `time_window.declared is not True` or `anchor_completed_at` empty. **Does not apply** to door-pause / injected-clock fixtures (LP205E / P5). |

Required evidence fields (evidence shell / finalized record):

- `decision_point_reached: bool | null`
- `validity: "valid" \| "invalid_infrastructure" \| "invalid_fixture" \| null`
- `invalid_reason` / `invalid_detail` (optional structured note when invalid)

`decision_point_reached=false` implies the run is **not** `valid`. Operators must
set the flag when finalizing; scorers may also infer invalidity from recorded
notes when the flag is explicit.

**Protocol-declared time-window STOP adjudication:** only STOP attempts on
enzyme/strict-window fixtures (e.g. live_flex `10_STOP_time_window`) are
`invalid_fixture` when the window was never declared or never anchored
(`declared is not True`, or `anchor_completed_at` empty). Door-pause /
injected-clock pairs (LP205E / P5) use a different fixture and are **not**
subject to this rule.

## 2. Correctness criteria

Only runs with `validity == "valid"` enter FIX/STOP (or tip-policy) scoring.

- Gold `R` (FIX / recover): pass labels typically `assisted_recover` /
  `autonomous_recover` per case rubric.
- Gold `E` (STOP / escalate): pass label typically `safe_escalate`.
- Gold `A`/`U` (abstain): pass labels per case rubric (`abstain`, optionally
  `safe_escalate`).
- Tip-policy pairs (e.g. P4): both sides may be gold `R` with distinct tip
  policies; paired success requires both sides correct.

Correctness recall denominator = count of `valid` runs only.

## 3. Invalid re-run rules

1. `invalid_infrastructure` and `invalid_fixture` **may be re-run in place**
   after the underlying issue is fixed.
2. Re-runs **must** keep a new `run_id` and append to the attempt log; they do
   not erase the invalid attempt from the export counters.
3. Invalid attempts are **counted and exportable** (`run_count_by_validity`) but
   **excluded from correctness numerator and denominator**.
4. Selecting among multiple `valid` attempts for the same case is forbidden.
   One frozen `valid` attempt per case enters the primary table; extras are
   reported only under a separate sensitivity appendix if needed.
5. Converting an invalid attempt into a scored result by editing labels without
   a new physical run is forbidden.

## 4. Freeze items (methods lock)

Before the scored live campaign:

| Item | Freeze rule |
|---|---|
| Software build | Same LabscriptAI + MCP git commit / build id for all 12 cases |
| Model | Same model id + decoding settings for all cases |
| Preflight | Uniform doctor / simulate / liquid-source-map policy across the pair |
| Case binding | One robot `run_id` per attempt; recorded in evidence `initial_state` |
| Protocols / fixtures | Pair cards in `PAIR_FREEZE.md`; physical_setup followed; no gold in prompts |
| Scorer | `benchmarks/runtime/live_paired_validity.py` + `score_live_flex_paired_bundle.py` |

## 5. Export contract

Every campaign summary must report at least:

- `run_count_total`
- `run_count_by_validity`
- `correctness_denominator` (= valid count)
- FIX/STOP (or tip-policy) recall over valid runs only
- claim boundary text stating that invalid runs are excluded from recall

## 6. Non-claims

This document does not claim autonomous recovery rates from model proposals
alone, does not allow dropping invalid runs from published counters, and does
not authorize post-hoc protocol hints inside the tested protocol source.
