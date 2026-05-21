# Opentrons Lab MCP

This folder contains the canonical MCP server for `Opentrons-Lab-Agent`: local simulation, live robot control, session/restart helpers, and optional vision.

## Canonical repo documentation

| Topic | Path |
|-------|------|
| Workflows | [`../../docs/rules/workflows.md`](../../docs/rules/workflows.md) |
| Safety policy | [`../../docs/rules/safety-policy.md`](../../docs/rules/safety-policy.md) |
| Errors, recovery branches, Phase 2/4 policy | [`../../docs/rules/error-response.md`](../../docs/rules/error-response.md) |
| Architecture | [`../../docs/architecture/architecture.md`](../../docs/architecture/architecture.md) |

Do not duplicate long policy text here; link the files above.

## Why this server exists

The repository already includes Python-first skills for writing protocols, verifying locally, and LAN fallback. This server adds a tight tool loop for agents:

1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. retry until pass

## Tool surface (representative)

Live and orchestration tools include: `robot_health`, `robot_status`, `module_status`, `get_slot_occupation`, `list_tip_candidates`, `suggest_next_tip_well`, `is_home_safe`, `preflight_run_setup`, `live_readiness_check`, `reconcile_state`, `parse_error`, `suggest_recovery_action`, `create_run_context`, command helpers (`load_pipette`, `load_labware`, `load_module`, module controls, `move_labware`, `cleanup_motion`), camera/file helpers, `get_protocols`, `upload_protocol`, `run_protocol`, `execute_protocol_recovery`, `recover_tip_pickup`, run control, `run_history`, `experiment_history`, `restart_review`, `safe_next_action`, `probe_wells`, `health_check`, plus simulation tools above. Optional: `vision_check`, `analyze_image_with_kimi`.

See `index.js` for the authoritative tool list and schemas.

## Feature maturity

| Feature / tool | Status | Notes |
|----------------|--------|--------|
| Simulation gate inside `run_protocol` (`doctor_local_runtime` → `simulate_protocol` → `parse_simulation_output`) | **stable** | Blocks real **play** when simulation fails. |
| `live_readiness_check` | **stable** | Read-only live go/no-go gate; combines local runtime health, restart guidance, live status, and optional preflight. |
| `preflight_run_setup` | **stable** | After run creation: reconciliation, readiness, Flex-oriented declared deck vs live snapshot. Overrides: `skip_preflight`, `skip_preflight_deck_diff`. |
| Core live tools (`robot_status`, `reconcile_state`, recovery chain) | **stable** | See tests under `test/`. |
| `vision_check` | **beta** | Local inference; observation-only JSON. Install: `uv sync --extra vision`. Checklist: [`../../docs/runbooks/vision-acceptance.md`](../../docs/runbooks/vision-acceptance.md). |
| `analyze_image_with_kimi` | **beta** | External chat API; deck-level hints, not liquid-volume truth. |
| `probe_wells` | **experimental** | Default simulate-only; live motion requires `OPENTRONS_ENABLE_PROBE_WELLS=1` and operator sign-off ([`../../docs/runbooks/probe-wells-live-validation.md`](../../docs/runbooks/probe-wells-live-validation.md)). |

## Operator runbooks (this repo)

- Restart / reconcile: [`../../docs/runbooks/restart-review-runbook.md`](../../docs/runbooks/restart-review-runbook.md)
- Live `probe_wells` validation: [`../../docs/runbooks/probe-wells-live-validation.md`](../../docs/runbooks/probe-wells-live-validation.md)
- Vision acceptance: [`../../docs/runbooks/vision-acceptance.md`](../../docs/runbooks/vision-acceptance.md)

## Implementation notes (MCP-specific)

- **Breaking:** Older integrations that called `get_run_status` must use **`run_history`** (same inputs: `robot_ip`, `run_id`, optional `page_length`).
- This directory is the canonical `opentrons-lab-mcp` implementation. Community projects (e.g. `yerbymatey/opentrons-mcp`) are reference-only.
- Pair with `opentrons-document-mcp-server` for Python API lookup.
- Live-state tools return a common envelope: `success`, `data`, `error`, `hardware_snapshot`, `state_revision`, `run_id`, `session_id`, `timestamp`.
- `run_protocol` gates real **play** with (1) the simulation chain above and (2) `preflight_run_setup` after run creation unless skipped via explicit flags.
- `health_check` remains an environment/developer probe. Use `live_readiness_check` for operator-facing live gating before `create_run` or `play`.
- Session `DeckState` lives under `data/session-state/` (override: `OPENTRONS_SESSION_STATE_DIR`). Append-only result logs under `data/result-logs/` (`OPENTRONS_RESULT_LOG_DIR`).
- `experiment_history` filters: `session_id`, `run_id`, `tool_name`, `status`, `limit`, optional `event_kind`. **Logs are historical evidence**; committed deck truth is session state + live `reconcile_state` / `robot_status`.
- Tests may set `OPENTRONS_RESULT_LOG_DIR` and `OPENTRONS_SESSION_STATE_DIR` (see `test/experiment-history.test.js`, `test/restart-reconcile.test.js`).
- `capture_preview_image` writes a local file and returns the path (no binary in MCP payloads). `capture_run_image` uses the robot queue; some builds may not return a downloadable `fileId` immediately — use `list_data_files` / `download_data_file` when needed.
- Camera capability gaps (e.g. POST endpoints missing on some Flex builds) are reported explicitly instead of failing silently.

## Recovery policy (Phase 2 / Phase 4)

Full rules and the error table live in [`../../docs/rules/error-response.md`](../../docs/rules/error-response.md).

## Real Response Samples

### `run_protocol` (abbreviated)

```json
{
  "success": true,
  "data": {
    "final_status": "succeeded",
    "requires_attention": false,
    "final_run_history": {
      "command_counts": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
      }
    }
  }
}
```

### `recover_tip_pickup` (abbreviated)

```json
{
  "success": true,
  "data": {
    "recovered_well": "B1",
    "final_run_history": {
      "status": "succeeded"
    }
  }
}
```

`recover_tip_pickup` remains a compatibility wrapper. Prefer `execute_protocol_recovery` for supported branches (tip `fixit`, `moveLabware` alternative slot, module wait-then-resume).

### `run_protocol` blocked by simulation gate (abbreviated)

```json
{
  "success": false,
  "data": {
    "blocked_real_execution": true,
    "gate_stage": "simulate_protocol",
    "parsed_simulation_output": {
      "success": false,
      "issues": [
        { "category": "SYNTAX_OR_IMPORT" }
      ]
    }
  }
}
```

### `suggest_recovery_action` for occupied destination (abbreviated)

```json
{
  "success": true,
  "data": {
    "recovery": {
      "action": "suggest_new_destination_slot",
      "escalate_to_human": true,
      "candidate_destination_slots": [
        { "slot_name": "A2", "confidence": "low" },
        { "slot_name": "B2", "confidence": "low" },
        { "slot_name": "C2", "confidence": "low" }
      ]
    }
  }
}
```

## Install

```bash
cd mcp-servers/opentrons-mcp
npm install
```

## Test

```bash
npm test
```

### What the tests prove

Policy mapping: [`../../docs/rules/error-response.md`](../../docs/rules/error-response.md).

| Area | Primary test files |
|------|-------------------|
| `DESTINATION_OCCUPIED` decision + summaries | `test/decision.test.js` |
| `moveLabware` recovery execution | `test/recover-tip-pickup.test.js` |
| Safe-home / `is_home_safe` inputs | `test/decision.test.js` |
| Hard stops (`DECK_COLLISION`, `UNKNOWN`, collision parse) | `test/decision.test.js` |
| Simulation gate (`run_protocol`) | `test/run-protocol.test.js`, `test/experiment-history.test.js` |
| Log query (`experiment_history`) | `test/experiment-history.test.js` |
| Restart: reconcile flag vs historical log | `test/restart-reconcile.test.js` |
| `restart_review` + `safe_next_action` | `test/restart-review.test.js` |
| `preflight_run_setup` | `test/preflight-run-setup.test.js` |
| Experimental `probe_wells` | `test/probe-wells.test.js` |
| `vision_check` input validation | `test/vision-check.test.js` |

## Example MCP config

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"]
    },
    "opentrons-docs": {
      "command": "npx",
      "args": ["-y", "opentrons-document-mcp-server@latest"]
    }
  }
}
```

If your simulation environment is not the default `python3`, use the repo-local `./.venv/bin/python`, set `OPENTRONS_PYTHON`, or pass `python_executable` to the simulation tools.
