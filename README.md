# Opentrons-Lab-Agent

`Opentrons-Lab-Agent` is a Claude Code plugin-style repository that packages Opentrons-focused Agent Skills and a practical MCP server for four jobs:

- writing and revising Python protocols
- checking whether a local Opentrons runtime is able to analyze or simulate a protocol
- iteratively repairing protocols through a simulation-first loop
- driving an OT-2 or Flex robot over the LAN HTTP API, including camera-related actions

The layout follows Anthropic's public skills conventions: each skill lives in its own folder with a `SKILL.md`, optional `scripts/`, `references/`, and `assets/`, and the repository also includes `.claude-plugin/plugin.json` so the repo can be treated as a Claude Code plugin root.

## Python Environment

This project assumes Python is managed with `uv`.

- create the local virtual environment with `uv venv .venv`
- run commands with `uv run ...`
- avoid mixing in `pip install` or a system Python unless you are intentionally debugging environment issues

If you want the project-local interpreter explicitly, activate `.venv` created by `uv`, but the default examples below assume `uv run`.

The local MCP server also auto-detects `./.venv/bin/python` when present, so once `opentrons` is installed into the project environment, `doctor_local_runtime` and `simulate_protocol` can usually run without an extra Python path argument.

## Included Skills

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

## Included MCP Server

- `mcp-servers/opentrons-mcp`
  - A compact MCP server for practical Claude Code orchestration.
  - Includes live robot tools such as `robot_status`, `module_status`, `get_slot_occupation`, `list_tip_candidates`, `suggest_next_tip_well`, `is_home_safe`, `reconcile_state`, `parse_error`, `suggest_recovery_action`, `create_run_context`, `load_pipette`, `load_labware`, `load_module`, `control_temperature_module`, `control_heater_shaker`, `control_thermocycler`, `move_labware`, `cleanup_motion`, `camera_status`, `capture_run_image`, `list_data_files`, `download_data_file`, `analyze_image_with_kimi`, `run_history`, `upload_protocol`, `run_protocol`, `recover_tip_pickup`, `create_run`, and `control_run`.
  - Adds local tools `doctor_local_runtime`, `simulate_protocol`, and `parse_simulation_output` for simulation-first repair.

This repository's `mcp-servers/opentrons-mcp` is the canonical `opentrons-lab-mcp` implementation. Community MCP servers in the broader workspace are reference material only; they are useful for HTTP surface comparison, but this repo's tool names, recovery rules, and response envelope are defined here.

## Repository Layout

```text
Opentrons-Lab-Agent/
├── .claude-plugin/plugin.json
├── mcp-servers/
│   └── opentrons-mcp/
├── skills/
│   ├── opentrons-protocol-author/
│   ├── opentrons-protocol-verify/
│   ├── opentrons-robot-lan/
│   └── opentrons-simulation-repair/
├── src/opentrons_lab_agent/
└── tests/
```

## Using It In Claude Code

This repository is already shaped like a Claude Code plugin:

- plugin metadata lives at `.claude-plugin/plugin.json`
- skills live under `skills/`
- helper code lives under `src/`

If you distribute skills through a Claude Code plugin or marketplace workflow, this repo is ready for that structure. If you use direct skills folders, you can also copy the individual skill directories under `skills/` into the Claude Code skills location used in your environment.

## Local Opentrons Runtime Assumptions

The verification skill is intentionally defensive.

It assumes the Opentrons source tree may be vendored into the same workspace, but not necessarily installed as a working Python package. In the current workspace snapshot, the available `opentrons/` tree contains `api/`, `api-client/`, and `shared-data/`, but it does not include a fully usable local development environment. Because of that:

- the verification wrapper injects a minimal `opentrons._version` module at runtime
- the wrapper checks whether Python can import the modules needed for `opentrons.cli` and `opentrons.simulate`
- if third-party dependencies or sibling packages are missing, it exits with a clear diagnostic instead of pretending validation succeeded

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

### Local simulation-first repair workflow

Recommended Claude Code tool order:

1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. `simulate_protocol` again

### Phase 1 live-state workflow

Recommended Claude Code tool order before and during live execution:

1. `robot_status`
2. `module_status`
3. `reconcile_state`
4. `get_slot_occupation` / `list_tip_candidates` / `is_home_safe`
5. `create_run_context`
6. `load_pipette` / `load_labware` / `move_labware`
7. `cleanup_motion`
8. `upload_protocol`
9. `create_run`
10. `control_run`
11. `run_history`
12. `suggest_recovery_action`
13. `parse_error` when a live command or run fails

For the common "upload + create run + play + poll" path, prefer the single `run_protocol` tool. It now enforces a local `doctor_local_runtime -> simulate_protocol -> parse_simulation_output` gate before any real upload or run start, so a simulation failure blocks physical execution immediately.

Recent real-Flex validation now also covers a physical gripper move:

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
- `recover_tip_pickup` on that same run, which executed `pickUpTip(B1, intent="fixit") -> resume-from-recovery` and let the original protocol finish with `status = succeeded`
- live read-only Phase 2 validation for `suggest_recovery_action(error_category="DESTINATION_OCCUPIED", target_slot="C1")`, which returned concrete alternative slots from the real deck layout and still marked the branch as human-reviewed because the candidates were only low-confidence `unknown` slots
- negative Phase 3 gate validation with a deliberately broken local protocol, where `run_protocol` stopped at simulation parsing and never started a real robot run

All MCP tools now return a common response envelope with:

- `success`
- `data`
- `error`
- `hardware_snapshot`
- `state_revision`
- `run_id`
- `session_id`
- `timestamp`

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

The repository already contains two useful layers for vision-related work:

- Robot-side camera control in `src/opentrons_lab_agent/robot_api.py` for `GET /camera`, `POST /camera`, `POST /camera/cameraSettings`, and `POST /camera/capturePreviewImage`.
- MCP-side camera tools in `mcp-servers/opentrons-mcp` for:
  - `camera_status`
  - `configure_camera`
  - `capture_preview_image`
  - `capture_run_image`
  - `list_data_files`
  - `download_data_file`
  - `analyze_image_with_kimi`

Design rule:

- keep image acquisition inside the robot MCP
- keep image interpretation in a separate analyzer step or future MCP
- pass around a saved `image_path` artifact instead of stuffing binary blobs into tool output

That split makes it easy to start with human inspection now, then later plug in a multimodal model or an external CV service without coupling perception logic to robot control.

Practical note from the current Flex:

- `GET /camera` works
- `/camera/capturePreviewImage` currently returns `404`
- `captureImage` through command queue succeeds, but maintenance-context capture may still fail to expose a downloadable `fileId`
- historical real robot images are still retrievable through `dataFiles`, so `download_data_file` + `analyze_image_with_kimi` is already a usable real-image workflow

## Source Mapping

These skills were written against the Opentrons code that is present in the same workspace:

- protocol analysis entry point: `opentrons/api/src/opentrons/cli/analyze.py`
- protocol simulation entry point: `opentrons/api/src/opentrons/simulate.py`
- Python protocol camera method: `opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- HTTP client endpoint wrappers: `opentrons/api-client/src/`

## Testing

The Python helper modules are covered with lightweight unit tests that do not require a robot:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

The MCP server has lightweight Node tests for simulation parsing, HTTP URL normalization, live-state normalization, and decision helpers:

```bash
cd mcp-servers/opentrons-mcp
npm test
```

The repository also now includes mocked unit tests for `run_protocol` and `recover_tip_pickup`, plus safe real-Flex validation protocols at `mcp-servers/opentrons-mcp/examples/flex_noop_protocol.py` and `mcp-servers/opentrons-mcp/examples/flex_tip_recovery_validation.py`.

Repository: https://github.com/SmartisanNaive/Opentrons-Lab-Agent