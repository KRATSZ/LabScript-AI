# Safety policy (canonical)

This file is the **single source of truth** for safety rules and hard bans in this repository. `CLAUDE.md` and the root `README.md` only summarize and link here.

## Hard bans (do not violate)

1. **Simulation gate is blocking.** If `simulate_protocol` or `doctor_local_runtime` fails, fix the protocol or environment. No `maintenance_runs` spam, no blind `curl` loops, no ad hoc HTTP workarounds.
2. **Live execution via MCP only.** Use `run_protocol`. No parallel scripts on the same robot unless MCP is unavailable and the user explicitly chose fallback (`opentrons-robot-lan`).
3. **Hardware errors → MCP recovery pipeline.** `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`. No improvised commands.
4. **Logs are audit-only.** `experiment_history` is post-hoc review. Current deck truth: `reconcile_state`, `robot_status`, `module_status`.
5. **No parallel MCP + scripts on the same robot.**
6. **Hard stops require human review.** `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always escalate.

## Additional safety rules

- **DESTINATION_OCCUPIED**: Alternative slots are always human-reviewed. No automatic reroute outside `execute_protocol_recovery`.
- **Safe home**: `home` only when there are no blockers, no tip cleanup pending, and `needs_reconciliation` is false (use `is_home_safe` before homing when applicable).
- **Simulation** must use the project venv: `.venv/bin/python` (or `uv run python`) for all simulate paths.
- **Physical deck**: Never assume layout — read actual state via MCP or `data/session-state/` JSON.
- **Modules**: Do not `load_module` for hardware you are not using.

## Vision and camera

Vision / `vision_check` is **observation-only**. It does not mutate session state or override `reconcile_state`. Compare vision output with robot APIs and reconciled deck state before treating it as truth. Use only when the operator asks for a visual check (see skill routing in `CLAUDE.md`).

## Runtime defaults

- Open-ended experiment or robot questions → start from `opentrons-experiment-run`.
- After MCP or host restart → prefer `safe_next_action` (or `restart_review`) before chaining `reconcile_state` and live status tools.

## Interaction defaults

- Default operator experience: one input → at most one blocking clarification round → one confirmation before live execution.
- If a runnable protocol exists, simulation is the default next step.
- Only block on missing information that changes safety, deck truth, robot type, labware compatibility, or required modules.
- Safety refusals must include a compliant alternative path.

## See also

- Workflows: [workflows.md](workflows.md)
- Error taxonomy and recovery: [error-response.md](error-response.md)
- Experiment-type heuristics: [experiment-sop.md](experiment-sop.md)
- Operator UX: [agent-behavior.md](agent-behavior.md)
