# LabscriptAI

Primary entry for live work: the lean package under **`labscriptai/`**.

Install: `cd labscriptai && pip install -e .` then `(cd plugins/mcp/opentrons-mcp && npm install)`. See [`README_AGENT_MIN.md`](README_AGENT_MIN.md).

Runtime policy (link, do not copy): [`docs/rules/`](docs/rules/) — map in [`docs/README.md`](docs/README.md).

## Read first (live work)

| Document | Role |
|----------|------|
| [`README_AGENT_MIN.md`](README_AGENT_MIN.md) | Colleague install, CLI, MCP |
| [`docs/rules/safety-policy.md`](docs/rules/safety-policy.md) | Hard bans, deck truth, vision |
| [`docs/rules/workflows.md`](docs/rules/workflows.md) | Tool order, end-to-end sequences |
| [`docs/rules/error-response.md`](docs/rules/error-response.md) | Error taxonomy, recovery branches |

## Lean agent surface

| Piece | Location |
|-------|----------|
| CLI (`labscriptai doctor` / `chat`) | `labscriptai/agent/` |
| Skills (on-demand via `skill` tool) | `labscriptai/plugins/skills/*.md` |
| Vendored MCP | `labscriptai/plugins/mcp/opentrons-mcp/` |
| Package tests | `labscriptai/tests/` |

Root `benchmarks/`, `reference-protocols/`, `mcp-servers/`, and duplicate operator `skills/` trees were removed from this branch; do not reintroduce them for colleague runs.

## On demand

| Document | Role |
|----------|------|
| [`docs/guides/agent-behavior.md`](docs/guides/agent-behavior.md) | Status labels, clarification tone |
| [`docs/runbooks/`](docs/runbooks/) | Live readiness, restart, probe |
| [`docs/architecture/architecture.md`](docs/architecture/architecture.md) | Layers |
