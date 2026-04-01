# Opentrons Lab MCP

This folder contains a practical MCP server for `Opentrons-Lab-Agent`.

It is intentionally focused on the highest-value workflow for Claude Code:

- a few useful live robot control tools
- local `opentrons.simulate` integration
- structured simulation parsing for multi-round protocol repair

## Why this server exists

The repository already includes Python-first skills for:

- writing protocols
- verifying protocols locally
- controlling a robot over LAN

This MCP server adds a tighter tool loop for agent orchestration:

1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. retry until pass

It also exposes a compact set of live tools:

- `robot_health`
- `robot_status`
- `module_status`
- `get_slot_occupation`
- `list_tip_candidates`
- `suggest_next_tip_well`
- `is_home_safe`
- `preflight_run_setup` *(in development)*
- `reconcile_state`
- `parse_error`
- `suggest_recovery_action`
- `create_run_context`
- `load_pipette`
- `load_labware`
- `load_module`
- `control_temperature_module`
- `control_heater_shaker`
- `control_thermocycler`
- `move_labware`
- `cleanup_motion`
- `camera_status`
- `configure_camera`
- `capture_preview_image`
- `capture_run_image`
- `list_data_files`
- `download_data_file`
- `analyze_image_with_kimi`
- `vision_check` *(in development)*
- `get_protocols`
- `upload_protocol`
- `run_protocol`
- `execute_protocol_recovery`
- `recover_tip_pickup`
- `create_run`
- `control_run`
- `get_runs`
- `run_history`
- `experiment_history`
- `restart_review`
- `probe_wells`
- `health_check`

## Operator runbooks (this repo)

- Restart / reconcile: `../../docs/restart-review-runbook.md`
- Live `probe_wells` validation: `../../docs/probe-wells-live-validation.md`

## Notes

- **Breaking note:** older integrations that called `get_run_status` must switch to **`run_history`** (same inputs: `robot_ip`, `run_id`, optional `page_length`). The duplicate alias was removed to avoid two names for one behavior.
- This folder is the canonical `opentrons-lab-mcp` implementation for the repository. Community MCP projects such as `yerbymatey/opentrons-mcp` are reference material only.
- The tool surface is inspired by the community project `yerbymatey/opentrons-mcp`, but reduced to the parts that are most useful for this repository's simulation-first workflow.
- For API documentation lookup, pair this server with `opentrons-document-mcp-server`.
- Live-state tools return a common envelope with `success`, `data`, `error`, `hardware_snapshot`, `state_revision`, `run_id`, `session_id`, and `timestamp`.
- `run_protocol` hard-gates real **play** with (1) `doctor_local_runtime -> simulate_protocol -> parse_simulation_output` and (2) `preflight_run_setup` after run creation (reconciliation flag, robot readiness, Flex-oriented protocol deck declaration vs live snapshot). Use `skip_preflight` or `skip_preflight_deck_diff` only as explicit operator overrides.
- Session-level `DeckState` snapshots are persisted under `data/session-state/` so tip bookkeeping and reconciliation survive MCP restarts.
- Phase 4 MVP persists compact result logs under `data/result-logs/`. `experiment_history` filters: `session_id`, `run_id`, `tool_name`, `status`, `limit`, and optional `event_kind`. **Logs are historical evidence;** committed deck truth stays in `data/session-state/` and live `robot_status` / `reconcile_state`.
- Tests may set `OPENTRONS_RESULT_LOG_DIR` and `OPENTRONS_SESSION_STATE_DIR` to isolate JSONL session and log files (see `test/experiment-history.test.js`, `test/restart-reconcile.test.js`).
- `capture_preview_image` saves the preview locally and returns the artifact path so a later human step or vision analyzer can consume it without embedding binary image data into MCP responses.
- `capture_run_image` uses the robot command queue (`captureImage`) and attempts to download the generated data file immediately; on the current Flex software, maintenance-context captures may succeed without returning a downloadable `fileId`, so the server also exposes `list_data_files` and `download_data_file` for working with historical robot images.
- `analyze_image_with_kimi` calls SiliconFlow's OpenAI-compatible chat API and is intended for deck-level visual analysis, not liquid-volume truth.
- `vision_check` runs **local Ultralytics YOLOE** (`yoloe-26s-seg.pt` by default) via `scripts/vision_check.py` in the project Python environment. It returns **observation-only** JSON (`summary`, `slot_mapping`, `observed_items`, `slot_observations`, `mismatches`, `uncertainties`, `needs_human_review`, `annotated_image_path`). It does **not** mutate `data/session-state/`. Install deps from repo root: `uv sync --extra vision` (includes **CLIP** + `ultralytics`; YOLOE also needs `mobileclip2_b.ts` — auto-downloaded or placed under `weights/` per repo `weights/README.md`). Override weights with `weights` or `OPENTRONS_YOLOE_WEIGHTS`. `mode: deck` maps detections to Flex 12 slots using **optional deck homography** (`deck_corners_norm` or `labels/<stem>.labels.json` → `optional_deck_corners_norm`) or a uniform image-grid fallback; empty slots are geometric (no detection in cell). Default YOLOE prompts are Flex-oriented (yellow/teal tip racks, plates, thermocycler/heater-shaker wording, trash); override with `class_prompts` + `canonical_labels` (same length). For quick visual iteration use `scripts/yoloe_deck_preview.py`; batch MVP JPEGs with `uv run python scripts/batch_vision_deck_mvp.py` (env `OPENTRONS_VISION_CONF`, `OPENTRONS_YOLOE_PROMPTS_JSON`). `mode: tiprack` is a reserved stub until rack-local analysis ships. For offline labeling batches, `scripts/fetch_robot_camera_samples.py` pulls recent `dataFiles` JPEGs.
- On the current validated Flex (`10.31.2.149:31950`, API `8.8.1`), `GET /camera` is available, while the POST camera endpoints currently return `404`; the MCP therefore reports these as capability/version gaps instead of silently pretending preview capture is supported everywhere.
- Real-Flex validation now includes a physical gripper move of `corning_96_wellplate_360ul_flat` from `C3` to `B3`, followed by successful `cleanup_motion`.
- Real-Flex validation also includes runtime error parsing for `TIP_PHYSICALLY_MISSING`, `PROTOCOL_SETUP_ERROR`, `DESTINATION_UNAVAILABLE`, and a software-occupied `DESTINATION_OCCUPIED` move failure.
- Real-Flex validation now also includes `run_protocol` with `examples/flex_noop_protocol.py`, which completed `upload -> create_run -> play -> poll` and returned a final `succeeded` run snapshot.
- Real-Flex validation now also includes `run_protocol` with `examples/flex_tip_recovery_validation.py`, which entered `awaiting-recovery` on `pickUpTip(A1)` and exposed a real `TIP_PHYSICALLY_MISSING` branch.
- The server now exposes `execute_protocol_recovery` as the general protocol-run recovery executor for supported automatic branches.
- Real-Flex validation now also includes `recover_tip_pickup`, which executed `pickUpTip(B1, intent="fixit")` and `resume-from-recovery`, then allowed the original protocol to finish with `status = succeeded`.
- Phase 2 live read-only validation now confirms that `suggest_recovery_action(error_category="DESTINATION_OCCUPIED")` can return concrete alternative slots from the real deck layout while still escalating when those candidates are only low-confidence `unknown` slots.
- Phase 3 negative validation now confirms that a broken local protocol is blocked at simulation time and never starts a real robot run.
- Phase 2 and 3 closeout now also harden the rule boundary: collision-class and unresolved-ambiguity failures are explicit hard stops, and `is_home_safe` keeps `home` blocked whenever tips, pending cleanup, or reconciliation blockers remain.
- `probe_wells` is now available as an experimental helper that generates a temporary protocol and simulates it locally by default. Live robot probing stays disabled unless the operator explicitly enables `OPENTRONS_ENABLE_PROBE_WELLS=1`.

## Phase 2/3 acceptance (frozen) and Phase 4 minimal scope

Canonical wording lives in `Developdocs/design/phase-2-3-acceptance.md` (workspace root). This server implements:

**Phase 2 — three rules**

1. **`DESTINATION_OCCUPIED`** — Protocol error recovery: destination changes stay **human-reviewed** (`escalate_to_human: true`). Outside recovery: escalation is **off** only when at least one alternative has `confidence: "high"`; unknown/low-confidence slots still escalate. Automatic `moveLabware` fixit only through `execute_protocol_recovery` with an explicit slot.
2. **`is_home_safe`** — `auto_home_allowed` only with **no** robot blockers, **no** tip/cleanup backlog, **no** `needs_reconciliation`.
3. **Hard stops** — `HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN`: **no** autonomous continuation; escalate.

**Phase 4 — three pillars only**

1. Append-only **result logs** for: `run_protocol`, `control_run`, `reconcile_state`, `execute_protocol_recovery`, `recover_tip_pickup`, plus experimental `probe_wells` lines (`probe_preview` / `probe_execution`).
2. **`experiment_history`** query API (see Notes).
3. **`restart_review`** — read session file + recent result logs + structured guidance; optional `robot_ip` for live home-safety preview. If `needs_reconciliation`, follow `guidance` and run `reconcile_state` before autonomous motion.

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

`recover_tip_pickup` remains available as a compatibility wrapper. New integrations should prefer `execute_protocol_recovery`, which currently supports:

- tip fallback with `pickUpTip(..., intent="fixit")`
- alternative-slot retry for `moveLabware`
- module-blocker recovery by waiting until blockers clear, then resuming the run

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

### What the tests prove (Phase 2/3 and Phase 4)

Full mapping: `Developdocs/design/phase-2-3-acceptance.md`.

| Area | Primary test files |
|------|-------------------|
| `DESTINATION_OCCUPIED` decision + summaries | `test/decision.test.js` |
| `moveLabware` recovery execution | `test/recover-tip-pickup.test.js` |
| Safe-home / `is_home_safe` inputs | `test/decision.test.js` |
| Hard stops (`DECK_COLLISION`, `UNKNOWN`, collision parse) | `test/decision.test.js` |
| Simulation gate (`run_protocol`) | `test/run-protocol.test.js`, `test/experiment-history.test.js` |
| Log query (`experiment_history`) | `test/experiment-history.test.js` |
| Restart: reconcile flag vs historical log | `test/restart-reconcile.test.js` |
| `restart_review` bundle + optional live preview + suggested tool order + handler-level ordering | `test/restart-review.test.js` |
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

If your simulation environment is not on the default `python3`, either:

- rely on the repository-local `./.venv/bin/python` auto-detection, or
- set `OPENTRONS_PYTHON`, or
- pass `python_executable` to the simulation tools.
