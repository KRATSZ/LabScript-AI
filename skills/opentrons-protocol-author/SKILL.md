---
name: opentrons-protocol-author
description: Use when writing, revising, or reviewing Opentrons Python protocols for OT-2 or Flex robots, including deck setup, labware loading, pipette usage, runtime parameters, and camera capture with ProtocolContext.capture_image().
license: Apache-2.0
compatibility: Requires Python 3.8+, uv for package management, and access to Opentrons protocol documentation.
---

# Protocol Author

1. Identify target robot: `OT-2` or `Flex`. **Default Flex.**
2. For spatial patterns, arbitrary well subsets, or unclear plate mapping:
   run `opentrons-experiment-intent-review` first. Lock `target_wells` / tip policy.
3. Read `references/python-protocol-patterns.md` and `references/pattern-library.md`.
4. Start from `assets/flex_protocol_template.py` (Flex) or `assets/protocol_template.py` (OT-2).
5. Keep protocol explicit: labware, instruments, mounts, slots, runtime parameters.
6. If user asks about validation -> `opentrons-protocol-verify`.
7. If simulation fails and goal is iterative repair -> `opentrons-simulation-repair`.

## Rules

- Use `requirements = {"robotType": "...", "apiLevel": "..."}` for modern protocols.
- `apiLevel` must appear **only** in `requirements`, never inside `metadata`.
- Call out custom labware dependencies explicitly.
- **Flex trash bin is NOT a Labware.** `load_trash_bin()` returns a `TrashBin` object,
  not a labware with wells. You CANNOT subscript it (`trash_bin["A1"]` is invalid).
  To dispose of liquid waste: `pipette.dispense(vol, location=trash_bin)` or
  `pipette.blow_out(location=trash_bin)`. To drop tips: `pipette.drop_tip(trash_bin)`.
  You CANNOT `aspirate()` from a TrashBin.
- Do not claim validated unless verify tooling ran or user provided validated result.
- **Questions describe simplified workflows.** Real protocols have intermediate steps
  (aspiration between reagent additions, neutralization, temperature control) that
  question descriptions omit. Add biologically necessary steps even when the
  question doesn't mention them.
- **Implement known limitations.** If your draft protocol has steps you know are
  biologically or mechanically incomplete, go back and implement them before
  finalizing. Document in `known_limitations` only steps that truly cannot be
  automated (e.g., visual cell detachment inspection).

## Self-Review Checklist

Before outputting your final protocol, verify each item below. Fix any issues found:

1. **Volume accumulation**: Does sequential addition without removal cause volume to exceed the well capacity? Add aspiration/removal steps between reagent additions.
2. **Reagent compatibility**: Does the protocol neutralize or remove reagents before the next step? (e.g., trypsin must be neutralized before adding fresh medium)
3. **Temperature sensitivity**: Do any reagents require temperature control (37°C for cell culture, 4°C for enzyme reactions)? Add temperature module if needed.
4. **Tip contamination**: Is a new tip used between different reagents and between wells containing different biological material?
5. **Empty well assumption**: If the protocol adds liquid to wells, does it first remove any pre-existing liquid?
6. **Pipette accuracy**: Are transfers within 10-90% of the pipette's max volume? Avoid operating at the absolute edge of the range.

## design-notes.json Schema

When producing `design-notes.json`, use this exact schema. Field types matter:

```json
{
  "question_id": "Q1",
  "experiment_type": "cell_culture_passaging",
  "robot": "Flex",
  "deck_layout": {
    "description": "Description of the deck setup (10+ chars)",
    "slots_used": ["A3", "B2", "C2", "C3", "D1"]
  },
  "pipette_choice": {
    "name": "flex_1channel_1000",
    "reason": "1000 uL max volume covers 1 mL transfers; single-channel for 6-well plate individual well access"
  },
  "tip_strategy": {
    "policy": "fresh_tip_per_well_per_reagent",
    "reason": "Prevent cross-contamination between wells and between reagent steps; 96-tip rack has ample capacity"
  },
  "key_decisions": [
    {"decision": "...", "rationale": "..."}
  ],
  "known_limitations": ["..."]
}
```

**Critical rules for design-notes.json:**
- `deck_layout` MUST be an object with `description` (string, 10+ chars) and `slots_used` (array of slot strings).
- `pipette_choice` MUST be an object with `name` and `reason` (string, 5+ chars) fields. NOT a plain string.
- `tip_strategy` MUST be an object with `policy` and `reason` (string, 5+ chars) fields. NOT a plain string.
- `key_decisions` MUST be a non-empty array of objects with `decision` and `rationale`.
- For workflow/safety questions where no protocol is generated, still fill all fields. Use "N/A" only for `robot` if truly inapplicable; always provide meaningful `deck_layout.description`, `pipette_choice.reason`, and `tip_strategy.reason` even when describing why no action was taken.

## References

- Protocol patterns: `references/python-protocol-patterns.md`
- Pattern index: `references/pattern-library.md`
- Flex template: `assets/flex_protocol_template.py`
- OT-2 template: `assets/protocol_template.py`
