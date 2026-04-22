# Python Protocol Patterns

## Scope

This note is grounded in the local Opentrons sources under:

- `opentrons/api/docs/v2/example_protocols/`
- `opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- `opentrons/api/tests/opentrons/data/testosaur_with_rtp.py`

## Core File Shape

Modern protocols should usually look like:

```python
from opentrons import protocol_api

metadata = {...}
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    ...

def run(protocol: protocol_api.ProtocolContext) -> None:
    ...
```

Notes:

- Older examples still put `apiLevel` inside `metadata`, but the local parser also recognizes `requirements`.
- **This repo’s Flex templates** use `requirements = {"robotType": "Flex", "apiLevel": "2.24"}` as the default baseline (liquid-class compatible).
- Runtime parameters (`protocol.params`) require apiLevel >= 2.18; **2.24** is the default for new Flex work here.
- Use `apiLevel >= 2.24` when using `get_liquid_class()` / `transfer_with_liquid_class()` (same floor as default templates).
- OT-2 protocols may omit `robotType`, but being explicit is better when the target matters.

## Flex pipette and tip load names

### Pipettes

| Load name | Channels | Volume range |
|-----------|----------|-------------|
| `flex_1channel_50` | 1 | 1-50 µL |
| `flex_1channel_1000` | 1 | 5-1000 µL |
| `flex_8channel_50` | 8 | 1-50 µL |
| `flex_8channel_1000` | 8 | 5-1000 µL |
| `flex_96channel_1000` | 96 | 5-1000 µL |

**Do NOT use:** `flex_1channel_200`, `flex_8channel_200`, `flex_8channel_200` — these do not exist.

### Tip racks

| Load name | Tip capacity |
|-----------|-------------|
| `opentrons_flex_96_tiprack_50ul` | 50 µL |
| `opentrons_flex_96_tiprack_200ul` | 200 µL |
| `opentrons_flex_96_tiprack_1000ul` | 1000 µL |

### Common Flex labware (verified load names)

Use ONLY these exact names. If you're unsure whether a name exists, prefer one from this table:

| Load name | Description |
|-----------|-------------|
| **Reservoirs** | |
| `nest_12_reservoir_15ml` | 12-well reservoir, 15 mL/well |
| `nest_1_reservoir_195ml` | 1-well reservoir, 195 mL |
| `usascientific_12_reservoir_22ml` | 12-well reservoir, 22 mL/well |
| **Tube racks (Opentrons namespace)** | |
| `opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical` | 10-tube rack: 4×50 mL + 6×15 mL |
| `opentrons_15_tuberack_falcon_15ml_conical` | 15-tube rack: 15 mL conical |
| `opentrons_24_tuberack_generic_2ml_screwcap` | 24-tube rack: 2 mL screwcap |
| **Tube racks (NEST namespace)** | |
| `nest_12_reservoir_15ml` | NEST 12-well reservoir |
| **Plates** | |
| `nest_96_wellplate_200ul_flat` | 96-well plate, 200 µL, flat bottom |
| `nest_96_wellplate_2ml_deep` | 96-well deep-well plate, 2 mL |
| `corning_96_wellplate_360ul_flat` | 96-well plate, 360 µL, flat bottom |
| `biorad_96_wellplate_200ul_pcr` | 96-well PCR plate |
| `corning_6_wellplate_16.8ml_flat` | 6-well plate, 16.8 mL |

**IMPORTANT:** Do NOT guess or invent labware names. Common mistakes:
- `opentrons_6_tuberack_falcon_15ml_conical` does NOT exist (correct: `opentrons_15_tuberack_falcon_15ml_conical`)
- `opentrons_flex_96_tiprack_1000ul` uses lowercase `ul` (not `uL`)
- Always verify: if unsure, use the `opentrons-protocol-verify` skill or simulate to catch bad names.

```python
tips_200 = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "D2")
pipette = protocol.load_instrument("flex_8channel_1000", "left", tip_racks=[tips_200])
```

### Tip selection heuristic

- Volumes ≤50 µL: use `50ul` tips with a 50µL pipette (best accuracy).
- Volumes 5-200 µL: use `200ul` tips with a 1000µL pipette.
- Volumes >200 µL: use `1000ul` tips with a 1000µL pipette.
- For protocols needing both small and large volumes, use a 1000µL pipette with 200ul tips as compromise, and flag if precision is critical at low volumes.
- If an operator asks for a "P300" on Flex, translate that into a real Flex choice instead of inventing a 300 µL model:
  usually `flex_1channel_1000` + `200ul` tips for mid-volume work, or `flex_1channel_50` if the critical transfers are mostly ≤50 µL.

## Flex trash bin

Every Flex protocol MUST load a trash bin and pass it to `drop_tip(...)`:

```python
trash = protocol.load_trash_bin("A3")
# ...
pipette.drop_tip(trash)
```

Use an explicit slot consistent with your deck layout (this repo’s templates default to **`"A3"`**). If your deck uses another trash slot, change the string to match the Flex deck map.

## OT-2 vs Flex

- OT-2 uses integer deck slots like `1`, `2`, `3`.
- Flex uses addressable slots like `"D1"`, `"D2"`, `"D3"`.
- Flex uses `load_trash_bin()` instead of loading trash as labware.
- Flex pipettes have different load names (see table above).
- Flex tip racks have different load names (see table above).

### Slot correspondence

| Flex | A1 | A2 | A3 | B1 | B2 | B3 | C1 | C2 | C3 | D1 | D2 | D3 |
|------|----|----|----|----|----|----|----|----|----|----|----|-----|
| OT-2 | 10 | 11 | Trash | 7 | 8 | 9 | 4 | 5 | 6 | 1 | 2 | 3 |

## Runtime Parameters

The local test protocol `testosaur_with_rtp.py` shows the supported pattern:

- define `add_parameters(parameters: protocol_api.ParameterContext) -> None`
- use `parameters.add_int(...)`, `parameters.add_str(...)`, and similar helpers
- consume values inside `run()` via `protocol.params.<variable_name>`

**IMPORTANT constraints on `add_parameters` arguments:**

- **`display_name` must be ≤ 30 characters.** The API raises `ParameterNameError` for longer names. Use concise labels: `"Incubation (min)"` not `"Incubation time in minutes (0 = skip)"`.
- **Use ALL keyword arguments or ALL positional — never mix.** The correct call pattern:
  ```python
  # CORRECT: all keyword
  parameters.add_int(display_name="Incubation (min)", variable_name="incubation_min", default=5, minimum=0, maximum=60)

  # WRONG: mixing positional display_name with keyword display_name
  parameters.add_int("Incubation (min)", variable_name="incubation_min", display_name="Incubation")  # TypeError!
  ```
- `variable_name` must be a valid Python identifier.
- `default` must fall within `minimum` and `maximum` for numeric types.
- **`add_str` `choices` must be a list of `{"display_name": ..., "value": ...}` dicts**, NOT plain strings. Plain strings like `choices=["auto", "P50", "P1000"]` cause `TypeError: string indices must be integers, not 'str'` at runtime. Correct:
  ```python
  parameters.add_str(
      display_name="Pipette type",
      variable_name="pipette_type",
      default="auto",
      choices=[
          {"display_name": "Auto", "value": "auto"},
          {"display_name": "P50", "value": "P50"},
          {"display_name": "P1000", "value": "P1000"},
      ],
  )
  ```
  This applies to `add_str` only — `add_int` and `add_float` do not have a `choices` parameter.

Use runtime parameters when:

- the user wants one protocol reused for multiple batch sizes
- mount, pipette, sample count, or file inputs vary per run

Do not use runtime parameters for constants that never change.

## Camera Capture

The local `ProtocolContext.capture_image()` method supports:

- `home_before`
- `filename`
- `resolution`
- `zoom`
- `contrast`
- `brightness`
- `saturation`

Use it only when:

- the workflow explicitly needs run-time imaging
- the requested API level is high enough for camera capture in the target environment

When adding capture points, keep them intentional:

- after setup verification
- before or after a critical transfer step
- during inspection or recovery workflows

## Magnetic Block pattern (Flex)

Flex Magnetic Block is **passive** — no engage/disengage API. Use the gripper to move plates on and off:

```python
mag_block = protocol.load_module("magneticBlockV1", "C1")
# Gripper moves plate onto block for bead separation
# Then waits:
protocol.delay(minutes=2)
# Gripper moves plate off block for wash/elution
```

**Differences from OT-2 Magnetic Module:**
- OT-2: `mag_deck.engage()` / `mag_deck.disengage()` — actively moves magnets.
- Flex: No engage API. Plate sits on block; bead separation happens passively.
- Flex: Requires gripper to move plate on/off block. Plan deck layout accordingly.

## Heater-Shaker pattern

```python
hs = protocol.load_module("heaterShakerModuleV1", "B1")
hs_adapter = hs.load_labware("opentrons_96_deep_well_adapter")
plate = hs_adapter.load_labware("nest_96_wellplate_2ml_deep")

# Blocking: wait for temperature
hs.set_and_wait_for_temperature(37)

# Non-blocking: continue pipetting while heating
hs.set_temperature(95)
# ... do other pipetting here ...
hs.wait_for_temperature()

# Shaking (must latch first)
hs.set_latch_status(True)
hs.set_shake_speed(1000)
protocol.delay(minutes=5)
hs.deactivate_shaker()
```

**Rules:**
- Must latch before shaking.
- Non-blocking temperature set requires `wait_for_temperature()` before use.
- Requires appropriate thermal adapter for the labware type.

## Authoring Checklist

- Robot type is explicit (`"Flex"`).
- API level is explicit (Flex default **≥2.24** in this repo; liquid classes need that floor).
- Labware load names exist for the target robot (Flex prefix: `opentrons_flex_*`).
- Pipette load names match the table above — no made-up model names.
- Mounts: `"left"` or `"right"` for 1/8-channel; both mounts for 96-channel.
- Runtime parameters are only used where they make the protocol more reusable.
- Camera usage is purposeful and not decorative.
- Custom labware or bundled files are called out.
- **Flex trash bin**: Every Flex protocol MUST include `protocol.load_trash_bin()`.
- **Volume splits**: Transfers exceeding pipette max are split into multiple operations.
- **Tip sufficiency**: Total tips needed ≤ tips available (96 per rack).
- **Dead volume**: Source labware is loaded with transfer volume + dead volume.
- **Liquid classes**: Use `transfer_with_liquid_class()` when reagent matches a verified class. Do NOT hand-tune µL/s tables for water/ethanol_80/glycerol_50.

## Volume Splitting Pattern

When a transfer volume exceeds the pipette's max volume, split it automatically:

```python
def transfer_large_volume(pipette, volume, source, dest, **kwargs):
    """Transfer volume > pipette max by splitting into multiple transfers."""
    max_vol = pipette.max_volume
    remaining = volume
    while remaining > 0:
        chunk = min(remaining, max_vol)
        pipette.aspirate(chunk, source, **kwargs)
        pipette.dispense(chunk, dest, **kwargs)
        remaining -= chunk
```

For 1500 µL with a P1000: `1000 + 500`. For 2000 µL: `1000 + 1000`.

## Mixing Pattern

After adding reagent to a well, always mix to ensure homogeneity:

```python
pipette.mix(repetitions=3, volume=50, location=plate["A1"])
```

Mix volume should typically be 50-80% of what was just dispensed, capped at pipette max.

## Incubation / Delay Pattern

Use `protocol.delay()` for timed incubations. Add a comment for manual handoff steps:

```python
# Automated incubation
protocol.delay(minutes=5)

# Manual handoff — pause and prompt the operator
protocol.pause("Centrifuge the plate at 12,000 x g, 4°C for 15 min, then return to deck.")
```

For long incubations (hours), use `protocol.delay(minutes=...)` or note that
the protocol will pause and the operator should resume after the incubation.

## Flow rate pattern (when not using liquid classes)

For reagents that do NOT match the three verified liquid classes:

```python
# Save current flow rate BEFORE changing
saved_aspirate = pipette.flow_rate.aspirate
saved_dispense = pipette.flow_rate.dispense

# Slow aspirate for viscous liquids
pipette.flow_rate.aspirate = 25  # µL/s

# Fast dispense for resuspension
pipette.flow_rate.dispense = 500  # µL/s

# Reset to saved values after special handling
pipette.flow_rate.aspirate = saved_aspirate
pipette.flow_rate.dispense = saved_dispense
```

**IMPORTANT:** `pipette.default_flow_rate` does NOT exist on `InstrumentContext`. To restore defaults after a temporary change, save the current value before modifying.

Common patterns from reference protocols:
- **Supernatant removal** (bead work): aspirate 25-30 µL/s, dispense 150 µL/s.
- **Bead resuspension**: dispense 500 µL/s, mix 10 reps.
- **Gentle aspiration** (cells): aspirate at half default rate.

## One-to-Many / Many-to-One Transfers

`pipette.transfer()` requires **equal-length** source and destination lists. For unequal lengths:

- **One source → many destinations:** use `pipette.distribute(vol, source, [dest1, dest2, ...])` or loop manually.
- **Many sources → one destination:** use `pipette.consolidate(vol, [src1, src2, ...], dest)` or loop manually.

```python
# CORRECT: distribute from one source to many wells
pipette.distribute(50, reservoir["A1"], [plate.wells_by_name()[w] for w in targets])

# CORRECT: loop for complex per-well logic
for well_name in targets:
    pipette.transfer(50, reservoir["A1"], plate[well_name], new_tip="once")

# WRONG: mismatched lengths → ValueError at runtime
pipette.transfer(50, reservoir["A1"], [plate["A1"], plate["A2"], plate["A3"]])
```

## Flex: verified liquid classes

Opentrons defines three verified liquid classes for Flex (`water`, `ethanol_80`, `glycerol_50`) with `get_liquid_class` and `transfer_with_liquid_class`. Prefer that path over inventing per-liquid µL/s tables. See `liquid-classes-flex.md` and `../assets/flex_liquid_classes_example.py`.

**Only these three names are verified.** Do NOT invent names like `glycerol`, `ethanol`, `dmem`, etc. — the runtime will reject unknown class names. For unlisted liquids, use `rate=` or `flow_rate` overrides instead of `transfer_with_liquid_class`.
