# Error Response Table

| Error | Action | Tools |
|-------|--------|-------|
| `TIP_PHYSICALLY_MISSING` | Retry with next tip candidate | `recover_tip_pickup` or `execute_protocol_recovery(retry_pick_up_tip_with_next_candidate)` |
| `DESTINATION_OCCUPIED` | Suggest alternatives, **human review required** | `suggest_recovery_action` → `execute_protocol_recovery(suggest_new_destination_slot)` |
| `HARDWARE_FAULT` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `DECK_COLLISION` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `UNKNOWN` | **Hard stop — escalate to human** | Stop all autonomous motion |
| `DESTINATION_UNAVAILABLE` | Treat as occupied | Same as DESTINATION_OCCUPIED |
| `PROTOCOL_SETUP_ERROR` | Fix protocol in simulation loop | Back to simulation gate |
| Simulation failure | Fix code, re-simulate | `opentrons-simulation-repair` loop |

## Recovery Branches

`execute_protocol_recovery` supports 4 automatic branches:

1. **`retry_pick_up_tip_with_next_candidate`** — marks failed well, finds next tip, re-enqueues pickUpTip
2. **`suggest_new_destination_slot`** — proposes alternative slot (always human-reviewed)
3. **`wait_and_poll_module_status`** — waits for module blocker to clear, then resumes
4. **`reconcile_state_first`** — reconciles deck state before any further motion
