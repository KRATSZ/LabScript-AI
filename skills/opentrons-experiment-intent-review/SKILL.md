---
name: opentrons-experiment-intent-review
description: Plate mapping, tip strategy, deck alignment — validate experiment intent before coding or live runs.
type: prompt-only
mcp_tools: []
---

# Experiment Intent Review

Use when the task involves **what should happen on the deck** (patterns, mappings,
which wells, how many tips, source vs target).

Trigger: drawing, stamping, arbitrary well subsets, "does not look right",
wasteful tip usage, ambiguous deck orientation or slot assignments.

## Review Checklist

1. **Restate intent** in one paragraph (volumes, liquids, success criteria).
2. **Deck snapshot** — slots, load names, pipette mounts; flag anything unstated.
3. **Plate mapping** — 8x12 indexing, orientation vs human "up"; produce
   ASCII or table preview of target wells.
4. **Protocol alignment** — does well list match preview? Extra/missing wells?
5. **Tip and liquid strategy**
   - Same sterile liquid to many wells: one tip + repeated aspirate/dispense
     is acceptable; ask if biosafety requires one tip per well.
   - Minimize motion: batch paths, avoid unnecessary pick/drop.
6. **Risks** — overflow, wrong reservoir well, wrong tip rack density,
   Flex vs OT-2 naming (requirements, trash, pipette API).

## Required Output

Produce these sections for the downstream author:

1. `intent_summary` — bullet list of non-negotiables.
2. `plate_mask` or `target_wells` — explicit list or grid.
3. `tip_policy` — e.g. `single_tip_reuse_same_buffer` vs `one_tip_per_destination`.
4. `open_questions` — numbered; block live run until answered if safety-critical.
5. `recommendation` — `go` | `revise_mapping` | `revise_protocol` | `stop_for_human`.

## Handoff

- Intent confirmed -> `opentrons-protocol-author`
- Only import/simulate errors -> `opentrons-simulation-repair` or `opentrons-protocol-verify`
