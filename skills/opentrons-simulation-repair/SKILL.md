---
name: opentrons-simulation-repair
description: Use when the user wants Claude Code to iteratively repair an Opentrons Python protocol by running local simulation, parsing the logs, editing the script, and retrying until it passes or a non-editable blocker is reached.
---

# Opentrons Simulation Repair

Use this skill when the protocol should be fixed through a simulation-first loop instead of guessing.

## Goal

Make the protocol pass `simulate_protocol` before any real execution.

## Required Loop

1. If runtime readiness is unknown, call `doctor_local_runtime`.
2. Call `simulate_protocol`.
3. If simulation fails, call `parse_simulation_output`.
4. Fix only the highest-priority issue first.
5. Re-run `simulate_protocol`.
6. Repeat up to 5 rounds.

Stop the loop early if:

- the issue is `RUNTIME_UNAVAILABLE`
- the issue is `UNKNOWN_NEEDS_HUMAN`
- two rounds in a row do not materially change the failure

## Editing Rules

- Make the smallest useful edit.
- Preserve the user's experiment intent whenever possible.
- Do not rewrite the full protocol if a local fix is enough.
- Do not claim the protocol is validated unless simulation actually passed.
- Do not send the protocol to the robot while simulation is still failing.

## Common Repair Actions

- `MISSING_TRASH_OR_SETUP`
  - add explicit trash setup such as `protocol.load_trash_bin("A3")`
- `SYNTAX_OR_IMPORT`
  - fix the first traceback line first
- `API_MISUSE`
  - correct method names, arguments, or `apiLevel`
- `LABWARE_OR_MODULE_COMPAT`
  - align `robotType`, labware names, pipette, and tiprack platform
- `VOLUME_OR_RANGE_VIOLATION`
  - keep aspirate/dispense volumes inside pipette limits

## Reporting Back

After each repair round, briefly report:

- what changed
- why it changed
- whether the latest simulation passed or failed
