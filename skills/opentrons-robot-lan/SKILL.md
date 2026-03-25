---
name: opentrons-robot-lan
description: Use when guiding live Opentrons OT-2 or Flex operations. Prefer MCP (opentrons-lab-mcp) for all robot state and control; optional Python scripts below are a manual fallback when MCP is not wired.
---

# Opentrons Robot LAN

**Primary path:** use **`opentrons-lab-mcp`** tools for health, deck state, runs, recovery, cameras, and protocol upload/run. Runtime truth and safety gates live in MCP, not in this skill.

**Fallback path:** the Python script under `scripts/` talks to the same HTTP API for environments without MCP — keep payloads consistent and do not bypass MCP session state when both are available.

Prefer running any script through a `uv` virtual environment: `uv run python ...`.

## Workflow

1. For end-to-end “verify → run → monitor → recover,” use skill **`opentrons-experiment-run`** so the agent follows one orchestration story.
2. After an MCP or host restart, prefer MCP **`restart_review`** first (same `session_id`, optional `robot_ip`), then follow `guidance.suggested_tool_order` — if `reconcile_first`, run **`reconcile_state`** before other autonomous motion; use **`run_history`** (there is no separate `get_run_status` tool) for live run + command history. Operator checklist: `docs/restart-review-runbook.md`.
3. Prefer the MCP live-state order when available:
   `robot_status` -> `module_status` -> `reconcile_state` -> `get_slot_occupation` / `list_tip_candidates` / `is_home_safe` -> `create_run_context` -> command tools (`load_pipette`, `load_labware`, `load_module`, `control_temperature_module`, `control_heater_shaker`, `control_thermocycler`, `move_labware`, `cleanup_motion`) -> `camera_status` / `capture_run_image` / `list_data_files` / `download_data_file` / `analyze_image_with_kimi` when visual confirmation is needed -> `run_history` / `experiment_history` -> `suggest_recovery_action`
4. For full protocol runs on the robot, prefer MCP `run_protocol` so the **simulation gate** runs before any upload or play. The skill's manual `upload-protocol -> analyze-protocol -> create-run -> run-action` path **does not** apply that gate unless you separately run MCP `doctor_local_runtime` / `simulate_protocol` / `parse_simulation_output`.
5. For protocol execution **without MCP**, use the safe script order:
   upload protocol -> analyze protocol -> create run -> run action
6. Use the provided script instead of ad hoc `curl` so payloads stay consistent.
7. For preview images, always save to a file path and then reference that file in the response.
8. Treat robot camera output as acquisition only: do not infer liquid state from the preview unless a separate human or analyzer step has been added.
9. If the user wants local dry-run verification instead of robot API analysis, switch to `opentrons-protocol-verify`.
10. For `DESTINATION_OCCUPIED`, follow MCP `suggest_recovery_action`: if the run is in **protocol error recovery**, treat alternative destination suggestions as **human-reviewed** even when a slot looks empty. Outside recovery, **high-confidence** empty alternatives may be actionable only through MCP `execute_protocol_recovery` with an explicit chosen slot; **unknown** slots stay human-reviewed.
11. Before suggesting `home`, use MCP `is_home_safe`. If reconciliation is pending or cleanup is required, **do not** assume homing is safe.
12. Treat `HARDWARE_FAULT`, collision-class (`DECK_COLLISION`), and unresolved ambiguity (`UNKNOWN`) as **hard stops**. Do not auto-continue them.
13. `probe_wells` is experimental. Simulate it first, and do not run it on a real robot unless the operator explicitly confirms and `OPENTRONS_ENABLE_PROBE_WELLS=1` is set for the MCP server. Live checklist: `docs/probe-wells-live-validation.md`.
14. Treat `experiment_history` and result logs as **audit trail**, not current deck truth; use `reconcile_state` and live status tools for what the robot is doing now.

## Commands (optional fallback without MCP)

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 get-camera
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 create-run --protocol-id <protocol-id>
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 run-action <run-id> play
```

## Reference File

- Wrapped endpoints and payloads: `references/http-api.md`
