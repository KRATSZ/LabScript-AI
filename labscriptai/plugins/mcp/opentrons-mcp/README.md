# Opentrons robot backend

Node backend for **`labscriptai chat`** (`mcp_adapter.call_tool` → `TOOL_HANDLERS` in `index.js`). Not a Cursor plugin and not a second CLI.

```bash
cd labscriptai/plugins/mcp/opentrons-mcp && npm install
```

User entry and health check: repo-root [`README.md`](../../../../README.md). Safety / recovery: [`../../skills/`](../../skills/) (`safety-brief`, `error-taxonomy`, `recovery-playbooks`, `pressure-trace`).

Override the entry with `LABSCRIPTAI_MCP_INDEX=/abs/path/to/index.js` if needed. Live pressure sampling is opt-in (`OPENTRONS_ENABLE_PRESSURE_TRACE=1`) and never authorizes play/resume.

Pressure evidence is advisory and cannot override controller state. Tools: `run_pressure_trace`, `fetch_pressure_trace`, `analyze_pressure_trace`.

| Feature / tool | Status | Notes |
|---|---|---|
| `run_pressure_trace` | stable | Generate hover/z_trace/during_probe protocol; `execute_on_robot` opt-in |
| `fetch_pressure_trace` | stable | Pull PRESSURE_CSV_B64 comments from a finished run |
| `analyze_pressure_trace` | stable | Feature extraction; observation-only |
| Simulation gate inside `run_protocol` (`doctor_local_runtime` → `simulate_protocol` → `parse_simulation_output`) | **stable** | Blocks real **play** when simulation fails. |
| `live_readiness_check` | **stable** | Read-only live go/no-go gate; combines local runtime health, restart guidance, live status, and optional preflight. |
| `preflight_run_setup` | **stable** | After run creation: reconciliation, readiness, Flex-oriented declared deck vs live snapshot. Overrides: `skip_preflight`, `skip_preflight_deck_diff`. |
| Core live tools (`robot_status`, `reconcile_state`, recovery chain) | **stable** | See tests under `lib/*.test.js`. |
| `vision_check` | **beta** | Local inference; observation-only JSON. |
| `analyze_image_with_kimi` | **beta** | External chat API; deck-level hints, not liquid-volume truth. |
| `analyze_image_with_ark` | **beta** | Volcengine Ark (Doubao VLM) second opinion; reads `ARK_API_KEY` from env or `automation/.env`. |
| `deck_vision_check` | **beta** | Preflight orchestration: capture → YOLO → conditional Ark VLM. |
| `list_critical_probe_targets` | **stable** | Read-only critical well list for Phase 3c LPD probing. |
| `probe_wells` | **stable (opt-in live)** | Default simulate-only; live motion requires `OPENTRONS_ENABLE_PROBE_WELLS=1` and operator sign-off. |
| `apply_liquid_probe_results` | **stable** | Bookkeeping only; writes `observed_presence` / `observed_height_mm` / estimated `volume_ul` (height→volume for `nest_12_reservoir_15ml` and destination `nest_96_wellplate_200ul_flat`). No destination volume stop-gate. |

## Operator guidance

- Load `../../skills/recovery-playbooks.md` before any live recovery action.
- Pressure traces are evidence only; they never authorize play, resume, or
  liquid-state writeback.
- Run `npm test` from this directory after changing the backend.

## Implementation notes (MCP-specific)

- **Breaking:** Older integrations that called `get_run_status` must use **`run_history`** (same inputs: `robot_ip`, `run_id`, optional `page_length`).
- This directory is the canonical `opentrons-lab-mcp` implementation. Community projects (e.g. `yerbymatey/opentrons-mcp`) are reference-only.
- Pair with `opentrons-document-mcp-server` for Python API lookup.
- Live-state tools return a common envelope: `success`, `data`, `error`, `hardware_snapshot`, `state_revision`, `run_id`, `session_id`, `timestamp`.
- `run_protocol` gates real **play** with (1) the simulation chain above and (2) `preflight_run_setup` after run creation unless skipped via explicit flags.
- `health_check` remains an environment/developer probe. Use `live_readiness_check` for operator-facing live gating before `create_run` or `play`.
- Session `DeckState` lives under `.plugin-data/session-state/` (override: `OPENTRONS_SESSION_STATE_DIR`). Append-only result logs under `.plugin-data/result-logs/` (`OPENTRONS_RESULT_LOG_DIR`).
- `experiment_history` filters: `session_id`, `run_id`, `tool_name`, `status`, `limit`, optional `event_kind`. **Logs are historical evidence**; committed deck truth is session state + live `reconcile_state` / `robot_status`.
- Tests may set `OPENTRONS_RESULT_LOG_DIR` and `OPENTRONS_SESSION_STATE_DIR` (see the runtime-watch tests under `lib/`).
- `capture_preview_image` writes a local file and returns the path (no binary in MCP payloads). `capture_run_image` uses the robot queue; some builds may not return a downloadable `fileId` immediately — use `list_data_files` / `download_data_file` when needed.
- Camera capability gaps (e.g. POST endpoints missing on some Flex builds) are reported explicitly instead of failing silently.

## Recovery policy (Phase 2 / Phase 4)

Full rules and the error table live in [`../../skills/error-taxonomy.md`](../../skills/error-taxonomy.md) and [`../../skills/recovery-playbooks.md`](../../skills/recovery-playbooks.md).

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

## Test

```bash
npm test
```

### What the tests prove

Policy mapping: [`../../skills/error-taxonomy.md`](../../skills/error-taxonomy.md).

| Area | Primary test files |
|------|-------------------|
| `DESTINATION_OCCUPIED` decision + summaries | `lib/decision.test.js` |
| `moveLabware` recovery execution | `lib/liquid-source-fixit-recovery.test.js` |
| Safe-home / `is_home_safe` inputs | `lib/decision.test.js` |
| Hard stops (`DECK_COLLISION`, `UNKNOWN`, collision parse) | `lib/decision.test.js` |
| Simulation gate (`run_protocol`) | `lib/tool-registry.test.js` |
| Log query (`experiment_history`) | `lib/runtime-watch/*.test.js` |
| `preflight_run_setup` | `lib/preflight-run-setup.test.js` |
| Experimental `probe_wells` | `lib/probe-geometry.test.js` |
| Pressure evidence | `lib/pressure-trace.test.js` |

## Example MCP config

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/labscriptai/plugins/mcp/opentrons-mcp/index.js"]
    },
    "opentrons-docs": {
      "command": "npx",
      "args": ["-y", "opentrons-document-mcp-server@latest"]
    }
  }
}
```

If your simulation environment is not the default `python3`, use the repo-local `./.venv/bin/python`, set `OPENTRONS_PYTHON`, or pass `python_executable` to the simulation tools.
