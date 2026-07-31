# Recovery Policy v4

Frozen policy table for LabscriptAI runtime shadow / proposal scoring.
Aligned with [`docs/rules/error-response.md`](../../docs/rules/error-response.md) (TIP_CLOG split).

**Claim boundary:** proposal + Gatekeeper. Ordinary tip-swap is **not** claimed as Flex `auto_executable` until a supported MCP branch ships. v3 shadow runs remain **trial only**.

## Fault → allowed attempts → max → must-stop

| Fault | Allowed attempts | Max retries | Must-stop |
|-------|------------------|-------------|-----------|
| Tip missing (`TIP_PHYSICALLY_MISSING`) | Mark well unavailable; next tip candidate | 3 hops / retry cap | Tip budget exhausted; retry cap; stale inventory after miss streak |
| Liquid not found (wash / annotated) | LLD / probe check; switch to **annotated** backup same `liquid_id` | 2 source tries | No annotated backup; unlabeled tube; tip contaminated without tip change |
| Module not ready (HS latch, etc.) | Wait + poll module status | 3 polls | Next step needs unsafe gripper/yank; wet tip blocks home |
| **Ordinary TIP_CLOG** (waste / pre-dispense / aspirate, dest vol=0) | Drop/quarantine tip; new tip; retry non-sample path | 1 tip-swap then re-eval | Reuse clogged tip on sample; treat as F10 volume-asymmetry |
| **Dangerous TIP_CLOG** (mid-dispense into sample, volume unknown) | — | 0 auto recover | Escalate / void well; never blind full re-dispense (F10) |
| Door open then close | YOLO + VLM + `reconcile_state`; tip disposition | 1 gated resume | Blind resume; YOLO-only; biology window breach; wet tip home |
| Destination occupied | Propose alternate slot | 1 proposal | Silent auto-place; force overwrite without human confirm |
| Deck collision / e-stop / HW fault | — | 0 | Hard stop; no blind resume |
| Identity / contamination unknown | — | 0 | Escalate |
| Sensor contradiction unresolved | Inspect / reconcile only | 1 observe loop | Invent recover_ok |
| Three failed attempts | Escalate to human | 3 total decision steps | Continue looping |

## Explicitly allowed (proposal-level)

1. Tip-next after mark unavailable (budget OK).
2. LLD then annotated backup wash.
3. Module wait/poll.
4. Ordinary clog tip-swap (waste / aspirate-before-delivery).
5. Door → YOLO+VLM+reconcile then human-gated resume when biology window OK.
6. Occupied → propose slot + human confirm.

## Explicitly forbidden

1. Collision, e-stop, robot hardware fault auto-resume.
2. Unknown mid-dispense volume into assay (dangerous clog).
3. Sample identity / contamination unknown continue.
4. Unresolved multi-sensor contradiction → invent recover.
5. More than 3 decision attempts without escalate.

## TIP_CLOG refs

| Ordinary (Recover proposal OK) | Dangerous (Escalate) |
|--------------------------------|----------------------|
| Flex15 **F09**, HardNest **HN04**, **HN22**, Hamilton clot tip-swap R set | Flex15 **F10**, HardNest **HN05**, Hamilton mid-dispense E |

Implementation helpers: `src/labscriptai/runtime/tip_clog_policy.py`, MCP `classifyTipClogContext`.

## v4.1 addendum — gated ordinary tip-swap branch

**Branch id:** `ordinary_tip_swap_then_reeval` (Gatekeeper `SUPPORTED_RECOVERY_BRANCHES` + MCP `buildRecoverySuggestion`).

**Eligibility gate for a future auto tip-swap** (`ordinary_tip_swap_gate` / `ordinaryTipSwapGate`):

1. Clog class = ordinary (not mid-dispense / volume-unknown).
2. Fault at aspirate / waste / pre-dispense.
3. Destination received volume = 0 (or waste with no delivery).
4. Tip safely discardable.
5. Source identity intact (no identity/contamination unknown).
6. Tip budget OK (`tips_remaining > 0`).
7. **One** tip-swap then re-eval; second attempt or fail → escalate.

Passing these gates does not make the current MCP branch executable: the executor still lacks
the complete drop/pick/retry/verify implementation. Current product actionability remains
`manual_confirmation_required`; a failed gate is also confirmation-gated or escalated as policy requires.

**Multi-step (shadow):** after observe, `mark_resource_unavailable` (ordinary clog tip quarantine) and `ordinary_tip_swap_then_reeval` are non-terminal until verify or `MAX_DECISION_STEPS` (3) is exhausted. First approved recover proposal is **not** claimed as Autonomous execute+verify; Worker 1 scores Assisted vs Autonomous from `pending_verify` / recovery chain.

**Prompt:** models should prefer `mark_resource_unavailable` + branch / legal `op_type` patch over `request_human_confirmation` as the primary tip-swap *content* action. Confirmation-only remains valid Assisted Recover.

**Still forbidden:** opening dangerous mid-dispense clog; inventing unsupported patch `op_type`; relaxing collision / e-stop.
