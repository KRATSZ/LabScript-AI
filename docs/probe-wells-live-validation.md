# `probe_wells` live validation runbook

`probe_wells` is **experimental**. Default behavior is **local simulation** only. Real robot motion requires explicit operator steps below.

## Preconditions (all required)

1. **Simulate first** — same `pipette_name`, `mount`, `tiprack_load_name`, `tiprack_slot`, `labware_load_name`, `labware_slot`, `wells`, and `mode` as the live attempt. Confirm simulate output is acceptable.
2. **Physical deck** matches every slot and mount in the request (tip rack seated, labware seated, pipette installed on the declared mount).
3. **Human operator** present with clear abort path (door, estop, stop software).
4. **MCP environment** — set `OPENTRONS_ENABLE_PROBE_WELLS=1` on the **MCP server process**; keep it unset everywhere else.
5. **Written or verbal sign-off** before calling with `execute_on_robot: true`.

## Minimal first live test (recommended scope)

- One pipette, one tip rack, one labware, **one well**, `mode: detect_presence` (or the least invasive mode you need).
- Record: `session_id`, wall time, robot IP, full tool arguments, and any returned probe summary.

## Execution checklist

1. Run **`restart_review`** if you are resuming after any restart or long pause (same `session_id`, optional `robot_ip`).
2. If **`reconcile_first`**, run **`reconcile_state`** before probing.
3. Call **`probe_wells`** with **`execute_on_robot: false`** once more to confirm simulate still passes.
4. Call **`probe_wells`** with **`execute_on_robot: true`** only after the sign-off in preconditions.
5. After the call, pull **`experiment_history`** filtered by `session_id` and/or `tool_name: probe_wells` for an audit trail.

## Stop immediately if

- Unexpected motion, sounds, or crashes.
- Tip pickup or liquid-handling errors you did not anticipate.
- **`is_home_safe`** / home-safety preview indicates blockers while you are planning further motion.
- Results are nonsensical vs. visual inspection — treat as **unknown**, do not auto-expand well list.

## Evidence to capture for a validation report

- MCP request payload (redact secrets).
- `experiment_history` entries for `probe_preview` / `probe_execution`.
- Operator notes: expected vs. observed for the single well.
- Whether `OPENTRONS_ENABLE_PROBE_WELLS` was enabled only on the MCP host.

## See also

- **Canonical** MCP handler and gating: `Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js` (`probe_wells`).
- **Canonical** tests: `Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/test/probe-wells.test.js`.
- Legacy community MCP notes only: `reference/opentrons-mcp/` (not an implementation tree).
