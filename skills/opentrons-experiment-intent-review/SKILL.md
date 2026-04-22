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

## Interaction Rule

This skill should reduce friction, not create a questionnaire.

- Ask at most one blocking clarification round.
- If only one preference is missing (for example tip reuse policy), explain the
  trade-off and give a recommendation.
- If the protocol can still be drafted safely, hand off with a recommended
  default instead of waiting forever for perfect inputs.

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
   - If user has not chosen a tip policy yet, give one recommended default plus
     one sentence on when to choose the stricter option.
6. **Risks** — overflow, wrong reservoir well, wrong tip rack density,
   Flex vs OT-2 naming (requirements, trash, pipette API).

## Supporting references (read when needed)

Bundled checklists (extend with lab-specific SOPs as separate files if needed):

- [references/deck-constraints.md](references/deck-constraints.md) — slots, labware, pipettes, modules, orientation.
- [references/biology-constraints.md](references/biology-constraints.md) — sample/reagent semantics, contamination policy, success criteria.

## Required Output

Produce these sections for the downstream author (seven blocks):

1. `intent_summary` — bullet list of non-negotiables.
2. `biology_constraints` — short bullets; use `unknown` + one question if unspecified. See `references/biology-constraints.md` only when you need the checklist.
3. `deck_constraints` — robot type, intended slots/load names, pipettes, modules, orientation vs indexing; must match what will be simulated and later `reconcile_state`. See `references/deck-constraints.md` only when needed.
4. `plate_mask` or `target_wells` — explicit list or grid.
5. `tip_policy` — e.g. `single_tip_reuse_same_buffer` vs `one_tip_per_destination`.
6. `open_questions` — numbered; block live run until answered if safety-critical.
7. `recommendation` — `go` | `revise_mapping` | `revise_protocol` | `stop_for_human`.

**Additionally, always produce `design-notes.json`** following the schema in `opentrons-protocol-author/references/authoring-appendix.md`. For intent-review tasks this is the primary deliverable. Required fields:

- `deck_layout` — object with `description` (10+ chars summarizing the layout) and `slots_used`.
- `pipette_choice` — object with `name` and `reason` (explain why this pipette fits the volume range and well access pattern).
- `tip_strategy` — object with `policy` and `reason` (explain the trade-off: why fresh vs reuse, tip budget math).
- `key_decisions` — array capturing assumptions and design choices.

**Workflow-specific additions** that the structure checker evaluates:
- Mapping preview: include an ASCII or table preview of target wells in `deck_layout.description`.
- Tip tradeoff: explain in `tip_strategy.reason` why this policy is preferred over alternatives.

Keep `open_questions` short. In the common case it should contain zero or one
item, not a long survey.

## Optional

- `reference_sources` — **only if** you opened a bundled file under `references/` to shape `biology_constraints` or `deck_constraints`; list those paths (one line). Omit in the common case (checklist-only review).

## Handoff

- Intent confirmed -> `opentrons-protocol-author`
- Only import/simulate errors -> `opentrons-simulation-repair` or `opentrons-protocol-verify`
