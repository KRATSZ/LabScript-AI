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
  - live_readiness_check
  - safe_next_action
  - restart_review
  - experiment_history
  - is_home_safe
  - health_check
  - camera_status
  - capture_preview_image
  - vision_check
---

# Experiment Run (MCP State Machine)

Phases are **ordered**. Finish each gate before the next. If a gate fails,
**stop** and fix or escalate.

## User-Facing Contract

Hide internal complexity from the operator. The default interaction model is:

1. One user input
2. At most one blocking clarification round
3. One confirmation before live execution

If a runnable protocol exists, the default next step is the simulation gate. Do
not wait for the user to explicitly ask for simulate.

### Phase 0 — Intent (multi-well / pattern / ambiguous mapping)

- If wells or spatial layout not confirmed: `opentrons-experiment-intent-review`
  to obtain `target_wells` / `plate_mask` and `tip_policy`.
- If intent already fixed: skip to Phase 1.
- Ask only the minimum blocking questions. Prefer a documented default for
  non-critical preferences.
- **Do not** default to `opentrons-protocol-library` for new authoring. Use it **only** if the user explicitly wants to search the reference catalog or find an existing protocol example.

### Phase 1 — Protocol

- Author or revise Python with `opentrons-protocol-author`.
- Code must match Phase 0 outputs (requirements, labware slots, pipette names,
  trash on Flex, volumes).

### Phase 2 — Simulation Gate (blocking)

- `doctor_local_runtime` -> `simulate_protocol` -> `parse_simulation_output`
- Or `opentrons-simulation-repair` for the edit loop.
- **Failure here -> STOP for live.** No workaround.
- If simulation fails, keep ownership of the repair loop when possible instead of
  pushing the user back to raw logs without guidance.

### Phase 3 — Live Preflight

- If the operator explicitly wants a cautious live bring-up gate: `health_check` -> `live_readiness_check` before `create_run` or `play`.
- After MCP/host restart or when the operator is lost: prefer **`safe_next_action`** (same inputs as `restart_review`) for `recommended_next_tool` and `operator_steps`; fall back to **`restart_review`** for the full raw bundle.
- If `guidance.reconcile_first` -> `reconcile_state`.
- `robot_status`, `module_status` — verify robot reachable and modules ready.
- `reconcile_state` — confirm deck matches expected layout.
- **Deck vision (observation-only) — ONLY if the operator explicitly requests a visual check or image-based deck confirmation:** `camera_status` → `capture_preview_image` → `vision_check` on the saved image. Canonical sequence and setup: **`docs/rules/workflows.md`** → section *Optional deck vision (observation-only)* and `docs/runbooks/vision-acceptance.md`. Do **not** pull vision into the default preflight path. Treat output as hints; **do not** treat vision as committed deck truth — compare with `reconcile_state` and robot APIs. Prefer in-repo `vision/models/weights/` auto-resolution (or local `vision/runs/detect/...`); legacy sibling `labagentyolo` paths still work during migration. Override with `weights` / `OPENTRONS_DECK_YOLO_WEIGHTS` if needed.
- Before `home`: `is_home_safe`.

### Phase 4 — Execute

- `run_protocol` (file_path, robot_ip, session_id).
- Simulation gate also runs inside this tool.
- Before this phase, give the operator a short ready-state summary rather than a
  long internal trace.

### Phase 5 — Failure / Recovery

- `run_history` -> `parse_error` -> `suggest_recovery_action`.
- Execute only branches that come back with `auto_executable: true`: `execute_protocol_recovery` / `recover_tip_pickup`.
- Hard stops and DESTINATION_OCCUPIED human-review rules per `docs/rules/safety-policy.md` and `docs/rules/error-response.md`.

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
- No MCP: `opentrons-robot-lan` (explicit fallback only).
- Search existing Opentrons examples: `opentrons-protocol-library` (user-requested only).
