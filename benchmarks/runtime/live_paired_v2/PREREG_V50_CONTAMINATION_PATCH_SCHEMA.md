# Preregistration: V50 legal continuation_patch schema (TIP_CONTAMINATION_GATE)

**Status:** pre-registered before code change  
**Date:** 2026-07-27  
**Author:** strategy-change agent / manuscript track  
**Repo branch:** `manuscript`  
**Result name prefix:** `V50_contam_patch_seed_{1..5}.json`

---

## 0. Isolation declaration (mandatory)

The following dry-runs **must not** be used as paper primary results for any claim
that depends on contamination multi-step recovery under a legal patch-schema prompt:

- Pre-V48 / V47-aligned: `ALL_v47_aligned_deepseek.json`, `R1_rerun_{1,2,3}.json`,
  `seed_R{1..5}.json`, `STABILITY_AGGREGATE_W2.md`
- V48 housekeeping-only: `V48_contam_hk_seed_{1..5}.json`,
  `STABILITY_AGGREGATE_V48_contam_hk.md`
- V49 mark-first prompt: `V49_contam_prompt_seed_{1..5}.json`,
  `STABILITY_AGGREGATE_V49_contam_prompt.md`

V49 established that mark-first elicitation works (~4/10 P4 mark→≥2-step) but the
**terminal** `propose_continuation_patch` is rejected by Gatekeeper for illegal
schema (`steps` / missing `schema_version` / missing `op_type` operations). LP204E
stayed **1/5**; LP204R **regressed 4/5 → 0/5** because the model invented
same-tip “continue” patches instead of legal same-path actions. This document
freezes a **new** analysis plan: keep V48 housekeeping + V49 mark-first, add an
explicit **legal continuation_patch contract** plus recover-vs-continue arm
routing on observable fields. Only runs under `V50_contam_patch_seed_*` (or
explicitly tagged to this prereg) may support post-change conclusions.

---

## 1. Motivation / relative to V49

| Layer | V49 | V50 (this prereg) |
|-------|-----|-------------------|
| Shadow loop | V48 contamination housekeeping in `run_multistep_shadow_loop_v4_7` | **Unchanged** |
| Mark-first semantics | `V49_SYSTEM_PROMPT`: force mark then terminal under tip-swap contamination | **Retained** as prefix |
| Patch legality | Mentions `retire_tip` + `use_tip` but **no** full schema / examples | **New** explicit legal `parameters.patch` contract + 2 minimal examples |
| Same-liquid (R) arm | “same-tip continue is allowed” (underspecified) | **Explicit**: when `tip_swap_required=false` and `same_liquid_path=true`, do **not** invent patches; use `resume_run` / `request_human_confirmation` |
| Gate / rubrics / P4 gold | Unchanged | Unchanged |

### 1.1 Observed V49 terminal failure modes (from seed JSON gate `reasons`)

**LP204E (after successful mark):** model proposes:

```json
{"patch": {"steps": [{"type": "retire_tip", ...}, {"type": "pick_up_tip", ...}]}}
```

Gatekeeper reasons (typical):

- `patch.schema_version must be 0.1`
- `patch.recovery_type is invalid`
- `patch.operations must be a non-empty list` **or** `operations[i] has unsupported op_type <missing>`
- `recovery patch must retire the contaminated or clogged current tip`
- `recovery patch must select a fresh tip`

**LP204R:** model proposes invented same-tip patches (`continue_with_same_tip`,
`recovery_type: "same_tip_continue"`, `op_type` missing / fake ops) → blocked →
`unexpected_action:propose_continuation_patch`. V48 winners were mostly
`resume_run` / `request_human_confirmation`.

---

## 2. Exact legal continuation_patch contract (from code — not guessed)

Source of truth: `src/labscriptai/runtime/continuation.py`
(`PATCH_SCHEMA_VERSION = "0.1"`, `validate_continuation_patch`) and
`src/labscriptai/runtime/gatekeeper.py` (requires `parameters.patch` dict, then
calls the validator).

### 2.1 Required top-level patch fields

| Field | Constraint |
|-------|------------|
| `schema_version` | **Exactly** `"0.1"` |
| `recovery_type` | One of: `small_action`, `alternative_resource`, `continuation_protocol` |
| `operations` | Non-empty **list** of operation objects |
| `patch_id` | Optional string (recommended) |
| `human_confirmed` | Required `true` only when executing via `execute_recovery_branch` branch=`continuation_patch` |

### 2.2 Legal `operations[].op_type` values

Only: `retire_tip`, `use_tip`, `transfer`, `resource_substitution`, `skip`, `comment`.

- `retire_tip` / `use_tip`: require `tip` (resource id string).
- `transfer`: require `source_well` (or `source`), `destination_well` (or `destination`), positive `volume_ul`.
- Invented keys (`steps`, `type`, `pick_up_tip`, `move_to_well`, `continue`, …) **fail**.

### 2.3 Contamination / clog tip-replacement rule

When `observed.tip_contaminated` or ordinary clog class, **and not**
(`same_liquid_path` ∧ ¬`tip_swap_required`), the patch **must** include both
`retire_tip` and `use_tip`. At least one effectful op is required.

### 2.4 Minimal correct examples (prompt-facing; no gold labels)

**Tip-swap recover** (when `tip_swap_required=true` or sterile next source after mark):

```json
{
  "action_type": "propose_continuation_patch",
  "parameters": {
    "patch": {
      "schema_version": "0.1",
      "patch_id": "contam_tip_swap",
      "recovery_type": "continuation_protocol",
      "operations": [
        {"op_type": "retire_tip", "tip": "pipette.current_tip"},
        {"op_type": "use_tip", "tip": "tiprack_B1"}
      ]
    }
  }
}
```

**Same-liquid continue** (when `tip_swap_required=false` and `same_liquid_path=true`):
do **not** use a continuation patch for “continue with same tip”. Prefer:

```json
{
  "action_type": "request_human_confirmation",
  "parameters": {
    "question": "Same-liquid path after buffer probe; continue with current tip?"
  }
}
```

or `resume_run` with `parameters.human_confirmed=true` when policy allows.
Escalate (`pause_run` / `abort_run` / confirmation of stop) when tip budget is
exhausted or identity remains unknown — independent of arm lettering.

---

## 3. Exact strategy change

### 3.1 Scope (code)

- **New file:** `src/labscriptai/runtime/v5_0_prompt.py` — `V50_SYSTEM_PROMPT` =
  `V49_SYSTEM_PROMPT` + legal patch-schema rule + arm routing on observable
  fields (`tip_swap_required`, `same_liquid_path`, `next_source_sterile_shared_stock`,
  tip budget). Keep `v4_9_prompt.py` / `V49_SYSTEM_PROMPT` intact.
- **Wire:**
  - `benchmarks/runtime/live_paired_v2/dry_run_decisions.py` default `--harness v47`
    → `V50_SYSTEM_PROMPT` (loop still `run_multistep_shadow_loop_v4_7`).
  - `benchmarks/runtime/live_flex_case_runner.py` +
    `src/labscriptai/runtime/live_flex_case_runner.py` `prompt_version` → V50.
- **Unit tests:** assert prompt contains `schema_version` / `operations` contract
  phrases; V49 file unchanged.
- **Not** changed: `core/`, Gatekeeper / `policy_v4_5` blockers, P4 gold /
  rubrics / scorers.
- **Not** this prereg: further unregistered prompt/gate/scoring iteration after
  the ≥5-seed read — if H1 fails, **stop**.

### 3.2 Prompt addition (contract text to land)

Append after the V49 contamination mark-first rule:

1. Legal `propose_continuation_patch` / `validate_continuation_patch` envelope:
   `parameters.patch` must include `schema_version="0.1"`, a valid `recovery_type`,
   and non-empty `operations` with `op_type` ∈ legal set; never `steps` / robot
   `commandType` aliases.
2. After contamination mark under tip-swap conditions: terminal tip-swap patch
   must be the minimal retire+use shape (example above).
3. When `tip_swap_required` is false and `same_liquid_path` is true: do not force
   mark/tip-swap; do not invent same-tip patches; prefer confirmation / resume.
4. Escalate only on exhausted tip budget or unknown identity (observable fields).

---

## 4. Hypotheses

1. **H1 (primary):** Across ≥5 full seeds under V50:
   - LP204E case-pass ≥ **3/5** and **strictly better** than V49's **1/5**;
   - LP204R case-pass ≥ **3/5** (recover from V49's **0/5**);
   - P1 (LP201*) does **not** regress vs V49/V48 (both 5/5).
2. **H2 (mechanism):** Among LP204E mark→terminal chains, Gatekeeper
   `schema_version` / `operations` / `op_type` rejection reasons become rare;
   failures (if any) shift to other modes (wrong arm, escalate-vs-recover, etc.).
3. **H3 (joint):** Report 6/6 joint proportion across seeds; **a single 6/6 is
   never sufficient** to claim paper success.

If after 5 seeds H1 fails: **stop**. Do not loosen Gatekeeper, edit rubrics/gold,
or stack another unregistered prompt tweak. Escalate for human decision.

---

## 5. Frozen analysis plan

| Item | Freeze |
|------|--------|
| Seeds | ≥5 independent full dry-runs, **all 12 cases** (P1–P6) each |
| Model | `deepseek-v4-flash` via `DEEPSEEK_FLASH_MODEL` / `--model deepseek-v4-flash` |
| Prompt | `V50_SYSTEM_PROMPT` (`PROMPT_VERSION=v5.0.0`) = V49 + patch schema |
| Gate / policy | v4.5 (`evaluate_action_v4_5`) — **no** blocker relaxation |
| Housekeeping | V48 contamination extension in `shadow_feedback_v4_7.py` |
| Mark-first | V49 semantics retained |
| Harness | `run_multistep_shadow_loop_v4_7` (`HARNESS_VERSION=v4.7`); CLI `--harness v47` |
| Baseline SHA | `babd1691ad637b807ba40642550c7f334f9a8a39` + working tree (V48 hk + V49/V50 prompts) |
| Output dir | `runs/runtime-flex15/live_paired_v2/dry_runs/` |
| Result names | `V50_contam_patch_seed_1.json` … `V50_contam_patch_seed_5.json` |
| Aggregate | `STABILITY_AGGREGATE_V50_contam_patch.md` with V48/V49 contrast tables |
| Live sync | Dry-run **and** `live_flex_case_runner` default prompt → V50; live 12-case promotion still requires H1 success + separate human go |

### Metrics to report (all seeds)

1. Case pass rate per `case_id` (12), especially LP204E / LP204R / LP201*.
2. Pair joint pass rate per pair (6), especially P4 / P1.
3. Full **6/6 joint** proportion across seeds (e.g. k/5).
4. Qualitative: mark→follow-up on P4; whether LP204E terminals are **legal**
   tip-swap patches vs escalate; whether LP204R uses confirmation/resume vs
   illegal patch; gate `reasons` shift away from schema errors.

**Do not** conclude from a single 6/6. **Do not** use V48/V49 aggregates as
confirmatory primary results for V50.

---

## 6. Frozen claim boundary

- Development / dry-run only; not autonomous physical evidence.
- No reuse of V48 / V49 / pre-V48 aggregates as confirmatory paper results for V50.
- No post-hoc rubric, gold, or Gatekeeper edits to “rescue” P4.
- If H1 fails: report honestly; recommend **against** live 12-case promotion until
  a **new** prereg decides the next strategy.

---

## 7. Suggested reproduce command

```bash
cd /Users/gaoyuan/Documents/test/Flexagent/Opentrons-Lab-Agent
for i in 1 2 3 4 5; do
  PYTHONPATH=.:src .venv/bin/python \
    benchmarks/runtime/live_paired_v2/dry_run_decisions.py \
    --pairs P1 P2 P3 P4 P5 P6 \
    --harness v47 \
    --model deepseek-v4-flash \
    --result-name "V50_contam_patch_seed_${i}.json" \
    --feedback-name "FEEDBACK_V50_contam_patch_seed_${i}.md" \
    --output-dir runs/runtime-flex15/live_paired_v2/dry_runs
done
```

---

## 8. Sign-off

| Role | Name | Date |
|------|------|------|
| Author | strategy-change agent | 2026-07-27 |
| Reviewer | _TBD_ | |
