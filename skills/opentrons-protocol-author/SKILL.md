---
name: opentrons-protocol-author
description: Write or revise Opentrons Python protocols for OT-2 or Flex robots — deck setup, labware, pipette, runtime parameters, camera capture.
type: prompt-only
entry: assets/flex_protocol_template.py
mcp_tools: []
---

# Protocol Author

1. Identify target robot: `OT-2` or `Flex`. **Default Flex.**
2. For spatial patterns, arbitrary well subsets, or unclear plate mapping:
   run `opentrons-experiment-intent-review` first. Lock `target_wells` / tip policy.
3. Read `references/python-protocol-patterns.md`, `references/pattern-library.md`, and (Flex) `references/liquid-classes-flex.md`.
4. Start from **`assets/flex_protocol_template.py`** (Flex) or **`assets/protocol_template.py`** (OT-2). For common workflows, copy from **`assets/flex_template_*.py`** or **`assets/flex_liquid_classes_example.py`**. Supplementary snippets live under **`assets/archive/`** — not default starters.
5. Keep protocol explicit: labware, instruments, mounts, slots, runtime parameters.
6. If user asks about validation -> `opentrons-protocol-verify`.
7. If simulation fails and goal is iterative repair -> `opentrons-simulation-repair`.
8. If MCP tools are available, validate unfamiliar labware names before writing code, inspect labware geometry/dead volume when choosing substitutes, and estimate tip budget before finalizing a draft. This catches the most common avoidable errors early.
9. If the user only wants validation or labware inspection, return findings directly. Do not force a full protocol draft when the task is just to check or compare options.

**Finalize / report:** When outputting `design-notes.json`, calculating dead volume or tip budgets, or running the full pre-output checklist, read **`references/authoring-appendix.md`**.

## Interaction Defaults

- Do not wait for perfect inputs when a safe, runnable draft is already possible.
- Ask only for choices that change robot compatibility, deck truth, module usage,
  or safety-critical contamination assumptions.
- If only a preference is missing, choose a documented default and note it in
  `design-notes.json` (schema in appendix when you write it).
- Once a runnable draft exists, the default next step is simulation.

## Rules

- Use `requirements = {"robotType": "...", "apiLevel": "..."}` for modern protocols.
- `apiLevel` must appear **only** in `requirements`, never inside `metadata`.
- Flex apiLevel must be **2.24 or higher** in bundled templates — compatible with verified liquid classes and RTP; raise toward `opentrons.protocol_api.MAX_SUPPORTED_VERSION` when your install allows. Older 2.20-only protocols may still run on robot but new drafts should not default below **2.24**.
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
- Prefer parameterized drafts over deferring work. For example, if a tip policy
  is undecided but the rest of the protocol is known, draft the protocol with a
  recommended default and make the choice easy to revise.
- **Tip budget is a hard constraint.** Before finalizing, COUNT every `pick_up_tip` / `transfer` / `mix` call and verify total ≤ 96 × number_of_tip_racks. Running out of tips mid-protocol is a fatal simulation failure. If tip budget is tight: use `new_tip="once"` for same-reagent consecutive transfers (NOT for different reagents or different destination types), or add a second tip rack.
- **PCR / 96-well tip math example:** 96 wells × 4 reagent additions + 96 mix passes = up to 384 tips. With one 96-tip rack this is IMPOSSIBLE. You MUST either: (a) use `new_tip="once"` within the same reagent step, (b) use multi-channel pipette (96 tips covers a full column), or (c) add multiple tip racks. Always calculate before writing.

## Liquid handling (prefer official APIs)

**Flex — Opentrons-verified liquid classes (three):** `water`, `ethanol_80`, `glycerol_50`. Use `protocol.get_liquid_class(...)` and `pipette.transfer_with_liquid_class(...)` so submerge speed, flow rate by volume, air gaps, and delays come from the verified definitions — **do not hand-copy µL/s tables**. Requires apiLevel **≥ 2.24** (use your environment’s supported maximum, e.g. check `opentrons.protocol_api.MAX_SUPPORTED_VERSION`). See `references/liquid-classes-flex.md` and `assets/flex_liquid_classes_example.py`.

**IMPORTANT:** `transfer_with_liquid_class` does NOT have `distribute`/`consolidate` variants. For one-to-many transfers with a liquid class, **loop per destination well**. Passing a list dest with a single source raises `ValueError`.

**OT-2 or legacy building-block transfers:** use the `rate=` multiplier on `aspirate()` / `dispense()` (relative to that pipette’s defaults), or set `pipette.flow_rate.aspirate` / `dispense` in µL/s. See [Liquid control](https://docs.opentrons.com/python-api/building-block-commands/liquids/).

**Local static check before simulate:** `uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py preflight <protocol.py>` catches invalid Flex pipette names and flags apiLevel mismatches for RTP / liquid-class features.

## Pipette range (Flex default path)

Choose the smallest pipette that covers the required volume range. Transfers below 10% of max volume lose accuracy.

**Flex pipettes (only these are valid `load_instrument` names):**

| Pipette model | Actual min | Recommended min (≥10% max) | Max volume | Use for |
|--------------|-----------|---------------------------|-----------|---------|
| `flex_1channel_50` / `flex_8channel_50` | 1 µL | 5 µL | 50 µL | Small-volume PCR, ELISA reagents |
| `flex_1channel_1000` / `flex_8channel_1000` | 5 µL | 100 µL | 1000 µL | Large-volume transfers, cell culture |

**IMPORTANT**: `flex_1channel_200` and `flex_8channel_200` do NOT exist. If you need a mid-range volume (20-200 µL), use `flex_1channel_50` with volume splitting, or `flex_1channel_1000` with awareness that accuracy decreases below 100 µL. **Do NOT claim the P1000 "cannot" do volumes below 100 µL** — it can transfer down to 5 µL, just with reduced accuracy. If high precision is needed below 100 µL, recommend the P50 instead.

**Common operator wording trap:** If a Flex user asks for a "single-channel P300", do **not** invent a non-existent `flex_1channel_300`. State the mismatch plainly, then choose the closest real option:
- default practical choice: `flex_1channel_1000` with `opentrons_flex_96_tiprack_200ul` for roughly 20-200 µL work
- precision-first choice: `flex_1channel_50` when important transfers are mostly ≤50 µL
- in `design-notes.json`, record that Flex has no native 300 µL single-channel pipette and explain the tradeoff you chose

**Volume split rule:** If a single transfer exceeds the pipette max, split into multiple transfers. Example: 1500 µL with a 1000 µL pipette → 1000 µL + 500 µL.

**Low-volume flag:** If any transfer volume is below 10% of the pipette's max, note it in `design-notes.json` under `key_decisions` (see appendix for schema) and suggest a smaller pipette if one is available.

**OT-2 pipette names and extended tables:** `references/authoring-appendix.md`.

## References (core)

- Protocol patterns: `references/python-protocol-patterns.md`
- Pattern index: `references/pattern-library.md`
- Flex liquid classes (official): `references/liquid-classes-flex.md`
- Finalize / checklist / design-notes / OT-2 tables: `references/authoring-appendix.md`
- Flex template: `assets/flex_protocol_template.py`
- Flex workflow templates: `assets/flex_template_cell_culture_passaging.py`, `assets/flex_template_pcr_setup.py`, `assets/flex_template_serial_dilution.py`
- Flex liquid-class example: `assets/flex_liquid_classes_example.py`
- OT-2 template: `assets/protocol_template.py`
- Extra code snippets (not default starters): `assets/archive/README.md`
