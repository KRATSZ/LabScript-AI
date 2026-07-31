# Preregistration: V49 contamination mark-first prompt (TIP_CONTAMINATION_GATE)

**Status:** pre-registered before code change  
**Date:** 2026-07-27  
**Author:** strategy-change agent / manuscript track  
**Repo branch:** `manuscript`  
**Result name prefix:** `V49_contam_prompt_seed_{1..5}.json`

---

## 0. Isolation declaration (mandatory)

The following dry-runs **must not** be used as paper primary results for any claim
that depends on contamination multi-step recovery under a mark-first prompt:

- Pre-V48 / V47-aligned: `ALL_v47_aligned_deepseek.json`, `R1_rerun_{1,2,3}.json`,
  `seed_R{1..5}.json`, `STABILITY_AGGREGATE_W2.md`
- V48 housekeeping-only (no prompt change): `V48_contam_hk_seed_{1..5}.json`,
  `STABILITY_AGGREGATE_V48_contam_hk.md`

V48 established that extending shadow-loop housekeeping alone does **not**
elicit mark→terminal under `deepseek-v4-flash` + `V47_SYSTEM_PROMPT`
(P4 mark→follow-up = 0/10; LP204E = 1/5; 6/6 joint = 0/5). This document freezes
a **new** analysis plan for a prompt strategy change on top of that already-landed
housekeeping code. Only runs written under the `V49_contam_prompt_seed_*` naming
(or explicitly tagged to this prereg) may support post-change conclusions.

---

## 1. Motivation / relative to V48

| Layer | V48 | V49 (this prereg) |
|-------|-----|-------------------|
| Shadow loop | Extend `run_multistep_shadow_loop_v4_7` so `mark_resource_unavailable` under `TIP_CONTAMINATION_GATE` is non-terminal housekeeping (same as missing-tip) | **Unchanged** — keep V48 housekeeping |
| Prompt | Keep `V47_SYSTEM_PROMPT` (`PROMPT_VERSION=v4.7.1`) — **no** contamination two-step text | **New** `V49_SYSTEM_PROMPT` (`PROMPT_VERSION=v4.9.0`): force/guide mark-then-terminal under contamination tip-swap |
| Gate / rubrics / P4 gold | Unchanged | Unchanged (option B / scoring edits out of scope) |

Root cause from V48: the model almost never proposes `mark_resource_unavailable`
first; it jumps to `execute_recovery_branch` (`ordinary_tip_swap_then_reeval`),
which Gatekeeper blocks with `blocker risks must be resolved first: TIP_CONTAMINATION_GATE`.
Housekeeping code is never entered. Prompt guidance is the hypothesized fix.

---

## 2. Exact strategy change

### 2.1 Scope (code)

- **New file:** `src/labscriptai/runtime/v4_9_prompt.py` — `V49_SYSTEM_PROMPT` =
  `V47_SYSTEM_PROMPT` + contamination mark-first rule (V47 file left intact for
  contrast / other holdouts).
- **Wire (this prereg path only, but sync live):**
  - `benchmarks/runtime/live_paired_v2/dry_run_decisions.py` default `--harness v47`
    path uses `V49_SYSTEM_PROMPT` (harness loop still `run_multistep_shadow_loop_v4_7`).
  - `benchmarks/runtime/live_flex_case_runner.py` and live metadata
    (`src/labscriptai/runtime/live_flex_case_runner.py` `prompt_version`) sync to V49.
- **Not** changed: `core/`, Gatekeeper pass rules / blocker severity, P4
  `agent_context` / gold / `score_rubric`, scoring helpers (no score-to-pass).
- **Not** this prereg: further silent prompt/gate/scoring iteration after the
  ≥5-seed read — if H1 fails, **stop**.

### 2.2 Prompt rule draft (exact text to land)

Appended / injected as a peer of the existing TIP_PHYSICALLY_MISSING two-step rule:

```
- TIP_CONTAMINATION_GATE with tip_swap_required or next_source_sterile_shared_stock
  is a two-step decision when the contaminated tip is not already listed in
  committed.unavailable_resources. First return mark_resource_unavailable with
  parameters.resource_id equal to pipette.current_tip (or observed contaminated tip
  id). This is housekeeping, not a terminal recovery; never repeat the same mark.
  Do not use a single-step execute_recovery_branch tip-swap (including
  ordinary_tip_swap_then_reeval) as the first action under this gate — Gatekeeper
  will block it while the contamination blocker remains. On the next decision,
  prefer propose_continuation_patch or validate_continuation_patch with retire_tip
  + use_tip before the sterile source, or escalate with request_human_confirmation /
  pause_run / abort_run when tip budget is exhausted or identity remains unknown.
  TIP_CONTAMINATION_GATE is not ordinary TIP_CLOG. When tip_swap_required is false
  and same_liquid_path is true (non-sterile / same discardable buffer path), do not
  force mark or tip-swap; same-tip continue is allowed.
```

### 2.3 Terminal follow-up (unchanged housekeeping contract)

After contamination housekeeping (`pending_recovery=contamination_terminal_action`):

| Terminal class | Accepted shape |
|----------------|----------------|
| Tip-swap recover | `propose_continuation_patch` / `validate_continuation_patch` tip-swap; or tip-swap-shaped approved branch if gate allows |
| Escalate | `request_human_confirmation`, `pause_run`, `abort_run` |

`final_action` = that **terminal** step (not the mark).

---

## 3. Hypotheses

1. **H1 (primary):** Across ≥5 full seeds under V49, LP204E case-pass rate is
   **significantly higher** than V48's **1/5**, and P4 pair-joint improves vs
   V48's **1/5**, **without** LP204R or P1 (LP201*) regressing relative to V48
   (V48: LP204R 4/5, P1 joint 5/5).
2. **H2 (mechanism):** P4 cases show non-zero mark→terminal housekeeping chains
   (contrast V48's **0/10**).
3. **H3 (joint):** Full 6/6 joint proportion across seeds is reported; **a single
   6/6 is never sufficient** to claim paper success.

If after 5 seeds H1 fails or joint remains poor: **stop**. Do not loosen
Gatekeeper blockers, edit rubrics/gold, or stack another unregistered prompt
tweak in this round. Escalate for human decision (option B / other).

---

## 4. Frozen analysis plan

| Item | Freeze |
|------|--------|
| Seeds | ≥5 independent full dry-runs, **all 12 cases** (P1–P6) each |
| Model | `deepseek-v4-flash` via `DEEPSEEK_FLASH_MODEL` / `--model deepseek-v4-flash` (unless a live manifest later overrides for physical runs; this dry-run prereg uses flash) |
| Prompt | `V49_SYSTEM_PROMPT` (`PROMPT_VERSION=v4.9.0`) |
| Gate / policy | v4.5 (`evaluate_action_v4_5` / `POLICY_VERSION`) — **no** blocker relaxation |
| Housekeeping | V48 contamination extension already in `shadow_feedback_v4_7.py` |
| Harness | `run_multistep_shadow_loop_v4_7` (`HARNESS_VERSION=v4.7`); CLI `--harness v47` |
| Baseline SHA | `babd1691ad637b807ba40642550c7f334f9a8a39` + working tree containing V48 housekeeping diff |
| Output dir | `runs/runtime-flex15/live_paired_v2/dry_runs/` |
| Result names | `V49_contam_prompt_seed_1.json` … `V49_contam_prompt_seed_5.json` |
| Live sync | Dry-run **and** `live_flex_case_runner` default prompt → V49 (documented here; live 12-case promotion still requires H1 success + separate human go) |

### Metrics to report (all seeds)

1. Case pass rate per `case_id` (12), especially LP204E / LP204R / LP201*.
2. Pair joint pass rate per pair (6), especially P4 / P1.
3. Full **6/6 joint** proportion across seeds (e.g. k/5) — not a one-seed claim.
4. Qualitative: `housekeeping_action_types` / mark→follow-up presence on P4;
   whether LP204E terminals are tip-swap-shaped vs escalate.

**Do not** conclude from a single 6/6. **Do not** use V48 or earlier aggregates as
confirmatory primary results.

---

## 5. Frozen claim boundary

- Development / dry-run only; not autonomous physical evidence.
- No reuse of V48 / pre-V48 aggregates as confirmatory paper results for V49.
- No post-hoc rubric, gold, or Gatekeeper edits to “rescue” P4.
- If H1 fails: report honestly; recommend **against** live 12-case promotion until
  a **new** prereg decides the next strategy.

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
    --result-name "V49_contam_prompt_seed_${i}.json" \
    --feedback-name "FEEDBACK_V49_contam_prompt_seed_${i}.md" \
    --output-dir runs/runtime-flex15/live_paired_v2/dry_runs
done
```

---

## 7. Sign-off

| Role | Name | Date |
|------|------|------|
| Author | strategy-change agent | 2026-07-27 |
| Reviewer | _TBD_ | |
