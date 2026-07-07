"""Probe: explicit well pick_up_tip after fixit recovery (A2 tiprack, A1 empty)."""

from opentrons import protocol_api

metadata = {
    "protocolName": "Tip Iterator Probe EXPLICIT",
    "author": "Opentrons-Lab-Agent",
    "description": "Three explicit pick_up_tip(well) calls; tests double-occupancy on B1 after fixit.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.22"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "A2")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    for well in ("A1", "B1", "C1"):
        pipette.pick_up_tip(tiprack[well])
        protocol.comment(f"explicit_pick_{well}_ok")
        pipette.drop_tip()
