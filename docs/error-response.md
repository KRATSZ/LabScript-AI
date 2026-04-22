# Error response (canonical)

This file is the **single source of truth** for error categories, default actions, and recovery-branch mapping. MCP and skills link here instead of duplicating tables.

## Error → action → tools

| Error | Action | Tools |
|-------|--------|-------|
| `TIP_PHYSICALLY_MISSING` | Retry with next tip candidate | `recover_tip_pickup` or `execute_protocol_recovery(retry_pick_up_tip_with_next_candidate)` |
| `DESTINATION_OCCUPIED` | Suggest alternatives, **human review required** | `suggest_recovery_action` → `execute_protocol_recovery(suggest_new_destination_slot)` |
| `HARDWARE_FAULT` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `DECK_COLLISION` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `UNKNOWN` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `DESTINATION_UNAVAILABLE` | Treat as occupied | Same as `DESTINATION_OCCUPIED` |
| `PROTOCOL_SETUP_ERROR` | Fix protocol in simulation loop | Back to simulation gate |
| Simulation failure | Fix code, re-simulate | `opentrons-simulation-repair` loop |

## Recovery branches

`execute_protocol_recovery` supports these automatic branches:

1. **`retry_pick_up_tip_with_next_candidate`** — marks failed well, finds next tip, re-enqueues pickUpTip
2. **`suggest_new_destination_slot`** — proposes alternative slot (always human-reviewed)
3. **`wait_and_poll_module_status`** — waits for module blocker to clear, then resumes
4. **`reconcile_state_first`** — reconciles deck state before any further motion

## Phase 2 / Phase 4 recovery policy (frozen invariants)

These rules are implemented in `mcp-servers/opentrons-mcp/` and covered by tests under `mcp-servers/opentrons-mcp/test/`. Historical lab validation notes are archived in `self-iterate-changelog.md`.

### Phase 2 — three rules

1. **`DESTINATION_OCCUPIED`** — In protocol error recovery, destination changes stay **human-reviewed** (`escalate_to_human: true`). Outside recovery, escalation is **off** only when at least one alternative has `confidence: "high"`; unknown/low-confidence slots still escalate. Automatic `moveLabware` fixit only through `execute_protocol_recovery` with an explicit slot.
2. **`is_home_safe`** — `auto_home_allowed` only with **no** robot blockers, **no** tip/cleanup backlog, **no** `needs_reconciliation`.
3. **Hard stops** — `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN`: **no** autonomous continuation; escalate.

### Phase 4 — three pillars

1. Append-only **result logs** for: `run_protocol`, `control_run`, `reconcile_state`, `execute_protocol_recovery`, `recover_tip_pickup`, plus experimental `probe_wells` lines (`probe_preview` / `probe_execution`).
2. **`experiment_history`** query API (filters documented in MCP server README).
3. **`restart_review`** — session file + recent result logs + structured guidance; optional `robot_ip` for live home-safety preview. If `needs_reconciliation`, follow `guidance` and run `reconcile_state` before autonomous motion.

## See also

- Operator restart runbook: [restart-review-runbook.md](restart-review-runbook.md)
- Workflow sequences: [workflows.md](workflows.md)
- Safety policy: [safety-policy.md](safety-policy.md)
