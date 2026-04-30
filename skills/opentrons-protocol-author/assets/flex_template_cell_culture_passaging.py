"""Template: 6-well cell culture passaging (remove medium → PBS rinse → remove PBS → trypsin → neutralize).

Fill slot and volume placeholders for your lab. Add a temperature module for 37 °C incubations
if your workflow requires on-deck holds (commented pattern below).
Uses apiLevel 2.24 — for verified liquid classes on Flex, see flex_liquid_classes_example.py
with apiLevel 2.28+ instead of manual flow_rate tuning.

Biology note (template, not a validated SOP):
- Remove spent medium before PBS so trypsin is not diluted by leftover culture fluid.
- After PBS wash, aspirate PBS from the well before adding trypsin.
- After trypsin incubation, cells are detached. Do **not** aspirate the well to trash unless
  your SOP says so (that would discard cells).
- **Option A (this template):** Add complete growth medium to neutralize trypsin, then mix.
- **Option B:** Removing trypsin / centrifugation / reseeding — implement per lab SOP (often off-deck).
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Flex — cell culture passaging (6-well) template",
    "author": "Replace",
    "description": "Remove medium, PBS wash, trypsinize, neutralize with medium, mix — tune volumes.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}

# Example wash / removal volumes (µL); tune per well size and starting fill.
_WASH_VOL = 1000.0


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    parameters.add_float(
        display_name="Well bottom clearance (mm)",
        variable_name="well_bottom_clearance_mm",
        default=2.0,
        minimum=0.5,
        maximum=5.0,
    )
    parameters.add_float(
        display_name="Trypsin per well (µL)",
        variable_name="trypsin_volume_ul",
        default=500.0,
        minimum=50.0,
        maximum=2000.0,
    )
    parameters.add_float(
        display_name="Medium per well (µL)",
        variable_name="medium_volume_ul",
        default=2000.0,
        minimum=200.0,
        maximum=2500.0,
    )


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")

    pbs = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    trypsin = protocol.load_labware("nest_12_reservoir_15ml", "B2")
    medium = protocol.load_labware("nest_12_reservoir_15ml", "B1")
    plate = protocol.load_labware("corning_6_wellplate_16.8ml_flat", "C3")

    pipette = protocol.load_instrument(
        "flex_1channel_1000",
        "left",
        tip_racks=[tiprack],
    )

    # Default clearance keeps the tip above the adherent cell layer.
    clearance = protocol.params.well_bottom_clearance_mm
    trypsin_vol = protocol.params.trypsin_volume_ul
    medium_vol = protocol.params.medium_volume_ul
    wash = min(_WASH_VOL, pipette.max_volume)

    wells = ["A1", "A2", "A3", "B1", "B2", "B3"]

    for well in wells:
        w = plate[well]
        # 1) Remove spent culture medium (repeat or increase volume if wells were overfilled).
        pipette.pick_up_tip()
        pipette.aspirate(wash, w.bottom(clearance))
        pipette.dispense(wash, trash)
        pipette.drop_tip(trash)

        # 2) PBS rinse, then remove PBS before trypsin (do not layer trypsin on top of PBS).
        pipette.pick_up_tip()
        pipette.aspirate(wash, pbs["A1"])
        pipette.dispense(wash, w.top())
        pipette.blow_out(w.top())
        pipette.aspirate(wash, w.bottom(clearance))
        pipette.dispense(wash, trash)
        pipette.drop_tip(trash)

        # 3) Trypsin for detachment
        pipette.pick_up_tip()
        pipette.aspirate(trypsin_vol, trypsin["A1"])
        pipette.dispense(trypsin_vol, w.top())
        pipette.drop_tip(trash)

    # Incubation at 37 °C for trypsinization.
    # WARNING: Trypsin is temperature-sensitive. If on-deck temperature control is needed,
    # uncomment the module loading below. Without it, room-temperature incubation may give
    # inconsistent detachment — operator should monitor visually.
    protocol.comment("=== Trypsin incubation (room temp ~5 min) ===")
    protocol.comment("Operator: visually check cell detachment before proceeding.")
    protocol.comment("If using Temperature Module, load it and set to 37C before this step.")
    # Uncomment for on-deck temp control:
    # temp_mod = protocol.load_module("temperatureModuleV2", "D1")
    # temp_mod.set_temperature(37)
    # temp_mod.deactivate()
    protocol.delay(seconds=300, msg="Trypsin incubation — check detachment before resuming")

    # Option A — neutralize trypsin and resuspend cells in the same well (see module docstring).
    for well in wells:
        w = plate[well]
        pipette.pick_up_tip()
        remaining = medium_vol
        while remaining > 0:
            chunk = min(remaining, pipette.max_volume)
            pipette.aspirate(chunk, medium["A1"])
            pipette.dispense(chunk, w.top())
            remaining -= chunk
        pipette.mix(
            repetitions=3,
            volume=min(300, min(medium_vol, pipette.max_volume) * 0.3),
            location=w.bottom(max(1.0, clearance + 1.0)),
        )
        pipette.drop_tip(trash)
