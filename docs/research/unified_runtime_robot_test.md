# Unified Runtime Robot Test

Date: 2026-05-22

Artifact directory: `runs/unified_runtime_robot_test/20260522_181106/`

## Correction

This artifact should not be described as a full `LabscriptAgentLoop.run()` execution. The recovery was executed through the unified tool registry, unified gatekeeper, and MCP recovery adapter, but the tool-call sequence was scripted by the operator-side harness. It is valid evidence for the gated tool path and MCP live recovery branch, not for the full unified agent loop autonomously driving the recovery.

## Conclusion

The unified tools/gatekeeper path completed one controlled live missing-tip recovery case on the Flex robot.

- Run ID: `f444f90b-dce0-4312-be87-cfb1b24d060e`
- Before recovery: `awaiting-recovery`, failed `pickUpTip(A1)`, `TIP_PHYSICALLY_MISSING / No Tip Detected`
- Recovery branch: `retry_pick_up_tip_with_next_candidate`
- Fixit command: `pickUpTip(B1)` with `intent=fixit`
- After recovery: `resume-from-recovery`, final run status `succeeded`

## Sensing Coverage

HTTP was available and useful:

- `/health` identified `Silabrobot001`, `FLXA2020240921002`, `OT-3 Standard`, API `9.0.0`.
- `/runs`, `/runs/{run_id}`, and `/runs/{run_id}/commands` captured before/after run state and command changes.
- `/modules` captured current module status.

MCP was available and useful:

- `parse_error` classified the error as `TIP_PHYSICALLY_MISSING`, `auto_executable: true`.
- `suggest_recovery_action` selected `retry_pick_up_tip_with_next_candidate`, C2/B1.
- `execute_protocol_recovery` executed the fixit branch and resumed the run.

Vision was partially available:

- `camera_status` succeeded.
- `capture_preview_image` failed with `Cannot capture preview photo, run is active.`
- Because no preview image was captured, `vision_check` was not run.
- This is recorded as observation-only evidence, not deck truth.

Pressure/liquid sensing was not used:

- Official Opentrons docs describe Flex pressure-based liquid detection and protocol methods such as `detect_liquid_presence()` and `measure_liquid_height()`.
- In this repo, `probe_wells` can generate such probe protocols, but live probing is experimental and requires extra enablement.
- There is no passive read-only pressure/liquid sensor endpoint exposed for this active missing-tip run.
- Running a probe would have added live motion outside the approved missing-tip recovery scope.

Sources:

- https://docs.opentrons.com/flex/system-description/pipettes/
- https://docs.opentrons.com/python-api/pipettes/loading/
- https://docs.opentrons.com/python-api/building-block-commands/liquids/

## Memory

The loop searched memory before recovery, appended a note after recovery, and `memory_search.json` retrieves the new note with query terms for missing-tip recovery.

## Limits

Do not report this as full autonomous live recovery. Also do not report it as proof that `LabscriptAgentLoop.run()` drove the recovery. The supported claim is narrower: one controlled Flex missing-tip live recovery case, using HTTP/MCP sensing, gated unified tools, MCP recovery execution, and memory write/read evidence.

## New Unified Agent Loop Live Case

Artifact directory: `runs/unified_agent_loop_live/20260522_182745/`

This second case corrects the limitation above. It was driven through `LabscriptAgentLoop.run()` with a real model client and the unified runtime tool registry.

- Run ID: `30b0350e-9b7a-458e-a5de-18c45d6b3854`
- Protocol: `missing_tip_b1_protocol.py`
- Before recovery: `awaiting-recovery`, failed `pickUpTip(B1)`, `tipPhysicallyMissing / 3003 / No Tip Detected`
- Unified loop trace: `labscript_agent_loop_trace_recoveryretry-c42fa4d5.jsonl`
- Trace summary: `trace_summary_recoveryretry.json`
- Tool order observed: `robot.inspect` -> `error.parse` -> `recovery.suggest` -> `memory.read_write search` -> `run.control` -> `memory.read_write append`
- Recovery branch: `retry_pick_up_tip_with_next_candidate`
- Gatekeeper decision for `run.control`: approved
- Execution backend: MCP `execute_protocol_recovery`
- After recovery: run action `resume-from-recovery`, final run status `succeeded`
- MCP `parse_error` audit: `labscript_agent_loop_trace_parsefix2-*.jsonl` confirmed `TIP_PHYSICALLY_MISSING` with `robot_ip + run_id`

Important nuance:

- The next candidate chosen by recovery was `A1`.
- `A1` was also physically missing, so the fixit `pickUpTip(A1)` failed with the same `tipPhysicallyMissing` code.
- The run still resumed and completed the protocol cleanup path.
- This proves the unified loop selected and executed the missing-tip recovery branch, but not that the next candidate tip was physically present.

Updated sensing coverage:

- HTTP state sensing succeeded before and after recovery.
- MCP recovery suggestion and execution succeeded.
- The main recovery trace's first `error.parse` call omitted `robot_ip`, so MCP returned a missing-robot-ip error; a follow-up unified-loop audit corrected this and captured the successful MCP `parse_error` classification.
- Camera status and preview capture succeeded after the run; `vision_check` executed but reported that `ultralytics` is not installed, so there is no visual detection result to treat as evidence.
- Pressure/liquid sensing remains unavailable for this case as a passive read-only signal. The repo exposes active `probe_wells` support and Opentrons documents Flex pressure/liquid APIs, but this test did not run a liquid-probing protocol.

Memory:

- The loop appended `runtime_memory/20260522T104021.935487Z-recovery-retry-pick-up-tip-with-next-candidate.md`.
- `memory_search_after.json` retrieves the new note.

Supported claim:

One controlled real Flex missing-tip recovery case was driven by `LabscriptAgentLoop.run()` using real robot state, gated `run.control`, MCP recovery execution, and memory write/read evidence.

## Normal Live Monitoring Case

Artifact directory: `runs/unified_agent_loop_live/20260522_185122_normal_monitor/`

- Run ID: `860b3683-4e9b-4078-b73c-4415702816c8`
- Protocol: `normal_monitor_protocol.py`
- Protocol behavior: comment -> 20 second delay -> comment; no pipette, no tip pickup, no liquid handling.
- Control path: MCP `run_protocol(auto_play=false)` created the run; MCP `control_run(play)` started it.
- Observation path: HTTP `RuntimePoller` only, no HTTP control.
- Poller events: `idle -> running`, normal progress, `running -> finishing`, `run_completed`.
- Final status: `succeeded`
- Commands: `home`, `comment`, `waitForDuration`, `comment`, all succeeded.
- Unified loop trace: `labscript_agent_loop_trace_normal_memory-a0532a49.jsonl`
- Unified loop tools: `robot.inspect`, then `memory.read_write append`
- Memory retrieval: `memory_search_after.json` retrieves the normal-monitor note.

Supported claim:

The runtime stack can monitor a normal no-error live Flex run through HTTP polling, record lifecycle events, and then route the real completed run through the unified agent loop for inspection and memory writing.

Limit:

This second case does not test recovery or liquid handling. It is a monitoring-only run.
