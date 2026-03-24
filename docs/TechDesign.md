# TechDesign Sync Notes

This repository tracks the implementation-facing subset of the workspace `TechDesign.md`.

## Current synced decisions

- The canonical lab MCP implementation is `mcp-servers/opentrons-mcp` in this repository.
- The separate workspace-level `mcp-servers/opentrons-mcp` is community reference code only and should not define this repo's tool names or recovery semantics.
- Phase 1 is now closed around:
  - unified response envelope
  - `run_protocol` (`upload -> create_run -> play -> poll`)
  - documented real response samples
- Phase 2 is now stronger for occupied-destination recovery:
  - `suggest_recovery_action` can return alternative destination slots
  - it still escalates when those candidates are only low-confidence `unknown` slots

## Real validation notes

- Real Flex `run_protocol` validation passed with `mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py`.
- Live read-only `DESTINATION_OCCUPIED` suggestion validation returned concrete candidate slots from the current deck layout.

For the full roadmap and design rationale, keep using the workspace root `TechDesign.md`. This file exists so the repo branch can carry the key design updates that were implemented here.
