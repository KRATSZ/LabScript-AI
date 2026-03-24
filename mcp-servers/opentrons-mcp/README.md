# Opentrons Lab MCP

This folder contains a practical MCP server for `Opentrons-Lab-Agent`.

It is intentionally focused on the highest-value workflow for Claude Code:

- a few useful live robot control tools
- local `opentrons.simulate` integration
- structured simulation parsing for multi-round protocol repair

## Why this server exists

The repository already includes Python-first skills for:

- writing protocols
- verifying protocols locally
- controlling a robot over LAN

This MCP server adds a tighter tool loop for agent orchestration:

1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. retry until pass

It also exposes a compact set of live tools:

- `robot_health`
- `robot_status`
- `module_status`
- `get_slot_occupation`
- `list_tip_candidates`
- `suggest_next_tip_well`
- `is_home_safe`
- `reconcile_state`
- `parse_error`
- `suggest_recovery_action`
- `create_run_context`
- `load_pipette`
- `load_labware`
- `load_module`
- `control_temperature_module`
- `control_heater_shaker`
- `control_thermocycler`
- `move_labware`
- `cleanup_motion`
- `camera_status`
- `configure_camera`
- `capture_preview_image`
- `capture_run_image`
- `list_data_files`
- `download_data_file`
- `analyze_image_with_kimi`
- `get_protocols`
- `upload_protocol`
- `create_run`
- `control_run`
- `get_runs`
- `run_history`
- `get_run_status` (compatibility alias)

## Notes

- The tool surface is inspired by the community project `yerbymatey/opentrons-mcp`, but reduced to the parts that are most useful for this repository's simulation-first workflow.
- For API documentation lookup, pair this server with `opentrons-document-mcp-server`.
- Live-state tools return a common envelope with `success`, `data`, `error`, `hardware_snapshot`, `state_revision`, `run_id`, `session_id`, and `timestamp`.
- Session-level `DeckState` snapshots are persisted under `data/session-state/` so tip bookkeeping and reconciliation survive MCP restarts.
- `capture_preview_image` saves the preview locally and returns the artifact path so a later human step or vision analyzer can consume it without embedding binary image data into MCP responses.
- `capture_run_image` uses the robot command queue (`captureImage`) and attempts to download the generated data file immediately; on the current Flex software, maintenance-context captures may succeed without returning a downloadable `fileId`, so the server also exposes `list_data_files` and `download_data_file` for working with historical robot images.
- `analyze_image_with_kimi` calls SiliconFlow's OpenAI-compatible chat API and is intended for deck-level visual analysis, not liquid-volume truth.
- On the current validated Flex (`10.31.2.149:31950`, API `8.8.1`), `GET /camera` is available, while the POST camera endpoints currently return `404`; the MCP therefore reports these as capability/version gaps instead of silently pretending preview capture is supported everywhere.
- Real-Flex validation now includes a physical gripper move of `corning_96_wellplate_360ul_flat` from `C3` to `B3`, followed by successful `cleanup_motion`.
- Real-Flex validation also includes runtime error parsing for `TIP_PHYSICALLY_MISSING`, `PROTOCOL_SETUP_ERROR`, `DESTINATION_UNAVAILABLE`, and a software-occupied `DESTINATION_OCCUPIED` move failure.

## Install

```bash
cd mcp-servers/opentrons-mcp
npm install
```

## Test

```bash
npm test
```

## Example MCP config

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"]
    },
    "opentrons-docs": {
      "command": "npx",
      "args": ["-y", "opentrons-document-mcp-server@latest"]
    }
  }
}
```

If your simulation environment is not on the default `python3`, either:

- rely on the repository-local `./.venv/bin/python` auto-detection, or
- set `OPENTRONS_PYTHON`, or
- pass `python_executable` to the simulation tools.
