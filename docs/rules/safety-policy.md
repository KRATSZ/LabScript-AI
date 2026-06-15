# Safety policy (canonical)

This file is the **single source of truth** for safety rules and hard bans in this repository. `AGENTS.md`, compatibility stubs, and the root `README.md` only summarize and link here.

## Hard bans (do not violate)

1. **Simulation gate is blocking before unattended live execution.** If `simulate_protocol` or `doctor_local_runtime` fails, fix the protocol or environment before live play. Read-only diagnostics may still run to understand the robot state.
2. **Live execution prefers MCP, with HTTP fallback as a formal route.** Use MCP `run_protocol` by default. Use `opentrons-robot-lan` / robot HTTP when MCP is unavailable, when debugging MCP itself, or when the operator explicitly chooses the HTTP route. Do not run MCP and HTTP control commands against the same robot at the same time.
3. **Hardware errors → MCP recovery pipeline.** `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`. No improvised commands.
4. **Logs are audit-only.** `experiment_history` is post-hoc review. Current deck truth: `reconcile_state`, `robot_status`, `module_status`.
5. **No parallel MCP + HTTP/scripts on the same robot.**
6. **Hard stops require human review.** `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always escalate.

## Additional safety rules

- **Read-only live gate first when requested**: use `live_readiness_check` before `create_run` or `play` when the operator asks for a cautious live readiness pass. `health_check` alone is not enough for live go/no-go decisions.
- **DESTINATION_OCCUPIED**: Alternative slots are always human-reviewed. No automatic reroute outside `execute_protocol_recovery`.
- **Safe home**: `home` only when there are no blockers, no tip cleanup pending, and `needs_reconciliation` is false (use `is_home_safe` before homing when applicable).
- **Simulation** should use the project venv: `.venv/bin/python` (or `uv run python`) for normal simulate paths. If another Opentrons runtime is selected, record the path in the command or run notes.
- **Physical deck**: Never assume layout — read actual state via MCP or `data/session-state/` JSON.
- **Modules**: Do not `load_module` for hardware you are not using.

## Vision and camera

Vision / `vision_check` is **observation-only**. It does not mutate session state or override `reconcile_state`. Compare vision output with robot APIs and reconciled deck state before treating it as truth. Use only when the operator asks for a visual check ([workflows.md](workflows.md) → *Optional deck vision*).

## Runtime defaults

- Open-ended experiment or robot questions → start from `opentrons-experiment-run` ([`skills/opentrons-experiment-run/SKILL.md`](../../skills/opentrons-experiment-run/SKILL.md); policy remains in this folder).
- Live readiness / staged bring-up questions → prefer `live_readiness_check`, then `create_run`, then the smallest safe live run.
- After MCP or host restart → prefer `safe_next_action` (or `restart_review`) before chaining `reconcile_state` and live status tools.

## Interaction defaults

- Workflow order and when to simulate: [workflows.md](workflows.md) (*User-facing defaults*).
- Operator phrasing and status labels: [agent-behavior.md](../guides/agent-behavior.md).
- **Safety refusals must include a compliant alternative path** (non-negotiable).

## See also

- Workflows: [workflows.md](workflows.md)
- Error taxonomy and recovery: [error-response.md](error-response.md)
- Experiment-type heuristics: [experiment-sop.md](../guides/experiment-sop.md)
- Operator UX: [agent-behavior.md](../guides/agent-behavior.md)
