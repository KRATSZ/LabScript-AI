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

```bash
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 health
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 get-camera
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 create-run --protocol-id <protocol-id>
uv run python scripts/opentrons_robot_api.py --host 192.168.1.50 run-action <run-id> play
```

Ref: `references/http-api.md`
