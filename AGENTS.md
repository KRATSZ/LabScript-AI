# Opentrons-Lab-Agent

## Canonical documents (read these for full rules)

| Document | Role |
|----------|------|
| [docs/workflows.md](docs/workflows.md) | **Workflow** — sequences, tool order, protocol library usage |
| [docs/safety-policy.md](docs/safety-policy.md) | **Safety policy** — hard bans, deck truth, vision, interaction defaults |
| [docs/error-response.md](docs/error-response.md) | **Errors & recovery** — categories, branches, Phase 2/4 invariants |
| [docs/architecture.md](docs/architecture.md) | **Architecture** — layers and pointers to diagrams |

This file stays short for the agent host; do not duplicate long policy text here.

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

**On-demand skills (do not use by default):**

- **`opentrons-protocol-library`** — Only when the user asks to search the 833-protocol catalog, find existing examples, or browse reference code. Do **not** open it for routine new-protocol authoring when a blank or workflow template suffices.
- **`opentrons-robot-lan`** — Only when MCP is unavailable or the user explicitly opts into LAN fallback (see [docs/safety-policy.md](docs/safety-policy.md)).
- **Vision / camera / `vision_check`** — Only when the user asks for a visual deck check, camera preview, or image-based confirmation. Vision is observation-only; never treat it as committed deck truth — reconcile with `reconcile_state` and robot APIs. Canonical tool order: [docs/workflows.md](docs/workflows.md) → section **Optional deck vision (observation-only)**.

MCP server: `opentrons-lab-mcp` at `mcp-servers/opentrons-mcp/`.

## Quick reminder (details in linked docs)

Simulation is blocking before live play; live runs go through MCP `run_protocol`; recovery follows `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`; logs are audit-only; hard-stop categories escalate to a human.

For protocol authoring, prefer MCP `validate_labware_name` before trusting a new load name, `inspect_labware_definition` when you need geometry or dead-volume guidance, and `estimate_tip_budget` before finalizing a draft with many transfers. These are the fast checks that prevent the common labware and tip-capacity mistakes.

## Detailed reference (read on demand)

- Architecture diagrams: [docs/diagrams/README.md](docs/diagrams/README.md)
- Experiment-type SOP: [docs/experiment-sop.md](docs/experiment-sop.md)
- Agent behavior guidelines: [docs/agent-behavior.md](docs/agent-behavior.md)
