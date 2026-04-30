# Architecture (canonical)

This document is the **canonical** text description of how Opentrons-Lab-Agent is layered. Visual diagrams live under `docs/diagrams/` (SVG).

## Layers

1. **Plugin** — `.claude-plugin/plugin.json` loads skills into the agent host.
2. **Skills** — `skills/*/SKILL.md` encode operator flows (intent, authoring, verify, run, recovery).
3. **MCP server** — `mcp-servers/opentrons-mcp/` exposes tools: simulation gate, live robot control, session/restart helpers, optional vision.
4. **Persisted state** — session deck snapshots and append-only result logs under paths documented in the MCP server README (configurable via `OPENTRONS_SESSION_STATE_DIR`, `OPENTRONS_RESULT_LOG_DIR`).
5. **Optional vision** — local `vision_check` / camera artifacts; **observation-only**, never overrides committed deck truth (see `docs/safety-policy.md` and `docs/vision-acceptance.md`).

## Related docs

| Topic | Document |
|-------|----------|
| End-to-end sequences | [workflows.md](workflows.md) |
| Safety and hard bans | [safety-policy.md](safety-policy.md) |
| Error categories and recovery branches | [error-response.md](error-response.md) |
| Restart / reconcile operator steps | [restart-review-runbook.md](restart-review-runbook.md) |
| Diagrams (SVG) | [diagrams/README.md](diagrams/README.md) |
