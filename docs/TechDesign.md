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
- Phase 2 also now has an executable protocol-recovery tool:
  - `recover_tip_pickup` performs `pickUpTip(..., intent="fixit") -> resume-from-recovery`
  - `execute_protocol_recovery` generalizes that path into a protocol-run recovery executor for multiple supported branches
- Phase 3 is now stricter at the real-run boundary:
  - `run_protocol` must pass local doctor + simulation + parsed gate checks before it can upload or start a run

## Real validation notes

- Real Flex `run_protocol` validation passed with `mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py`.
- Live read-only `DESTINATION_OCCUPIED` suggestion validation returned concrete candidate slots from the current deck layout.
- Real Flex `TIP_PHYSICALLY_MISSING` recovery validation passed with `mcp-servers/opentrons-mcp/examples/flex_tip_recovery_validation.py`:
  - first `pickUpTip(A1)` entered `awaiting-recovery`
  - `recover_tip_pickup` then succeeded with `B1`
  - `resume-from-recovery` let the original protocol end in `succeeded`
- The generalized recovery executor is now covered by local tests for:
  - tip fallback
  - occupied-destination alternative slot retry
  - module-blocker wait-and-resume
- A deliberately broken local protocol is now blocked by the simulation gate before any real robot action begins.

For the full roadmap and design rationale, keep using the workspace root `TechDesign.md`. This file exists so the repo branch can carry the key design updates that were implemented here.
