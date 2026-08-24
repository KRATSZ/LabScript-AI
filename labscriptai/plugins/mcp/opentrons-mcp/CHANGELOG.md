# Changelog — opentrons-mcp

## Unreleased

### Consumable labware offsets (workspace ledger)

- Added workspace true source at `.labscriptai/offsets/{device_id}.json` (`device_id` = robot health `serialNumber`).
- MCP tools:
  - `record_labware_offset` (`upsert` / `disable` / `revert`): writes one ledger entry, optional memory changelog, and on upsert/revert syncs via `POST /labwareOffsets`.
  - `list_labware_offsets`: read-only ledger + robot store + merge preview + diff.
  - `import_robot_labware_offsets`: post-LPC import from robot store into ledger (`confirm=true` to write; default dry-run).
- `resolveRunLabwareOffsets` auto path (`labware_offsets` **omitted** / `undefined`): merges workspace ledger over robot `GET /labwareOffsets` (same key: workspace wins; `enabled: false` tombstones suppress robot too).
- Explicit `labware_offsets` (including `[]`) still **full replace** — no workspace/robot merge. `[]` means no offsets.
- `preflight_run_setup` / `live_readiness_check`: labware offset coverage vs declared protocol loads (default **warn**; `strict_offset_coverage=true` to fail).

See repo root `consumable-offsets.md`.
