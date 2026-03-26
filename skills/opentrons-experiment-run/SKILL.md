---
name: opentrons-experiment-run
description: Use when orchestrating an end-to-end experiment on the robot via MCP — local verify, gated run, monitoring, audit logs, restart review, and recovery. Does not replace MCP tools; it defines the call order and human gates.
---

# Opentrons experiment run (MCP orchestration)

Use this skill when the user wants a **full loop** from “protocol file on disk” to “run finished or safely paused,” using **`opentrons-lab-mcp` as the only runtime authority**.

## Principles

- **MCP owns state and motion.** Do not use parallel HTTP scripts for the same robot action unless MCP is unavailable and the user explicitly chooses a manual fallback.
- **Simulation before hardware.** Prefer MCP `run_protocol` (built-in simulation gate) for full runs. For edit loops before upload, pair with `opentrons-protocol-verify` or `opentrons-simulation-repair`.
- **Logs are audit-only.** After restarts, use `restart_review` and `reconcile_state`; use `experiment_history` for narrative, not current deck truth.

## Recommended flow

### A. Before any live execution

1. Optional: `opentrons-protocol-verify` or MCP `doctor_local_runtime` → `simulate_protocol` → `parse_simulation_output` while editing (see `opentrons-simulation-repair` for iterative repair).
2. MCP **`restart_review`** if resuming a session or after MCP/host restart (`session_id`, optional `robot_ip`).
3. If **`guidance.reconcile_first`** → **`reconcile_state`** before autonomous motion.

### B. Run a full protocol on hardware

1. MCP **`run_protocol`** with `file_path`, `robot_ip`, `session_id` as needed (simulation gate runs inside the tool).
2. On intervention or failure: **`run_history`**, **`parse_error`**, **`suggest_recovery_action`**.
3. Execute only supported branches via **`execute_protocol_recovery`** (or **`recover_tip_pickup`** when that wrapper is appropriate). Respect **hard stops** and **`DESTINATION_OCCUPIED`** human-review rules from `opentrons-robot-lan` / project docs.
4. Before **`home`**: **`is_home_safe`**.

### C. Audit and resume

1. **`experiment_history`** with filters (`session_id`, `run_id`, `tool_name`, `status`, `limit`, optional `event_kind`).
2. **`restart_review`** again if context was lost or operators rotated.

## Handoffs

- **Authoring / editing Python:** `opentrons-protocol-author`
- **Local-only verify without MCP:** `opentrons-protocol-verify`
- **Simulate-fix loop:** `opentrons-simulation-repair`
- **Experimental liquid probe:** MCP `probe_wells` — follow `docs/probe-wells-live-validation.md` before any live execution

## Reference

- Restart operator checklist: `docs/restart-review-runbook.md`
- MCP README: `mcp-servers/opentrons-mcp/README.md`
