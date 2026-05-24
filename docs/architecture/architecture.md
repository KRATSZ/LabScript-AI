# Architecture (canonical)

This document is the **canonical** text description of how Opentrons-Lab-Agent is layered. Visual diagrams live under `docs/architecture/diagrams/` (SVG).

## Layers

1. **Python core** — `src/labscriptai/`: unified agent loop, gatekeeper, benchmark runners, runtime adapters.
2. **Operator flows** — `skills/*/SKILL.md` plus helper scripts (verify, protocol library, robot LAN); benchmark KB in `src/labscriptai/authoring/skills/`.
3. **MCP server** — `mcp-servers/opentrons-mcp/` exposes tools: simulation gate, live robot control, session/restart helpers, optional vision. Wired from Python via `OpentronsMcpRuntimeAdapter` and optional IDE config in `.mcp.json`.
4. **Persisted state** — session deck snapshots and append-only result logs under paths documented in the MCP server README (configurable via `OPENTRONS_SESSION_STATE_DIR`, `OPENTRONS_RESULT_LOG_DIR`).
5. **Optional vision** — local `vision_check` / camera artifacts; **observation-only**, never overrides committed deck truth (see `docs/rules/safety-policy.md` and `docs/runbooks/vision-acceptance.md`).

Repository folder roles: [`../REPO_LAYOUT.md`](../REPO_LAYOUT.md).

## Related docs

| Topic | Document |
|-------|----------|
| End-to-end sequences | [workflows.md](../rules/workflows.md) |
| Safety and hard bans | [safety-policy.md](../rules/safety-policy.md) |
| Error categories and recovery branches | [error-response.md](../rules/error-response.md) |
| Restart / reconcile operator steps | [restart-review-runbook.md](../runbooks/restart-review-runbook.md) |
| Diagrams (SVG) | [diagrams/README.md](diagrams/README.md) |
| Unified agent loop design | [agent_architecture.md](agent_architecture.md) |
