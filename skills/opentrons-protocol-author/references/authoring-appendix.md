# Protocol authoring appendix (read on demand)

Load this file when you are **finalizing** a protocol or need **OT-2 pipette tables**, **dead volume**, **tip math**, **`design-notes.json`**, or the **full self-review checklist**. Do not treat it as required context for the first draft.

## OT-2 pipettes

| Pipette model | Min reliable | Max volume | Use for |
|--------------|-------------|-----------|---------|
| `p20_single_gen2` / `p20_multi_gen2` | 2 µL | 20 µL | Small volumes |
| `p300_single_gen2` / `p300_multi_gen2` | 30 µL | 300 µL | Medium volumes |
| `p1000_single_gen2` | 100 µL | 1000 µL | Large volumes |

## Dead volume awareness

Source labware has unrecoverable dead volume — liquid below a certain height cannot be aspirated. Account for this when calculating how much source volume to load:

| Labware type | Typical dead volume |
|-------------|-------------------|
| 96-well plate | 5-10 µL (V-bottom), 15-20 µL (flat) |
| Reservoir well (NEST 12-well 15 mL) | **~1.9 mL** |
| Reservoir well (NEST 1-well 195 mL) | **~19 mL** |
| 15 mL conical tube (Falcon) | ~200 µL |
| 50 mL conical tube (Falcon) | ~500 µL |
| 1.5 mL microcentrifuge tube | ~10 µL |

**Note:** Reservoir dead volumes are much larger than plate wells — a 15 mL reservoir well has ~1.9 mL dead volume, not 20 µL. Always use the correct labware-specific value.

When calculating source volume: `load_volume = sum(transfers) + dead_volume`.

## Labware inspection and substitution

When a load name is unfamiliar or you need a safe substitute:

1. Call MCP `validate_labware_name` first to verify the exact load name or get close matches.
2. Call MCP `inspect_labware_definition` on each candidate if geometry or dead volume matters.
3. Prefer the same labware category, same well count, and the closest capacity class.
4. Do not invent substitutes for tip racks, reservoirs, or adapter-dependent labware when the geometry changes materially.
5. For cell culture and reservoir workflows, compare `representative_well.depth_mm`, `total_liquid_volume_ul`, and `dead_volume_hint` before choosing a fallback.

## Tip count estimation

Before finalizing any protocol, estimate total tip usage and verify the tip rack has enough tips:

```
tips_needed = (number_of_wells × number_of_reagent_steps) + (mixing steps) + (wash steps)
tips_available = 96 × number_of_tip_racks
assert tips_needed <= tips_available
```

If tips are insufficient:

1. Add a second tip rack on a different slot.
2. Consider whether partial tip reuse is safe for non-critical steps.
3. Document the tip count calculation in `design-notes.json`.

## Self-review checklist

Before outputting your final protocol, verify each item below. Fix any issues found:

1. **Volume accumulation**: Does sequential addition without removal cause volume to exceed the well capacity? Add aspiration/removal steps between reagent additions.
2. **Reagent compatibility**: Does the protocol neutralize or remove reagents before the next step? (e.g., trypsin must be neutralized before adding fresh medium)
3. **Temperature sensitivity**: Do any reagents require temperature control (37°C for cell culture, 4°C for enzyme reactions)? Add temperature module if needed.
4. **Tip contamination**: Is a new tip used between different reagents and between wells containing different biological material?
5. **Empty well assumption**: If the protocol adds liquid to wells, does it first remove any pre-existing liquid?
6. **Pipette accuracy**: Are transfers within 10-90% of the pipette's max volume? Avoid operating at the absolute edge of the range.
7. **Tip count**: Does the protocol have enough tips for all operations? Calculate explicitly and document in design-notes.
8. **Dead volume**: Have you accounted for dead volume in source wells/tubes? Total loaded volume = transfer volume + dead volume.
9. **Liquid class**: On Flex, did you use verified liquid classes (`water` / `ethanol_80` / `glycerol_50`) or document why not? On OT-2, are `rate=` / flow_rate overrides justified per liquid?
10. **Trash bin**: Flex protocols MUST call `protocol.load_trash_bin("A3")`. OT-2 protocols do not need this.
11. **RTP choices format**: Any `add_str(..., choices=...)` must use `{"display_name": ..., "value": ...}` dicts, NOT plain strings.
12. **transfer_with_liquid_class 1:many**: When transferring from one source to many destinations with a liquid class, you MUST loop per destination. `transfer_with_liquid_class` does NOT support `distribute` mode.

## design-notes.json schema

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
- `pipette_choice` MUST be an object with `name` and `reason` (string, 5+ chars) fields. NOT a plain string. The `reason` field must explain WHY this pipette was chosen (e.g., "P50 for ≤50 µL accuracy" or "P1000 covers 1 mL transfers with volume splitting").
- `tip_strategy` MUST be an object with `policy` and `reason` (string, 5+ chars) fields. NOT a plain string. The `reason` field must explain the contamination/tip budget tradeoff (e.g., "new_tip=always prevents cross-contamination; 96 tips sufficient for 8 samples × 3 reagents").
- `key_decisions` MUST be a non-empty array of objects with `decision` and `rationale`.
- For workflow/safety questions where no protocol is generated, still fill all fields. Use "N/A" only for `robot` if truly inapplicable; always provide meaningful `deck_layout.description`, `pipette_choice.reason`, and `tip_strategy.reason` even when describing why no action was taken.

**IMPORTANT:** Structure checker scores `pipette_choice.reason` and `tip_strategy.reason` separately. Missing or empty reasons lose points even when the name/policy is correct.
