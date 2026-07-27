# Recovery playbooks (skill)

Live recovery path: `robot(op=status)` (embeds `parse_error` + `suggest_recovery` when `run_id` set) → operator/gate → `robot(op=act)` with `recovery_branch`.

## Executable branches (`execute_protocol_recovery`)

1. **`retry_pick_up_tip_with_next_candidate`** — `TIP_PHYSICALLY_MISSING`; L0; same tiprack / next well.
2. **`suggest_new_destination_slot`** — `DESTINATION_OCCUPIED`; human-reviewed `destination_slot` required.
3. **`wait_and_poll_module_status`** — `MODULE_NOT_READY`; poll until ready then resume.
4. **`reconcile_state_first`** — module-blocker-only session diffs; reconcile before motion.

## Manual-only (do not auto-act)

`INSUFFICIENT_VOLUME`, `AIR_BUBBLE`, `LIQUID_PROPERTY_ERROR`, `DECK_COLLISION`, `UNKNOWN_NEEDS_HUMAN`, dangerous `TIP_CLOG`, `DESTINATION_OCCUPIED` outside awaiting-recovery.

## Watch loop

- `robot(op=watch)` → `runtime_watch_poll` (needs `run_id`) or `runtime_get_outbox`; degrades to status.
- Only L0 whitelist branches may auto-execute inside watch; `needs_user` / hard stop → BLOCKED.

## Act args (passthrough)

Common: `run_id`, `robot_ip`, `recovery_branch`, `session_id`, `recovery_well`, `tiprack_slot`, `destination_slot`, `idempotency_key`, `timeout_ms`.

Or set `action` to a specific MCP control tool name (e.g. pause/play helpers) instead of recovery.

## Invariants

- Simulation gate blocks unattended live play after failed sim/doctor.
- Reconciliation beats history when `needs_reconciliation`.
- Result logs / experiment history are audit-only — not deck truth.
