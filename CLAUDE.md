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

## Hard Bans (do not violate)

1. **Simulation gate is blocking.** If `simulate_protocol` or `doctor_local_runtime` fails, fix the protocol or environment. No `maintenance_runs` spam, no blind `curl` loops, no ad hoc HTTP workarounds.
2. **Live execution via MCP only.** Use `run_protocol`. No parallel scripts on the same robot unless MCP is unavailable and user explicitly chose fallback.
3. **Hardware errors → MCP recovery pipeline.** `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`. No improvised commands.
4. **Logs are audit-only.** `experiment_history` is post-hoc review. Current deck truth: `reconcile_state`, `robot_status`, `module_status`.
5. **No parallel MCP + scripts on same robot.**
6. **Hard stops require human review.** `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN` always escalate.

## Safety Rules

- **DESTINATION_OCCUPIED**: Alternative slots always human-reviewed. No automatic reroute outside `execute_protocol_recovery`.
- **Safe home**: `home` only when no blockers, no tip cleanup pending, `needs_reconciliation` is false.
- **Simulation 用 `.venv/bin/python` 跑**，所有 simulate 调用必须用 venv 解释器。
- **适配物理 deck 必须先查实际状态** — 通过 MCP 或 `data/session-state/` JSON 读取，不能凭假设写。
- **不用的模块不要 `load_module`**。

## Runtime Defaults

- Open-ended experiment or robot question → start from `opentrons-experiment-run`.
- Vision/camera is observation-only; compare with `reconcile_state` before trusting as truth.

## Detailed Reference (read on demand)

- Workflows & protocol library: [docs/workflows.md](docs/workflows.md)
- Error response table & recovery branches: [docs/error-response.md](docs/error-response.md)
- Experiment-type SOP: [docs/experiment-sop.md](docs/experiment-sop.md)
- Agent behavior guidelines: [docs/agent-behavior.md](docs/agent-behavior.md)
