---
name: opentrons-simulation-repair
description: Iteratively repair an Opentrons Python protocol — simulate, parse errors, edit, retry.
type: prompt-only
mcp_tools:
  - doctor_local_runtime
  - simulate_protocol
  - parse_simulation_output
---

# Simulation Repair

## Repair loop (no fixed round cap)

Repeat until simulation passes or you stop early:

1. If runtime readiness unknown: `doctor_local_runtime`.
2. `simulate_protocol`.
3. If fails: `parse_simulation_output`.
4. Fix only the highest-priority issue.
5. Re-run `simulate_protocol`.

**Stop early if:**
- `RUNTIME_UNAVAILABLE`
- `UNKNOWN_NEEDS_HUMAN`
- **Two consecutive rounds do not materially change the failure** (same root error / no meaningful code delta)

There is **no** target maximum number of rounds; avoid pointless churn by honoring the stop conditions above.

## Editing Rules

- Smallest useful edit. Preserve user intent.
- Do not rewrite the full protocol if a local fix is enough.
- Do not claim validated unless simulation actually passed.
- Do not send to robot while simulation is failing.
- For long sessions, a one-line note per round (or version control) helps avoid losing track of edits; still report each round’s delta in the conversation.

## Repair Lookup

| Error Class | Action |
|-------------|--------|
| `MISSING_TRASH_OR_SETUP` | Add explicit trash: `protocol.load_trash_bin("A3")` |
| `SYNTAX_OR_IMPORT` | Fix first traceback line first |
| `API_MISUSE` | Correct method names, arguments, or `apiLevel` |
| `LABWARE_OR_MODULE_COMPAT` | Align `robotType`, labware, pipette, tiprack platform |
| `VOLUME_OR_RANGE_VIOLATION` | Keep volumes inside pipette limits |

After each round, report: what changed, why, pass/fail.
