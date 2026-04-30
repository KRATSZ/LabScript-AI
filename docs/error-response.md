# Error response (canonical)

This file is the **single source of truth** for the MCP error taxonomy, recovery action contract, and live-recovery invariants.

## Canonical taxonomy fields

Every structured error emitted by `parse_simulation_output`, `parse_error`, `suggest_recovery_action`, blocked `run_protocol` payloads, and `preflight_run_setup` checks should use these fields:

- `phase`
- `error_domain`
- `error_leaf`
- `severity`
- `recoverability`
- `requires_human_review`
- `auto_executable`
- `default_next_step`
- `evidence_sources`

Compatibility fields such as `error_category`, `hard_stop`, and `escalate_to_human` remain valid.

## Canonical leaf tree

| Domain | Leaves |
|--------|--------|
| `environment` | `RUNTIME_UNAVAILABLE`, `PYTHON_ENV_BROKEN`, `MCP_CONFIG_MISMATCH` |
| `protocol` | `SYNTAX_OR_IMPORT`, `API_MISUSE`, `LABWARE_OR_MODULE_COMPAT`, `MISSING_TRASH_OR_SETUP`, `VOLUME_OR_RANGE_VIOLATION`, `OUT_OF_TIPS` |
| `session_state` | `SESSION_NEEDS_RECONCILIATION`, `STALE_LAST_RUN`, `RUN_NOT_AWAITING_RECOVERY` |
| `robot_state` | `ROBOT_UNREACHABLE`, `DOOR_OPEN`, `ESTOP_ENGAGED`, `INSTRUMENT_NOT_READY` |
| `module_state` | `MODULE_NOT_READY` |
| `deck_state` | `DESTINATION_OCCUPIED`, `DESTINATION_UNAVAILABLE`, `LABWARE_MISMATCH`, `SLOT_NOT_ADDRESSABLE` |
| `motion_or_liquid` | `DECK_COLLISION`, `TIP_PHYSICALLY_MISSING`, `TIP_CLOG`, `INSUFFICIENT_VOLUME`, `AIR_BUBBLE`, `LIQUID_PROPERTY_ERROR` |
| `unknown` | `UNKNOWN_NEEDS_HUMAN` |

## Recovery action contract

`suggest_recovery_action` must always return one of these actionability states:

| `actionability` | Meaning |
|-----------------|---------|
| `auto_executable` | `execute_protocol_recovery` can run the branch immediately with the current guidance. |
| `manual_confirmation_required` | `execute_protocol_recovery` supports the branch, but the operator must confirm and/or supply required inputs first. |
| `manual_only` | No supported automatic branch exists; the operator must intervene. |
| `protocol_edit_required` | Return to the simulation/edit loop instead of attempting runtime recovery. |

`execute_protocol_recovery` only accepts guidance with `auto_executable: true`.

### Supported executable branches

1. `retry_pick_up_tip_with_next_candidate`
2. `suggest_new_destination_slot`
3. `wait_and_poll_module_status`
4. `reconcile_state_first` when reconciliation diffs are module-blocker-only

### Manual-only examples

- `INSUFFICIENT_VOLUME`
- `AIR_BUBBLE`
- `TIP_CLOG`
- `LIQUID_PROPERTY_ERROR`
- `DECK_COLLISION`
- `UNKNOWN_NEEDS_HUMAN`
- `DESTINATION_OCCUPIED` outside `awaiting-recovery`

### Protocol-edit-required examples

- `MISSING_TRASH_OR_SETUP`
- `SYNTAX_OR_IMPORT`
- `API_MISUSE`
- `LABWARE_OR_MODULE_COMPAT`
- `VOLUME_OR_RANGE_VIOLATION`
- `OUT_OF_TIPS` when discovered in simulation

## Hard-stop policy

These remain non-negotiable:

1. `HARDWARE_FAULT`, `DECK_COLLISION`, and `UNKNOWN` compatibility categories are hard stops.
2. `collision` / `unknown` class failures do **not** auto-resume.
3. `DESTINATION_OCCUPIED` inside protocol recovery stays human-reviewed even when candidate slots look safe.

## Live readiness

Use `live_readiness_check` as the read-only gate before `create_run` or `play`.

- `health_check` is a developer/environment check.
- `live_readiness_check` is the operator-facing live gate.
- `preflight_run_setup` remains the final protocol-aware check before play.

Current rollout is **Flex-first**. OT-2 deck-diff modeling is still explicitly skipped in this build; OT-2 support should not be implied by the new taxonomy alone.

## Phase 2 / Phase 4 invariants

These rules are implemented in `mcp-servers/opentrons-mcp/` and covered by tests under `mcp-servers/opentrons-mcp/test/`.

1. **Simulation gate is blocking.** Runtime execution must not bypass `doctor_local_runtime` → `simulate_protocol` → `parse_simulation_output`.
2. **Reconciliation beats history.** When session state says `needs_reconciliation`, reconcile before autonomous motion even if historical logs show success.
3. **Result logs stay audit-only.** `experiment_history` is narrative evidence, not live deck truth.

## See also

- Live gating and staged validation: [live-readiness-runbook.md](live-readiness-runbook.md)
- Restart/reconcile operator flow: [restart-review-runbook.md](restart-review-runbook.md)
- Workflow sequences: [workflows.md](workflows.md)
- Safety policy: [safety-policy.md](safety-policy.md)
