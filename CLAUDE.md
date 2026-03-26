# Opentrons-Lab-Agent Guide

## Project Role

`Opentrons-Lab-Agent/` is the canonical Claude Code plugin-style implementation for the Flex lab automation work in this workspace.

- Plugin metadata lives in `.claude-plugin/plugin.json`.
- Plugin skills live in `skills/`.
- The canonical MCP server lives in `mcp-servers/opentrons-mcp/`.

## Canonical Names

Keep documentation and examples aligned with the current skill directories:

- `opentrons-protocol-author`
- `opentrons-protocol-verify`
- `opentrons-robot-lan`
- `opentrons-simulation-repair`
- `opentrons-experiment-run`

Use `opentrons-lab-mcp` as the MCP package/server name, even though the implementation directory is `mcp-servers/opentrons-mcp/`.

## Runtime Principles

- Python-first for protocol authoring.
- Simulation-first before any real robot execution.
- Runtime safety and truthful state tracking live in MCP code plus persisted session state.
- Skills are guidance only and must not be treated as authoritative runtime state.
- Vision is optional and should only augment runtime decisions.

## Implementation Boundaries

- `run_protocol` must stay simulation-gated.
- Recovery logic should prefer small, explicit query/decision tools over giant state blobs.
- `DeckState`, tip bookkeeping, reconciliation, and recovery decisions belong in MCP/server code.
- Camera and image analysis should be documented as capability-gated because robot software support varies.

## Update Discipline

When changing tool names, packaging, or major workflow assumptions, update:

1. `README.md`
2. `.mcp.json`
3. `mcp-servers/opentrons-mcp/README.md` when user-facing MCP behavior changed
4. `Developdocs/TechDesign.md` or the corresponding file under `Developdocs/design/`
5. `Developdocs/design/phase-2-3-acceptance.md` when changing Phase 2/3 rules, Phase 4 minimal scope, or test/acceptance mapping
