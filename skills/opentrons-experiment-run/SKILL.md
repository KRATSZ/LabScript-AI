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

# Experiment Run

**Policy:** [`docs/rules/`](../../docs/rules/) · **UX:** [`docs/guides/agent-behavior.md`](../../docs/guides/agent-behavior.md) · **Runbooks:** [`docs/runbooks/`](../../docs/runbooks/)

Phase orchestration only. Ordered phases; stop on gate failure.

## Phase routing

| Phase | Route to |
|-------|----------|
| **0** | `opentrons-experiment-intent-review` if wells / layout / tip policy unclear; else skip. No `opentrons-protocol-library` unless user asks. |
| **1** | `opentrons-protocol-author` |
| **2** | `opentrons-simulation-repair` or sim tools — [workflows § validation / new experiment](../../docs/rules/workflows.md) |
| **3** | [workflows § live readiness / restart / status](../../docs/rules/workflows.md); runbooks: [live-readiness](../../docs/runbooks/live-readiness-runbook.md), [restart-review](../../docs/runbooks/restart-review-runbook.md); vision only if asked — [workflows § vision](../../docs/rules/workflows.md#optional-deck-vision-observation-only) |
| **4** | `run_protocol` after operator confirm |
| **5** | [workflows § error recovery](../../docs/rules/workflows.md) + [error-response](../../docs/rules/error-response.md) |
| **6** | `experiment_history`; `restart_review` if context lost |

## Handoff

- Sim-stuck → `opentrons-simulation-repair` / `opentrons-protocol-author`
- No MCP → `opentrons-robot-lan` ([safety-policy](../../docs/rules/safety-policy.md))
- Catalog search → `opentrons-protocol-library` (user-requested)
