"""Flex protocol — High-volume buffer plate load.

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
    "protocolName": "High-volume buffer plate load",
    "author": "LabscriptAI OT",
    "description": "Load larger Assay Buffer volumes into three precious sample wells from primary stock.",
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

    primary = reservoir["A1"]
    reserve = reservoir["A2"]
    samples = [plate["A1"], plate["A2"], plate["A3"]]

    protocol.comment("High-volume Assay Buffer C2.A1 -> A1-A3 (quantitative)")
    protocol.comment(f"Reserve same-identity stock at C2.A2 ({reserve.well_name})")
    protocol.comment(
        "LPD: require_liquid_presence on primary before each 200 uL draw "
        "(not once before the loop)."
    )
    pipette.pick_up_tip()
    for dest in samples:
        if use_liquid_probe:
            pipette.require_liquid_presence(primary)
        pipette.transfer_with_liquid_class(
            liquid_class=water, volume=200, source=primary, dest=dest,
            new_tip="never", trash_location=trash,
        )
    finish_tip(pipette, trash, dry_run_on)

    protocol.comment("Confirm D2.A1")
    pipette.pick_up_tip()
    if use_liquid_probe:
        pipette.require_liquid_presence(samples[0])
    finish_tip(pipette, trash, dry_run_on)

