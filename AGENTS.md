# Opentrons-Lab-Agent

Short agent entry. **Runtime policy = `docs/rules/` only** — link, do not copy. Layering: [docs/README.md](docs/README.md). Repo folders: [docs/REPO_LAYOUT.md](docs/REPO_LAYOUT.md). Dirty workspace / active benchmark hygiene: [docs/WORKSPACE_MANAGEMENT.md](docs/WORKSPACE_MANAGEMENT.md). **`skills/*/SKILL.md`** = scenario routing and handoffs (link to rules, not restate).

## Read first (live work)

| Document | Role |
|----------|------|
| [docs/rules/safety-policy.md](docs/rules/safety-policy.md) | Hard bans, deck truth, vision |
| [docs/rules/workflows.md](docs/rules/workflows.md) | Tool order, end-to-end sequences |
| [docs/rules/error-response.md](docs/rules/error-response.md) | Error taxonomy, recovery branches |
| [docs/architecture/architecture.md](docs/architecture/architecture.md) | Layers (diagrams on demand) |

## Skills

| Skill | When to use |
|-------|-------------|
| `opentrons-experiment-run` | Default: new runs, status, resume, recovery |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment — before authoring |
| `opentrons-protocol-author` | Write or revise Python protocols |
| `opentrons-protocol-verify` | Local doctor / analyze / simulate (no MCP) |
| `opentrons-simulation-repair` | Simulate → parse → edit loop |
| `opentrons-protocol-library` | **On demand** — user asks to search the 833-protocol catalog |
| `opentrons-robot-lan` | **On demand** — MCP unavailable, MCP debug, or explicit HTTP route ([safety-policy](docs/rules/safety-policy.md)) |

MCP server: `opentrons-lab-mcp` at `mcp-servers/opentrons-mcp/`.

## On demand (not rules)

| Document | Role |
|----------|------|
| [docs/guides/agent-behavior.md](docs/guides/agent-behavior.md) | Status labels, clarification tone, refusal phrasing |
| [docs/guides/experiment-sop.md](docs/guides/experiment-sop.md) | Experiment-type heuristics |
| [docs/runbooks/](docs/runbooks/) | Live readiness, restart, probe, vision checklist |
| [docs/architecture/diagrams/README.md](docs/architecture/diagrams/README.md) | SVG diagrams |
