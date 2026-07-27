# Error taxonomy (skill)

Canonical leaf set for structured robot / simulation errors. Prefer these fields on every parsed error: `phase`, `error_domain`, `error_leaf`, `severity`, `recoverability`, `requires_human_review`, `auto_executable`, `default_next_step`, `evidence_sources`.

## Domains → leaves

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

## Actionability (`suggest_recovery`)

| State | Meaning |
|-------|---------|
| `auto_executable` | `execute_protocol_recovery` may run now |
| `manual_confirmation_required` | Branch supported; operator must confirm / supply inputs |
| `manual_only` | No auto branch — human intervenes |
| `protocol_edit_required` | Fix protocol + re-simulate; do not recover live |

`execute_protocol_recovery` only accepts `auto_executable: true`.

## Hard stops

`HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` / `UNKNOWN_NEEDS_HUMAN` → escalate; never auto-resume.

## TIP_CLOG split

- **Ordinary** (waste / zero dest delivery): tip quarantine + swap proposal; confirmation required.
- **Dangerous** (mid-dispense into sample/assay, unknown delivered vol): `manual_only` + hard stop; never blind full re-dispense.

Load `recovery-playbooks` for executable branches.
