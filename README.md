# Opentrons Lab Agent Skills

[Agent Skills](https://agentskills.io) are a simple, open format for giving AI agents new capabilities. `Opentrons-Lab-Agent` packages Opentrons-focused skills plus a practical local MCP server for:

- writing and revising Python protocols
- checking whether a local Opentrons runtime can analyze or simulate a protocol
- iteratively repairing protocols through a simulation-first loop
- driving an OT-2 or Flex robot over the LAN HTTP API, with camera-related actions treated as optional capability extensions
- referencing validated protocol-library examples and reusable code patterns

The repository follows Anthropic's public skills conventions: each skill lives in its own folder with a `SKILL.md`, optional `scripts/`, `references/`, and `assets/`, and the repository also includes `.claude-plugin/plugin.json`, `.mcp.json`, and `CLAUDE.md` so the repo can be treated as a Claude Code plugin root.

This repository now bundles a read-only `Protocols-develop` snapshot under `reference-code/Protocols-develop/` for agent reference. External checkouts such as an upstream `opentrons` source tree remain optional inputs.

## Python Environment

This project assumes Python is managed with `uv`.

- create the local virtual environment with `uv venv .venv`
- run commands with `uv run ...`
- avoid mixing in `pip install` or a system Python unless you are intentionally debugging environment issues
- for MCP `vision_check` (local YOLOE), add optional deps: `uv sync --extra vision` from the repo root so `ultralytics` + **CLIP** (Ultralytics fork) are available to the same interpreter MCP uses (`./.venv/bin/python` or `OPENTRONS_PYTHON`). For local protocol/simulation tools that need `opentrons`, use `uv sync --extra protocol` (or `--extra vision --extra protocol` if both; resolve any numpy pin conflicts as prompted by `uv`).

If you want the project-local interpreter explicitly, activate `.venv` created by `uv`, but the default examples below assume `uv run`.

The local MCP server also auto-detects `./.venv/bin/python` when present, so once `opentrons` is installed into the project environment, `doctor_local_runtime` and `simulate_protocol` can usually run without an extra Python path argument.

## Included Skills

- `skills/opentrons-experiment-full`
  - **Default entry** for natural-language routing: new experiments, resume/recovery, and robot status queries (orchestrates the other skills and MCP tools).
- `skills/opentrons-experiment-intent-review`
  - Locks experiment intent vs plate mapping, well lists, and tip/liquid strategy before authoring or live runs.
  - Use for spatial patterns, multi-well designs, and “does this match what I want?” gaps.
- `skills/opentrons-protocol-author`
  - Drafts or refactors Python protocols.
  - Includes a template and concise references for OT-2/Flex metadata, runtime parameters, and `capture_image()`.
- `skills/opentrons-protocol-verify`
  - Wraps local `opentrons` analyze/simulate entry points with environment checks.
  - Detects missing dependencies and missing source layout before trying to execute.
- `skills/opentrons-robot-lan`
  - Talks to a robot over the Opentrons HTTP API.
  - Covers health, camera settings, preview capture, protocol upload, analysis creation, run creation, and run actions.
- `skills/opentrons-simulation-repair`
  - Runs a multi-round `simulate -> parse -> edit -> simulate` loop.
  - Keeps Claude Code honest about what can be fixed by code edit vs what is a runtime blocker.
- `skills/opentrons-protocol-library`
  - References bundled validated protocols and optional external overrides.
  - Useful when the user needs an existing example protocol, a known liquid-handling pattern, or a snippet to adapt.
- `skills/opentrons-experiment-run`
  - **Mandatory state machine** for live runs: intent (when needed) → protocol → simulation gate → preflight → MCP `run_protocol` → MCP recovery → audit.
  - Explicit **no-bypass** rule: simulation failure must not be replaced with blind maintenance HTTP/`curl` loops.

## Included MCP Server

- `mcp-servers/opentrons-mcp`
  - A compact MCP server for practical Claude Code orchestration.
  - Includes live robot tools such as `robot_status`, `module_status`, `get_slot_occupation`, `list_available_slots`, `list_tip_candidates`, `suggest_next_tip_well`, `is_home_safe`, `reconcile_state`, `parse_error`, `suggest_recovery_action`, `create_run_context`, `load_pipette`, `load_labware`, `load_module`, `control_temperature_module`, `control_heater_shaker`, `control_thermocycler`, `move_labware`, `cleanup_motion`, `camera_status`, `configure_camera`, `capture_preview_image`, `capture_run_image`, `list_data_files`, `download_data_file`, `analyze_image_with_kimi`, `vision_check`, `run_history`, `experiment_history`, `restart_review`, `preflight_run_setup`, `probe_wells`, `upload_protocol`, `run_protocol`, `execute_protocol_recovery`, `recover_tip_pickup`, `create_run`, and `control_run`.
  - Adds local tools `doctor_local_runtime`, `simulate_protocol`, and `parse_simulation_output` for simulation-first repair.

This repository's `mcp-servers/opentrons-mcp` is the canonical `opentrons-lab-mcp` implementation. Community MCP servers in the broader workspace are reference material only; they are useful for HTTP surface comparison, but this repo's tool names, recovery rules, and response envelope are defined here.

## Repository Layout

```text
Opentrons-Lab-Agent/
├── .claude-plugin/plugin.json
├── .mcp.json
├── CLAUDE.md
├── examples/
│   └── reference-protocols/
├── mcp-servers/
│   └── opentrons-mcp/
├── docs/
│   ├── restart-review-runbook.md
│   └── probe-wells-live-validation.md
├── reference-code/
│   └── Protocols-develop/
├── skills/
│   ├── opentrons-experiment-full/
│   ├── opentrons-experiment-intent-review/
│   ├── opentrons-protocol-author/
│   ├── opentrons-protocol-library/
│   ├── opentrons-protocol-verify/
│   ├── opentrons-robot-lan/
│   ├── opentrons-simulation-repair/
│   └── opentrons-experiment-run/
├── src/opentrons_lab_agent/
└── tests/
```

## Reference Library Resolution

- `opentrons-protocol-library` resolves its reference library in this order:
  1. `--library`
  2. `OPENTRONS_PROTOCOL_LIBRARY_PATH`
  3. bundled `reference-code/Protocols-develop`
  4. legacy sibling `../Protocols-develop`
- `opentrons-protocol-verify` and the MCP simulation helper use the installed `opentrons` runtime by default.
- If you want to validate against an external source checkout, pass `--workspace-root` or explicit `--api-root` / `--shared-data-root`.
- The bundled reference library is read-only reference material and is not part of the package runtime surface.

## Using It In Codex

Codex reads repository guidance from `AGENTS.md`. Open the repository root so Codex can discover:

- `AGENTS.md` for workflow rules
- `skills/` for authored capabilities
- `examples/reference-protocols/` for small runnable baselines
- `reference-code/Protocols-develop/` for real protocol references

Recommended Codex workflow:

1. search the bundled library with `search`
2. inspect likely matches with `show`
3. pull reusable fragments with `snippet`
4. adapt one of `examples/reference-protocols/` or author a new protocol
5. run `doctor`, then `analyze` or `simulate`
6. use live MCP execution only after local validation passes

## Using It In Claude Code

This repository is already shaped like a Claude Code plugin:

- plugin metadata lives at `.claude-plugin/plugin.json`
- plugin-owned MCP configuration lives at `.mcp.json`
- plugin-local instructions live at `CLAUDE.md`
- skills live under `skills/`
- helper code lives under `src/`

If you use direct skills folders instead of the plugin flow, you can also copy the individual skill directories under `skills/` into the Claude Code skills location used in your environment.

Recommended Claude Code workflow:

1. use `opentrons-protocol-library` to inspect bundled references first
2. pick a close match from `reference-code/Protocols-develop/` or `examples/reference-protocols/`
3. switch to `opentrons-protocol-author` for drafting or edits
4. run `opentrons-protocol-verify` or `opentrons-simulation-repair`
5. use `opentrons-mcp` only when local checks pass

## Developer Docs

**In this repository:**

- `docs/restart-review-runbook.md` — operator checklist after MCP/host restart (`restart_review`, reconcile, live polls).
- `docs/probe-wells-live-validation.md` — prerequisites and minimal scope before live `probe_wells`.

When cloned inside the broader Flexagent workspace, also read:

- `../CLAUDE.md` for workspace-level guidance
- `../Developdocs/TechDesign.md` for the top-level design overview
- `../Developdocs/design/plugin-packaging.md` for Claude Code plugin packaging decisions
- `../Developdocs/design/mcp-surface.md` for MCP tool boundary decisions
- `../Developdocs/design/phase-2-3-acceptance.md` for frozen Phase 2/3 rules and Phase 4 minimal scope

## Local Opentrons Runtime Assumptions

The verification skill is intentionally defensive.

By default it checks the currently selected Python environment and tries to import `opentrons.cli` and `opentrons.simulate` from the installed runtime there.

If you want to validate against an external Opentrons source checkout instead, pass `--workspace-root` or explicit `--api-root` / `--shared-data-root`. In that source-layout mode:

- the verification wrapper injects a minimal `opentrons._version` module at runtime
- the wrapper prepends `opentrons/api/src` and `opentrons/shared-data/python`
- if third-party dependencies are missing, it exits with a clear diagnostic instead of pretending validation succeeded

This keeps Claude Code honest about what can and cannot be executed locally.

## Script Examples

### Check local analyze/simulate readiness

```bash
uv venv .venv
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
```

### Try protocol analysis

```bash
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze path/to/protocol.py -- --check
```

### Search the bundled protocol library

```bash
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  search "magnetic beads" "DNA cleanup"
```

### Inspect one protocol folder

```bash
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  show 00222e
```

### Extract focused snippets from a protocol

```bash
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  snippet 00222e serial plasma
```

### Query a robot on the LAN

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
```

### Upload a protocol and create an analysis

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
```

### Start the local MCP server

```bash
cd mcp-servers/opentrons-mcp
npm install
node index.js
```

## Reference Protocols For Agents

Small runnable examples live under `examples/reference-protocols/`:

- `ot2_minimal_transfer.py`
- `flex_minimal_transfer.py`
- `flex_tip_recovery_reference.py`

Use these as clean starting points for Codex or Claude Code when you need a minimal baseline before adapting a larger protocol-library example.

## Simulation-First Repair Workflow
**Run snapshots:** use **`run_history`** only (`robot_ip`, `run_id`, optional `page_length`). The duplicate `get_run_status` tool was removed from this MCP to avoid two names for the same behavior.

Recommended Claude Code tool order:

0. `search_protocols.py search/show/snippet` when you need a real reference first
1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. `simulate_protocol` again

## Live-State Workflow

Recommended Claude Code tool order before and during live execution:

1. `robot_status`
2. `module_status`
3. `reconcile_state`
4. `get_slot_occupation` / `list_available_slots` / `list_tip_candidates` / `is_home_safe`
5. `create_run_context`
6. `load_pipette` / `load_labware` / `load_module` / `move_labware`
7. `cleanup_motion`
8. `upload_protocol`
9. `create_run`
10. `control_run`
11. `run_history`
12. `suggest_recovery_action`
13. `parse_error` when a live command or run fails

Recent real-Flex validation also covers a physical gripper move:

For the common "upload + create run + play + poll" path, prefer the single `run_protocol` tool. It now enforces a local `doctor_local_runtime -> simulate_protocol -> parse_simulation_output` gate before any real upload or run start, then runs `preflight_run_setup` (reconciliation flag, robot readiness, Flex deck declaration vs live snapshot) after run creation and before play unless `skip_preflight` is set. A simulation or preflight failure blocks physical execution immediately.

### Phase 2/3 acceptance (frozen rules)

Canonical spec: `../Developdocs/design/phase-2-3-acceptance.md`. Summary:

1. **`DESTINATION_OCCUPIED`** — In protocol error recovery, alternative destination suggestions are always **human-reviewed** (`escalate_to_human: true`). Outside recovery, **high-confidence** empty slots can avoid escalation; **low-confidence / unknown** slots stay human-reviewed. **No** automatic reroute outside `execute_protocol_recovery` with an explicit chosen slot.
2. **`is_home_safe` / safe-home** — Automatic `home` is allowed only when there are **no** robot blockers, **no** tip cleanup pending, **no** non-empty cleanup chain, and **`needs_reconciliation` is false**. Otherwise cleanup first and/or run `reconcile_state` before homing.
3. **Hard stops** — `HARDWARE_FAULT`, `DECK_COLLISION`, and **`UNKNOWN`** (unresolved ambiguity): **no** autonomous continuation; escalate for human review.

Phase 3: protocol/source problems stay on the **simulation-edit** loop; physical failures stay on the **recovery** loop (`run_protocol` remains simulation-gated).

### Phase 4 minimal delivery (three pillars)

Scope is intentionally narrow:

1. **Result log** — append-only JSONL under `mcp-servers/opentrons-mcp/data/result-logs/` (override with `OPENTRONS_RESULT_LOG_DIR` in tests).
2. **`experiment_history`** — query logs by `session_id`, `run_id`, `tool_name`, `status`, `limit`, and optional `event_kind`.
3. **Restart / reconcile review** — MCP tool **`restart_review`**: loads persisted **session state** and recent **result logs**, returns **`guidance`** (`reconcile_first`, `suggested_tool_order`, `logs_are_historical_only`). Optional **`robot_ip`** adds a live **home-safety preview**. Same data paths as above (`OPENTRONS_SESSION_STATE_DIR` / `OPENTRONS_RESULT_LOG_DIR` in tests). If `needs_reconciliation` is set, **reconcile before** trusting autonomous motion — logs record history, **not** current deck truth.

**`probe_wells`** writes experimental log lines only; it does not define committed deck state or default recovery.

- `create_run_context` in `maintenance` mode
- `load_labware("corning_96_wellplate_360ul_flat", "C3")`
- `move_labware` from `C3` to `B3`
- `cleanup_motion` returning the gripper and gantry to a clean state
- `parse_error` and `suggest_recovery_action` on real failure cases including:
  - `TIP_PHYSICALLY_MISSING`
  - `PROTOCOL_SETUP_ERROR`
  - `DESTINATION_UNAVAILABLE`
  - `DESTINATION_OCCUPIED` in a software-occupied destination test
- `run_protocol` using `mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py`, which completed `upload -> create_run -> play -> poll` on the real Flex and returned `status = succeeded`
- `run_protocol` using `mcp-servers/opentrons-mcp/examples/flex_tip_recovery_validation.py`, which passed local simulation, then entered real `awaiting-recovery` on `pickUpTip(A1)` with `TIP_PHYSICALLY_MISSING`
- `execute_protocol_recovery`, which is now the general protocol-recovery executor for supported live recovery branches
- `recover_tip_pickup` on that same run, which executed `pickUpTip(B1, intent="fixit") -> resume-from-recovery` and let the original protocol finish with `status = succeeded`
- live read-only Phase 2 validation for `suggest_recovery_action(error_category="DESTINATION_OCCUPIED", target_slot="C1")`, which returned concrete alternative slots from the real deck layout and still marked the branch as human-reviewed because the candidates were only low-confidence `unknown` slots
- negative Phase 3 gate validation with a deliberately broken local protocol, where `run_protocol` stopped at simulation parsing and never started a real robot run
- explicit Phase 2/3 rule hardening, where collision-class and unresolved-ambiguity failures remain hard stops, and destination-occupied recovery in protocol context stays human-reviewed
- experimental `probe_wells`, which currently generates a temporary probe protocol and simulates it locally by default; live robot probing remains operator-gated

All MCP tools return a common response envelope with `success`, `data`, `error`, `hardware_snapshot`, `state_revision`, `run_id`, `session_id`, and `timestamp`.

Phase 4 MVP uses the separate result-log layer under `mcp-servers/opentrons-mcp/data/result-logs/` for **audit and replay**, retrieved through `experiment_history`. Committed deck truth remains in session state and live API polls — see `../Developdocs/design/phase-2-3-acceptance.md` when present, otherwise `docs/restart-review-runbook.md` for the operator path.

### Restart / reconcile runbook (operator)

1. `restart_review` (`session_id`, optional `robot_ip`, optional `limit`).
2. If `guidance.reconcile_first` → `reconcile_state` before other autonomous motion.
3. `robot_status` → `module_status` → if a run matters, `run_history` / `parse_error`.
4. `experiment_history` for audit only — not current deck truth.
5. `is_home_safe` before homing (or use `home_safety_preview` from `restart_review` when `robot_ip` was set).

Full wording: `docs/restart-review-runbook.md`.

The safe-home rule matches Phase 2 acceptance: `home` only when `is_home_safe()` reports no blockers, no cleanup backlog, and no reconciliation flag.

## Real Response Examples

### `robot_status` (real Flex, abbreviated)

```json
{
  "success": true,
  "data": {
    "ready_for_physical_action": true,
    "blockers": [],
    "health_summary": {
      "robot_model": "OT-3 Standard",
      "api_version": "8.8.1",
      "robot_serial": "FLXA2020240921002"
    }
  }
}
```

### `run_protocol` (real Flex noop validation, abbreviated)

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
  },
  "run_id": "5b6cc2d2-ef50-4da6-9f9f-090fc243ccfe",
  "session_id": "5b6cc2d2-ef50-4da6-9f9f-090fc243ccfe"
}
```

### `recover_tip_pickup` (real fixit recovery, abbreviated)

```json
{
  "success": true,
  "data": {
    "recovered_well": "B1",
    "resume_action": {
      "data": {
        "actionType": "resume-from-recovery"
      }
    },
    "final_run_history": {
      "status": "succeeded",
      "has_ever_entered_error_recovery": true
    }
  }
}
```

`recover_tip_pickup` is now kept as a compatibility wrapper around the more general `execute_protocol_recovery` tool. The general executor currently supports:

- `retry_pick_up_tip_with_next_candidate`
- `suggest_new_destination_slot`
- module-blocker `reconcile_state_first` by waiting for blockers to clear before resuming

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

### `suggest_recovery_action` for `DESTINATION_OCCUPIED` (real deck snapshot, abbreviated)

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

## Vision Integration

The repository contains two useful layers for vision-related work:

- Robot-side camera control in `src/opentrons_lab_agent/robot_api.py` for `GET /camera`, `POST /camera`, `POST /camera/cameraSettings`, and `POST /camera/capturePreviewImage`.
- MCP-side camera and image tools in `mcp-servers/opentrons-mcp` for `camera_status`, `configure_camera`, `capture_preview_image`, `capture_run_image`, `list_data_files`, `download_data_file`, `analyze_image_with_kimi`, and `vision_check` (local **YOLOE** / Ultralytics on a saved image; observation-only; does not write session state).

Design rule:

- keep image acquisition inside the robot MCP
- keep image interpretation in a separate analyzer step or future MCP
- pass around a saved `image_path` artifact instead of stuffing binary blobs into tool output

That split makes it easy to start with human inspection now, then later plug in a multimodal model or an external CV service without coupling perception logic to robot control.

### Local YOLOE (`vision_check`)

- **Purpose:** `CHECKDECK` / future `CHECKTIPS` — structured JSON for agents to compare with `reconcile_state` and live APIs, not as committed deck truth.
- **Python:** install optional extras from the repo root: `uv sync --extra vision` (installs `ultralytics`, `opencv-python-headless`, and **CLIP** from `git+https://github.com/ultralytics/CLIP.git`). MCP resolves Python via `OPENTRONS_PYTHON` or `Opentrons-Lab-Agent/.venv/bin/python`.
- **YOLOE text prompts:** Ultralytics also needs a **MobileCLIP** TorchScript bundle (`mobileclip2_b.ts`) on first `set_classes`. It is normally auto-downloaded; if that fails, copy it into `weights/` (see `weights/README.md`).
- **Weights:** default `yoloe-26s-seg.pt` (override with `weights` or `OPENTRONS_YOLOE_WEIGHTS`).
- **Fallback:** if CLIP/MobileCLIP is missing, `vision_check` can fall back to `yolo11n.pt` + COCO mapping (marked in JSON; not labware-tuned).
- **CHECKDECK:** default YOLOE prompts are Flex-oriented (yellow/teal tip racks, clear/black plates, thermocycler/heater-shaker wording, trash); each prompt maps to a canonical label (`tiprack`, `plate`, `reservoir`, `module`, `trash_bin`). Empty slots are **grid-derived** (no detection center in that cell). Slot mapping uses **optional homography** (`deck_corners_norm` on the tool, or `optional_deck_corners_norm` in `labels/<stem>.labels.json`) else a **uniform image grid** — see `slot_mapping` in JSON output.
- **CHECKTIPS:** `mode: tiprack` is reserved (conservative stub) until rack-local well analysis is implemented.
- **Quick prompt tuning:** `uv run python scripts/yoloe_deck_preview.py <jpeg-or-0-for-webcam>` opens an Ultralytics window (or `--no-show --out file.jpg`). Override prompts via `--prompts-json` (see `scripts/yoloe_prompt_preset.example.json`).
- **MVP vision batch:** `bash scripts/batch_vision_check_mvp.sh` (or `OPENTRONS_VISION_BATCH_OUT=... OPENTRONS_VISION_CONF=0.2 uv run python scripts/batch_vision_deck_mvp.py`) runs `vision_check` on `mvp-annotation-batch` with sidecar labels; optional `OPENTRONS_YOLOE_PROMPTS_JSON` for A/B prompts.
- **MVP labeling batch:** `uv run python scripts/fetch_robot_camera_samples.py --robot HOST:31950 --limit 12` downloads recent `dataFiles` camera JPEGs into `artifacts/camera-captures/mvp-annotation-batch/` with a `manifest.json` (different runs → varied gantry/framing).
- **Slot label templates:** `uv run python scripts/generate_slot_label_templates.py` writes empty `labels/*.labels.json` (12 slots per image); see `artifacts/camera-captures/mvp-annotation-batch/labels/README.md`.
- **Kimi K2.5 deck photo (SiliconFlow):** set `SILICONFLOW_API_KEY`, then `node scripts/vlm_kimi_deck_one.mjs artifacts/camera-captures/device-latest-from-datafiles.jpeg` (or any local JPEG path).

Practical note from the current Flex:

- `GET /camera` works (HTTP needs `Opentrons-Version`, same as MCP). Quick check: `uv run python scripts/probe_robot_camera_http.py --robot HOST:31950`
- `/camera/capturePreviewImage` and `POST /camera/cameraSettings` may return `404` — **no remote zoom/pan/resolution** from HTTP on this build; variety in images comes from **different protocol captures** (`dataFiles`) or physical deck changes.
- `captureImage` through command queue can produce files, but maintenance-context capture may still fail to expose a downloadable `fileId`
- historical real robot images are still retrievable through `dataFiles`, so `download_data_file` + `vision_check` / `analyze_image_with_kimi` is a usable real-image workflow

## Protocol Library Knowledge Base

The `opentrons-protocol-library` skill uses the bundled `reference-code/Protocols-develop/` snapshot by default and still supports external overrides through `--library` or `OPENTRONS_PROTOCOL_LIBRARY_PATH`.

When configured, the skill can reference:

- validated example protocols with README documentation
- protocol source files for reusable code snippets
- `fields.json` parameter schemas
- `Cookbook.md` when the selected snapshot includes it

Example queries:

- "Is there a protocol for magnetic bead DNA cleanup?"
- "Show me how to implement liquid level tracking"
- "Find me a protocol that does serial dilution"
- "What's the pattern for CSV-based plate layout?"
- "Show me the source and runtime metadata for protocol 00222e"
- "Pull snippets related to plasma or serial dilution from protocol 00222e"

## Optional Source Mapping

If you intentionally point the verification tools at an external Opentrons source checkout, these are the most useful reference locations:

- protocol analysis entry point: `opentrons/api/src/opentrons/cli/analyze.py`
- protocol simulation entry point: `opentrons/api/src/opentrons/simulate.py`
- Python protocol camera method: `opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- HTTP client endpoint wrappers: `opentrons/api-client/src/`

## Testing

The Python helper modules are covered with lightweight unit tests that do not require a robot:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

The MCP server uses Node's built-in test runner for simulation parsing, HTTP URL normalization, live-state normalization, decision helpers, execution helpers, restart/audit-log behavior, and vision helpers. Run:

```bash
cd mcp-servers/opentrons-mcp
npm test
```

**What the MCP tests prove** (mapped to acceptance): see `../Developdocs/design/phase-2-3-acceptance.md` — in short, `test/decision.test.js` covers `DESTINATION_OCCUPIED`, safe-home, and hard stops; `test/run-protocol.test.js` and `test/experiment-history.test.js` cover the simulation gate; `test/preflight-run-setup.test.js` covers `preflight_run_setup` and declared-deck helpers; `test/experiment-history.test.js`, `test/restart-reconcile.test.js`, and `test/restart-review.test.js` cover log query, restart guidance, and restart-vs-log truth boundaries; `test/probe-wells.test.js` covers experimental probing only.

The repository also includes mocked HTTP tests for `run_protocol`, `execute_protocol_recovery`, and `recover_tip_pickup`, plus safe real-Flex validation protocols at `mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py` and `mcp-servers/opentrons-mcp/examples/flex_tip_recovery_validation.py`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on developing and validating new skills.

## License

MIT

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Adding Skills Support](https://agentskills.io/docs/client-implementation/adding-skills-support)
- [Example Skills](https://github.com/anthropics/skills)
- [Opentrons Protocol API Documentation](https://docs.opentrons.com/)
Repository: https://github.com/SmartisanNaive/Opentrons-Lab-Agent
