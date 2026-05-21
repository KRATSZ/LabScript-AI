# Opentrons-Lab-Agent

## Canonical documents (read these for full rules)

| Document | Role |
|----------|------|
| [docs/rules/workflows.md](docs/rules/workflows.md) | **Workflow** — sequences, tool order, protocol library usage |
| [docs/rules/safety-policy.md](docs/rules/safety-policy.md) | **Safety policy** — hard bans, deck truth, vision, interaction defaults |
| [docs/rules/error-response.md](docs/rules/error-response.md) | **Errors & recovery** — categories, branches, Phase 2/4 invariants |
| [docs/architecture/architecture.md](docs/architecture/architecture.md) | **Architecture** — layers and pointers to diagrams |

**Documentation layout (LLM routing):** [docs/README.md](docs/README.md) — which folder to open for rules vs runbooks vs research.

This is the primary agent instruction entrypoint for this repository. Keep it short and link to canonical docs instead of duplicating policy text.

## Skills

| Skill | When to use |
|-------|-------------|
| `opentrons-experiment-run` | Default entry. New experiments, "what's the robot doing?", resume, recovery |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment — before authoring |
| `opentrons-protocol-author` | Write or revise Python protocol code |
| `opentrons-protocol-library` | Search 833 reference protocols, find code examples |
| `opentrons-protocol-verify` | Local doctor/analyze/simulate without MCP |
| `opentrons-robot-lan` | Formal robot HTTP route: MCP fallback, MCP debugging, or explicit operator choice |
| `opentrons-simulation-repair` | Iterative simulate → parse → edit → simulate fix loop |

**On-demand skills (do not use by default):**

- **`opentrons-protocol-library`** — Only when the user asks to search the 833-protocol catalog, find existing examples, or browse reference code. Do **not** open it for routine new-protocol authoring when a blank or workflow template suffices.
- **`opentrons-robot-lan`** — Use when MCP is unavailable, when debugging MCP itself, or when the user explicitly opts into the robot HTTP route (see [docs/rules/safety-policy.md](docs/rules/safety-policy.md)).
- **Vision / camera / `vision_check`** — Only when the user asks for a visual deck check, camera preview, or image-based confirmation. Vision is observation-only; never treat it as committed deck truth — reconcile with `reconcile_state` and robot APIs. Canonical tool order: [docs/rules/workflows.md](docs/rules/workflows.md) → section **Optional deck vision (observation-only)**.

MCP server: `opentrons-lab-mcp` at `mcp-servers/opentrons-mcp/`.

## Quick reminder (details in linked docs)

Simulation is blocking before unattended live play. MCP `run_protocol` is the default live path; robot HTTP is a formal fallback/debug path, but never run both against the same robot in parallel. Recovery follows `parse_error` → `suggest_recovery_action` → `execute_protocol_recovery`; logs are audit-only; hard-stop categories escalate to a human.

For protocol authoring, prefer MCP `validate_labware_name` before trusting a new load name, `inspect_labware_definition` when you need geometry or dead-volume guidance, and `estimate_tip_budget` before finalizing a draft with many transfers. These are the fast checks that prevent the common labware and tip-capacity mistakes.

## Detailed reference (read on demand)

- Architecture diagrams: [docs/architecture/diagrams/README.md](docs/architecture/diagrams/README.md)
- Experiment-type SOP: [docs/guides/experiment-sop.md](docs/guides/experiment-sop.md)
- Agent behavior guidelines: [docs/guides/agent-behavior.md](docs/guides/agent-behavior.md)
