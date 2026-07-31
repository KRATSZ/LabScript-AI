# Preregistration: V48 contamination housekeeping (TIP_CONTAMINATION_GATE)

**Status:** pre-registered before code change  
**Date:** 2026-07-27  
**Author:** _TBD (strategy-change agent / manuscript track)_  
**Repo branch:** `manuscript`  
**Result name prefix:** `V48_contam_hk_seed_{1..5}.json`

---

## 0. Isolation declaration (mandatory)

Dry-runs completed **before** this preregistration — including but not limited to
`ALL_v47_aligned_deepseek.json`, `R1_rerun_{1,2,3}.json`, `seed_R{1..5}.json`, and
`STABILITY_AGGREGATE_W2.md` — were collected under the **old** v4.7 policy
(missing-tip housekeeping only). They **must not** be used as paper primary
results for any claim that depends on contamination multi-step recovery.

This document freezes a **new** analysis plan. Only runs written under the
`V48_contam_hk_seed_*` naming (or explicitly tagged to this prereg) may support
post-change conclusions.

---

## 1. Motivation

Under v4.7, `run_multistep_shadow_loop_v4_7` treats an approved
`mark_resource_unavailable` as **non-terminal housekeeping** only when the
visible fault is `TIP_PHYSICALLY_MISSING`, then continues for a second decision
(next-tip branch or escalate). `final_action` is the **terminal** step.

`TIP_CONTAMINATION_GATE` (live_paired_v2 P4 / LP204E–LP204R) does **not** get
that continuation. P4 therefore has only a **single** decision step for
mark → tip-swap / escalate chains. That asymmetry is the hypothesized driver of
LP204E instability (~50% in pre-prereg exploratory seeds) while tip-budget (P1)
stabilized after V47 alignment.

This is an explicit **strategy change**, not a post-hoc rescoring of old runs.

---

## 2. Exact strategy change

### 2.1 Scope (code)

- Module: `src/labscriptai/runtime/shadow_feedback_v4_7.py` (and tests /
  prereg-adjacent dry-run harness docs only as needed).
- **Not** changed: pass/fail rubrics, P4 `agent_context` / gold / score_rubric,
  Gatekeeper pass rules, `core/`.
- **Prompt:** keep **`V47_SYSTEM_PROMPT`** / `PROMPT_VERSION=v4.7.1` (no V48
  prompt rewrite in this prereg). Housekeeping semantics change only.

### 2.2 When is an action housekeeping?

| Condition | `action_type` | Housekeeping? |
|-----------|---------------|---------------|
| State shows `TIP_PHYSICALLY_MISSING` (error_signal / error_type / error_leaf / error_category or risk code) | `mark_resource_unavailable` | Yes (existing v4.7) |
| State shows `TIP_CONTAMINATION_GATE` (same signal fields or risk code) | `mark_resource_unavailable` | **Yes (new)** |
| Ordinary tip-clog / other leaves | `mark_resource_unavailable` | Unchanged (may still be pending-verify under clog rules; **not** this contamination chain) |

Housekeeping updates shadow state (commit `resource_id` to
`unavailable_resources`, set `pending_recovery`), appends to
`housekeeping_actions`, and **does not** set `terminal_action_complete`.

### 2.3 What counts as the terminal follow-up?

After contamination housekeeping (`pending_recovery` set):

| Terminal class | Accepted `action_type` / shape |
|----------------|--------------------------------|
| Tip-swap / continue recover | `execute_recovery_branch` with tip-swap / next-tip style branch; or tip-swap shaped `propose_continuation_patch` / `validate_continuation_patch` |
| Escalate | `request_human_confirmation`, `pause_run`, `abort_run` |

`final_action` / `final_decision` = that **terminal** step (not the mark).
Repeated mark of the same resource → `repeated_resource_mark` (incomplete), same
as missing-tip.

Missing-tip terminal rules (`retry_pick_up_tip_with_next_candidate` or
escalate) remain unchanged.

### 2.4 Live inheritance

`live_flex_case_runner.py` already calls `run_multistep_shadow_loop_v4_7`. Live
inherits this change automatically; no separate live branch.

---

## 3. Hypotheses

1. **H1 (primary):** After extending housekeeping to `TIP_CONTAMINATION_GATE`,
   LP204E case-pass rate across ≥5 full seeds rises vs the old single-step
   regime (exploratory baseline ~5/9; not a confirmatory number).
2. **H2 (non-regression):** LP204R and pairs P1–P3, P5–P6 do not regress in
   case-pass or pair-joint rate in a way that offsets H1.
3. **H3 (joint):** Pair-joint P4 and full 6/6 joint rates improve, but **a
   single 6/6 run is never sufficient** to claim paper success.

If after 5 seeds joint stability remains poor, **stop** — do not iterate prompt
or scoring to chase the number. Escalate for human decision.

---

## 4. Analysis plan

| Item | Freeze |
|------|--------|
| Seeds | ≥5 independent full dry-runs, 12 cases each (P1–P6) |
| Model | `deepseek-v4-flash` via `DEEPSEEK_FLASH_MODEL` / `--model deepseek-v4-flash` (`.env` also lists `DEEPSEEK_MODEL=deepseek-v4-pro`; **this prereg uses flash**) |
| Prompt | `V47_SYSTEM_PROMPT` (`PROMPT_VERSION=v4.7.1`) — **not** a new V48 prompt |
| Gate / policy | v4.5 (`evaluate_action_v4_5` / `POLICY_VERSION`) |
| Harness | `run_multistep_shadow_loop_v4_7` (`HARNESS_VERSION=v4.7`) with contamination housekeeping extension; dry-run CLI `benchmarks/runtime/live_paired_v2/dry_run_decisions.py --harness v47` |
| Output dir | `runs/runtime-flex15/live_paired_v2/dry_runs/` |
| Result names | `V48_contam_hk_seed_1.json` … `V48_contam_hk_seed_5.json` |

### Metrics to report (all seeds)

1. **Case pass rate** per case_id (12 cases), especially LP204E / LP204R.
2. **Pair joint pass rate** per pair (6 pairs).
3. **Full 6/6 joint** proportion across seeds (e.g. k/5), **not** as a
   standalone success claim from one seed.
4. Qualitative: whether LP204E terminal actions are tip-swap-shaped vs escalate;
   housekeeping chain presence (`housekeeping_action_types`).

**Do not** conclude from a single 6/6.

---

## 5. Frozen claim boundary

- Development / dry-run only; not autonomous physical evidence.
- No reuse of pre-prereg dry-run aggregates as confirmatory paper results.
- No post-hoc rubric or gold edits to “rescue” P4.
- If H1 fails: report instability honestly; recommend **against** live 12-case
  promotion until a new prereg decides the next strategy.

---

## 6. Suggested reproduce command

```bash
cd /Users/gaoyuan/Documents/test/Flexagent/Opentrons-Lab-Agent
for i in 1 2 3 4 5; do
  PYTHONPATH=.:src .venv/bin/python \
    benchmarks/runtime/live_paired_v2/dry_run_decisions.py \
    --pairs P1 P2 P3 P4 P5 P6 \
    --harness v47 \
    --model deepseek-v4-flash \
    --result-name "V48_contam_hk_seed_${i}.json" \
    --feedback-name "FEEDBACK_V48_contam_hk_seed_${i}.md" \
    --output-dir runs/runtime-flex15/live_paired_v2/dry_runs
done
```

---

## 7. Sign-off

| Role | Name | Date |
|------|------|------|
| Author | _TBD_ | 2026-07-27 |
| Reviewer | _TBD_ | |
