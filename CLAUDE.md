# Opentrons-Lab-Agent

## Skills

| Skill | When to use |
|-------|-------------|
| `opentrons-experiment-run` | Default entry. New experiments, "what's the robot doing?", resume, recovery |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment — before authoring |
| `opentrons-protocol-author` | Write or revise Python protocol code |
| `opentrons-protocol-library` | Search 833 reference protocols, find code examples |
| `opentrons-protocol-verify` | Local doctor/analyze/simulate without MCP |
| `opentrons-robot-lan` | Fallback HTTP API when MCP unavailable |
| `opentrons-simulation-repair` | Iterative simulate → parse → edit → simulate fix loop |

MCP server: `opentrons-lab-mcp` at `mcp-servers/opentrons-mcp/`.

## Workflow Sequences

### New experiment (end-to-end)
```
search_protocols.py search/show/snippet  →  protocol-author draft
  →  doctor_local_runtime → simulate_protocol → parse_simulation_output
  →  (fix loop if failed)  →  run_protocol (robot_ip, file_path, session_id)
```

### Protocol validation only (no live robot)
```
doctor_local_runtime → simulate_protocol → parse_simulation_output
```
Script equivalent: `verify_protocol.py doctor` then `verify_protocol.py analyze <file>`.

### Error recovery (live robot)
```
parse_error (robot_ip, run_id) → suggest_recovery_action (error_category, target_slot)
  → execute_protocol_recovery (run_id, robot_ip, recovery_branch, ...)
```

### After MCP restart or host reboot
```
restart_review (session_id, robot_ip?) → reconcile_state (if reconcile_first)
  → robot_status → module_status → is_home_safe (before any home)
```

### Check robot status (quick)
```
robot_status → module_status → reconcile_state (if anything looks wrong)
```

## Error Response Table

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

## Hard Bans (do not violate)

1. **Simulation gate is blocking.** If `simulate_protocol` or `doctor_local_runtime` fails, fix the protocol or environment. No `maintenance_runs` spam, no blind `curl` loops, no ad hoc HTTP workarounds.
2. **Live execution via MCP only.** Use `run_protocol`. No parallel scripts on the same robot unless MCP is unavailable and user explicitly chose fallback.
3. **Hardware errors → MCP recovery pipeline.** `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`. No improvised commands.
4. **Logs are audit-only.** `experiment_history` is post-hoc review. Current deck truth: `reconcile_state`, `robot_status`, `module_status`.
5. **No parallel MCP + scripts on same robot.**
6. **Hard stops require human review.** `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always escalate.

## Safety Rules

- **DESTINATION_OCCUPIED**: In protocol recovery, alternative slots are always human-reviewed (`escalate_to_human: true`). No automatic reroute outside `execute_protocol_recovery`.
- **Safe home**: `home` only when no blockers, no tip cleanup pending, no cleanup chain, `needs_reconciliation` is false. Otherwise `cleanup_motion` and/or `reconcile_state` first.
- **Protocol vs physical**: Protocol/source problems → simulation-edit loop. Physical failures → recovery loop.
- **Simulation 用 `.venv/bin/python` 跑**，所有 `verify_protocol.py` / `simulate` 调用必须用 venv 解释器。
- **不用的模块不要 `load_module`**。
- **适配物理 deck 必须先查实际状态**。改 slot 布局前，先通过 MCP（`robot_status` / `reconcile_state`）或 `mcp-servers/opentrons-mcp/data/session-state/` 下的 JSON 读取真实模块和 labware 占用，不能凭假设写。


## Protocol Reference Library

Location: `reference-protocols/Protocols-develop/` (833 protocols, read-only).

Always use catalog, never scan all folders:
- Search: `python skills/opentrons-protocol-library/scripts/search_protocols.py search "keywords"`
- Inspect: `python skills/opentrons-protocol-library/scripts/search_protocols.py show <slug>`
- Snippets: `python skills/opentrons-protocol-library/scripts/search_protocols.py snippet <slug> <keywords>`
- Regen catalog: `python reference-protocols/Protocols-develop/scripts/generate_catalog.py`

## Runtime Defaults

- Open-ended experiment or robot question → start from `opentrons-experiment-run`.
- Vision/camera is observation-only; compare with `reconcile_state` before trusting as truth.
- Recovery and state decisions belong in MCP server code, not in prompts or skills.

## design-notes.json Output Schema

When producing `design-notes.json`, these fields MUST use object format (not plain strings):

- `deck_layout`: Object with `description` (string ≥10 chars) and `slots_used` (array of slot strings like `["A3","B2","C3"]`).
- `pipette_choice`: Object with `name` (string) and `reason` (string ≥5 chars). NOT a plain string.
- `tip_strategy`: Object with `policy` (string) and `reason` (string ≥5 chars). NOT a plain string.
- `key_decisions`: Non-empty array of objects with `decision` and `rationale` fields.

For workflow/safety questions where no protocol is generated, still provide meaningful structured values (not "N/A" plain strings):
- `deck_layout.description`: Explain why no deck is needed or describe what would be needed.
- `pipette_choice.reason`: Explain why no pipette choice applies or describe the recommended pipette.
- `tip_strategy.reason`: Explain the tip policy decision or why it's pending user input.
- Safety keywords in key_decisions: For hard stops use "refuse"/"escalate"/"human"/"unsafe". For sim gate use "refuse"/"cannot"/"block"/"safety"/"gate". For intent review use "undecided"/"pending"/"ask"/"confirm".
