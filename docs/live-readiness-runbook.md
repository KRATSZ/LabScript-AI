# Live readiness runbook (`live_readiness_check`)

Use this before `create_run` or `play` when you want a **read-only** go/no-go gate for a Flex robot.

## What it checks

`live_readiness_check` combines:

1. `health_check` style local runtime inspection
2. persisted session/restart guidance
3. live `robot_status`
4. live `module_status`
5. `is_home_safe`-style cleanup/home blockers
6. optional `preflight_run_setup` when `file_path` is provided

## Recommended staged validation

1. **Stage 1 — read-only gate**
   Call `live_readiness_check(robot_ip, session_id?, file_path?)`.
2. **Stage 2 — create-run smoke test**
   Only if stage 1 has no blocking failures, upload the canary or target protocol and `create_run` without play.
3. **Stage 3 — minimal live canary**
   Only after stage 2 succeeds and the operator confirms, run the smallest safe Flex noop/smoke protocol.

## Interpreting results

- `overall_status: pass` means the read-only gate found no blocking issues.
- `overall_status: warn` means play may still be possible, but an operator should review the warnings first.
- `overall_status: fail` means do not create or play a run yet.

Always inspect:

- `checks[]` for per-check `pass|warn|fail`
- `blocking_reasons[]` for the immediate blockers
- `recommended_next_tools[]` for the next MCP calls

## Common outcomes

- `RUNTIME_UNAVAILABLE` or `PYTHON_ENV_BROKEN`
  Fix the local runtime before any live attempt.
- `SESSION_NEEDS_RECONCILIATION`
  Run `reconcile_state` before autonomous motion.
- `ROBOT_UNREACHABLE`
  Fix LAN / base URL / robot power before continuing.
- `MODULE_NOT_READY`
  Wait or manually resolve the module state first.
- `LABWARE_MISMATCH` / `SLOT_NOT_ADDRESSABLE`
  Treat the physical deck or protocol declaration as untrusted until confirmed.

## Scope note

Current readiness rollout is **Flex-first**. OT-2 deck-diff support is still not modeled by `preflight_run_setup` in this build.
