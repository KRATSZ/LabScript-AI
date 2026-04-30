# Flex: Opentrons-verified liquid classes (official)

Do **not** hand-tune arbitrary µL/s tables when the Opentrons API already encodes aspirate/dispense behavior per liquid type.

## Verified classes (three)

| Load name | Role |
|-----------|------|
| `water` | Aqueous (DI water–like) |
| `ethanol_80` | Volatile (80% ethanol–like) |
| `glycerol_50` | Viscous (50% glycerol–like) |

Source: [Python API: Liquid Classes](https://docs.opentrons.com/python-api/liquid-classes/).

## How to use

1. Set `requirements` to a Flex `apiLevel` that supports liquid classes: **minimum 2.24** for `transfer_with_liquid_class`. This repo’s Flex templates default to **2.24**. Newer installs often support higher API levels (e.g. **2.27** on many 8.8.x builds) — raise toward `MAX_SUPPORTED_VERSION` when you need features beyond 2.24, not as a template default requirement.
2. Load tips, trash, pipette, and labware.
3. Call `protocol.get_liquid_class(name="water" | "ethanol_80" | "glycerol_50")`.
4. Transfer with `pipette.transfer_with_liquid_class(liquid_class=..., volume=..., source=..., dest=..., new_tip=..., trash_location=...)`.

The runtime applies submerge speed, flow rate by volume, air gaps, delays, and related behavior from the verified definition — **prefer this over copying magic numbers into the protocol.**

### CRITICAL: one-to-many / many-to-one with liquid classes

`transfer_with_liquid_class` inherits the same length rules as `transfer`: **source and destination must be 1:1 or equal-length lists**. There is NO `distribute_with_liquid_class` or `consolidate_with_liquid_class` API.

**To transfer one source → many destinations with a liquid class, loop per destination:**

```python
for well in dest_wells:
    pipette.transfer_with_liquid_class(
        liquid_class=lc_water,
        volume=50,
        source=reservoir["A1"],
        dest=well,
        new_tip="always",
        trash_location=trash,
    )
```

**Do NOT pass a list as dest with a single source** — this will raise `ValueError: Sources and destinations should be of the same length`. The `distribute()` and `consolidate()` shortcuts do NOT support liquid classes.

## Customization

You may clone a verified class and edit specific properties (see [Liquid Class Definitions](https://docs.opentrons.com/python-api/liquid-class-definitions/)). Keep changes minimal and document why in `design-notes.json`.

## OT-2 (no verified liquid classes in the same form)

For OT-2 or when you cannot raise `apiLevel`, use building-block commands with the `rate=` multiplier on `aspirate` / `dispense` (relative to that pipette’s defaults), or set `pipette.flow_rate.aspirate` / `dispense` in µL/s. See [Liquid control](https://docs.opentrons.com/python-api/building-block-commands/liquids/).

## Example in this repo

- `assets/flex_liquid_classes_example.py` — minimal Flex sample using all three verified classes.
