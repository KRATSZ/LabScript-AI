"""Flex protocol — Dual-well buffer load.

Deck (same family as automation/new/protocol_b2_tip_c2_water_to_c1.py):
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
  A3  trash bin
"""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def finish_tip(pipette, trash, dry_run_on: bool) -> None:
    if dry_run_on:
        pipette.return_tip()
    else:
        pipette.drop_tip(trash)


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    parameters.add_bool(
        display_name="Dry run: return tips",
        variable_name="dry_run_on",
        default=False,
    )
    parameters.add_bool(
        display_name="Use liquid probe",
        variable_name="use_liquid_probe",
        default=True,
    )

metadata = {
    "protocolName": "Dual-well buffer load",
    "author": "LabscriptAI OT",
    "description": "Load assay buffer into two sample wells, then discard wash to waste well.",
}


def run(protocol: protocol_api.ProtocolContext) -> None:

    trash = protocol.load_trash_bin("A3")
    tip_rack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")

    dry_run_on = protocol.params.dry_run_on
    use_liquid_probe = protocol.params.use_liquid_probe

    pipette = protocol.load_instrument(
        "flex_1channel_1000",
        "left",
        tip_racks=[tip_rack],
        liquid_presence_detection=use_liquid_probe,
    )
    water = protocol.get_liquid_class(name="water")
    glycerol = protocol.get_liquid_class(name="glycerol_50")
    if dry_run_on:
        protocol.comment("DRY RUN: no liquids loaded; tips return to rack.")

    # Tip pickups in a clean run: 3
    buf = reservoir["A1"]
    wash = reservoir["A3"]
    samples = [plate["A1"], plate["A2"]]
    waste = plate["H12"]

    protocol.comment("Step 1: Assay Buffer -> D2.A1 / A2")
    pipette.pick_up_tip()
    if use_liquid_probe:
        pipette.require_liquid_presence(buf)
    for dest in samples:
        pipette.transfer_with_liquid_class(
            liquid_class=water, volume=100, source=buf, dest=dest,
            new_tip="never", trash_location=trash,
        )
    finish_tip(pipette, trash, dry_run_on)

    protocol.comment("Step 2: Wash Buffer -> D2.H12")
    pipette.pick_up_tip()
    if use_liquid_probe:
        pipette.require_liquid_presence(wash)
    pipette.transfer_with_liquid_class(
        liquid_class=water, volume=150, source=wash, dest=waste,
        new_tip="never", trash_location=trash,
    )
    finish_tip(pipette, trash, dry_run_on)

    protocol.comment("Step 3: confirm D2.A1")
    pipette.pick_up_tip()
    if use_liquid_probe:
        pipette.require_liquid_presence(samples[0])
    finish_tip(pipette, trash, dry_run_on)

