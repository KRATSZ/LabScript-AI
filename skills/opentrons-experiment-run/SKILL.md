---
name: opentrons-experiment-run
description: Default entry for new experiments, "what's the robot doing?", resume, and recovery — orchestrates MCP state machine from intent through simulation gate to live execution.
type: prompt-only
mcp_tools:
  - robot_status
  - module_status
  - reconcile_state
  - run_protocol
  - parse_error
  - suggest_recovery_action
  - execute_protocol_recovery
  - recover_tip_pickup
  - restart_review
  - experiment_history
  - is_home_safe
  - health_check
---

# Experiment Run (MCP State Machine)

Phases are **ordered**. Finish each gate before the next. If a gate fails,
**stop** and fix or escalate.

### Phase 0 — Intent (multi-well / pattern / ambiguous mapping)

- If wells or spatial layout not confirmed: `opentrons-experiment-intent-review`
  to obtain `target_wells` / `plate_mask` and `tip_policy`.
- If intent already fixed: skip to Phase 1.

### Phase 1 — Protocol

- Author or revise Python with `opentrons-protocol-author`.
- Code must match Phase 0 outputs (requirements, labware slots, pipette names,
  trash on Flex, volumes).

### Phase 2 — Simulation Gate (blocking)

- `doctor_local_runtime` -> `simulate_protocol` -> `parse_simulation_output`
- Or `opentrons-simulation-repair` for the edit loop.
- **Failure here -> STOP for live.** No workaround.

### Phase 3 — Live Preflight

- `restart_review` if resuming or after MCP/host restart.
- If `guidance.reconcile_first` -> `reconcile_state`.
- `robot_status`, `module_status` — verify robot reachable and modules ready.
- `reconcile_state` — confirm deck matches expected layout.
- Before `home`: `is_home_safe`.

### Phase 4 — Execute

- `run_protocol` (file_path, robot_ip, session_id).
- Simulation gate also runs inside this tool.

### Phase 5 — Failure / Recovery

- `run_history` -> `parse_error` -> `suggest_recovery_action`.
- Execute supported branches: `execute_protocol_recovery` / `recover_tip_pickup`.
- Hard stops and DESTINATION_OCCUPIED human-review rules per Agent CLAUDE.md.

### Phase 6 — Audit

- `experiment_history` (session_id, run_id, tool_name, status, limit).
- `restart_review` again if operators rotate or context lost.

## Safety Refusals — Offer Alternative Path

When refusing an unsafe request, **always immediately offer the corrective action**:

| User asks | Agent refuses AND offers |
|-----------|-------------------------|
| "绕过仿真直接跑" | "不能跳过仿真。把报错信息给我，我现在帮你修" |
| "collision 了自动重试" | "碰撞后不能自动重试。请先：1) 检查 deck 有无移位 2) 确认 pipette 完好 3) 完成后我跑 reconcile_state" |
| "不管报错继续跑" | "硬件故障需要人工检查。检查完告诉我结果，我帮你判断下一步" |

## Handoff

- Sim-stuck: `opentrons-simulation-repair` or `opentrons-protocol-author`.
- No MCP: `opentrons-robot-lan`.
