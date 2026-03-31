---
name: opentrons-simulation-repair
description: Use when iteratively repairing an Opentrons Python protocol by running local simulation, parsing logs, editing, and retrying.
---

# Simulation Repair

## Loop (up to 5 rounds)

1. If runtime readiness unknown: `doctor_local_runtime`.
2. `simulate_protocol`.
3. If fails: `parse_simulation_output`.
4. Fix only the highest-priority issue.
5. Re-run `simulate_protocol`.

**Stop early if:**
- `RUNTIME_UNAVAILABLE`
- `UNKNOWN_NEEDS_HUMAN`
- Two consecutive rounds do not materially change the failure

## Editing Rules

- Smallest useful edit. Preserve user intent.
- Do not rewrite the full protocol if a local fix is enough.
- Do not claim validated unless simulation actually passed.
- Do not send to robot while simulation is failing.

## Repair Lookup

| Error Class | Action |
|-------------|--------|
| `MISSING_TRASH_OR_SETUP` | Add explicit trash: `protocol.load_trash_bin("A3")` |
| `SYNTAX_OR_IMPORT` | Fix first traceback line first |
| `API_MISUSE` | Correct method names, arguments, or `apiLevel` |
| `LABWARE_OR_MODULE_COMPAT` | Align `robotType`, labware, pipette, tiprack platform |
| `VOLUME_OR_RANGE_VIOLATION` | Keep volumes inside pipette limits |

After each round, report: what changed, why, pass/fail.
