---
name: opentrons-robot-lan
description: Fallback HTTP API when MCP is unavailable — direct LAN access to OT-2 or Flex robot.
type: script-backed
entry: scripts/opentrons_robot_api.py
mcp_tools:
  - robot_status
  - module_status
  - reconcile_state
  - run_protocol
  - restart_review
  - is_home_safe
  - camera_status
  - capture_preview_image
---

# Robot LAN (MCP-absent fallback)

MCP is primary path. This skill's scripts are fallback when MCP is not wired.

## MCP Tool Order (when available)

`robot_status` -> `module_status` -> `reconcile_state` ->
`get_slot_occupation` / `list_tip_candidates` / `is_home_safe` ->
`create_run_context` ->
command tools (`load_pipette`, `load_labware`, `load_module`,
`control_temperature_module`, `control_heater_shaker`, `control_thermocycler`,
`move_labware`, `cleanup_motion`) ->
camera tools (`camera_status`, `capture_preview_image`, `capture_run_image`,
`list_data_files`, `download_data_file`, `analyze_image_with_kimi`) ->
`run_history` / `experiment_history` -> `suggest_recovery_action`

## Key Rules

- After MCP/host restart: `restart_review` first, follow `guidance.suggested_tool_order`.
  If `reconcile_first`: run `reconcile_state` before other motion.
- For full protocol runs: `run_protocol` (simulation gate runs before play).
- For protocol execution without MCP: upload -> analyze -> create-run -> run-action.
- `DESTINATION_OCCUPIED`: follow `suggest_recovery_action`. In protocol recovery,
  treat alternative destinations as human-reviewed. Outside recovery, only
  `execute_protocol_recovery` with explicit slot.
- Before `home`: use `is_home_safe`.
- `probe_wells` = experimental. Simulate first. Requires
  `OPENTRONS_ENABLE_PROBE_WELLS=1` and operator confirmation for live use.
- Preview images: save to file, reference path in response.
- Do not infer liquid state from camera output without separate analysis.

## Fallback Commands (no MCP)

### Connection management

```bash
# Save connection for reuse (--host is optional afterwards)
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 save-connection
# Show saved connection (token is redacted)
uv run python scripts/opentrons_robot_api.py show-connection
```

### One-shot deploy and run

```bash
# Upload → analyze → create run → play (single command)
uv run python scripts/opentrons_robot_api.py deploy-and-run protocol.py
```

### Labware search

```bash
# Search labware definitions by keyword (local-only, no host needed)
uv run python scripts/opentrons_robot_api.py search-labware "PCR full skirt"
uv run python scripts/opentrons_robot_api.py search-labware "reservoir" --limit 10
```

### Run monitoring

```bash
# Smart monitoring: only outputs on status change, exits on terminal
uv run python scripts/opentrons_robot_api.py watch-run <run-id> --interval 30 --timeout 1800
```

### Deck check

```bash
# Compare protocol declarations vs live robot deck before running
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 deck-check protocol.py
```

### Legacy commands (still available)

```bash
uv run python scripts/opentrons_robot_api.py health                       # uses saved connection
uv run python scripts/opentrons_robot_api.py get-camera
uv run python scripts/opentrons_robot_api.py upload-protocol path/to/protocol.py
uv run python scripts/opentrons_robot_api.py analyze-protocol <protocol-id>
uv run python scripts/opentrons_robot_api.py create-run --protocol-id <protocol-id>
uv run python scripts/opentrons_robot_api.py run-action <run-id> play
```

Ref: `references/http-api.md`
