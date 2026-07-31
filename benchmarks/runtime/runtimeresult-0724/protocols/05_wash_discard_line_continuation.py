"""Flex continuation — Wash discard only (after overpressure FIX).

Deck (same as 05_wash_discard_line.py):
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
  A3  trash bin

Retries unfinished discard only: Wash Buffer C2.A3 -> D2.H12 200 uL.
Prime step already completed on parent run; do not re-prime.
Liquid probe disabled (failure mode was liquidProbe overpressure).
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
        default=False,
    )


metadata = {
    "protocolName": "Wash discard line — discard continuation",
    "author": "LabscriptAI OT",
    "description": "FIX continuation: discard Wash Buffer to plate waste well only.",
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
    if dry_run_on:
        protocol.comment("DRY RUN: no liquids loaded; tips return to rack.")

    wash = reservoir["A3"]
    waste = plate["H12"]

    # Parent run consumed B2.A1 (prime) and B2.B1 (failed discard probe tip).
    protocol.comment("FIX continuation: Wash Buffer C2.A3 -> D2.H12 (non-precious)")
    pipette.pick_up_tip(tip_rack["C1"])
    if use_liquid_probe:
        pipette.require_liquid_presence(wash)
    pipette.aspirate(200, wash.bottom(2))
    pipette.dispense(200, waste.bottom(2))
    finish_tip(pipette, trash, dry_run_on)
