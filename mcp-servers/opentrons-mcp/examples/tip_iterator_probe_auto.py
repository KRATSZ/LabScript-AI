"""Probe: auto tip iterator after fixit recovery (A2 tiprack, A1 empty)."""

from opentrons import protocol_api

metadata = {
    "protocolName": "Tip Iterator Probe AUTO",
    "author": "Opentrons-Lab-Agent",
    "description": "Three automatic pick_up_tip() calls; A1 should fail, fixit to B1, then observe next pickup.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.22"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "A2")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    for i in range(3):
        pipette.pick_up_tip()
        protocol.comment(f"auto_pick_{i + 1}_ok")
        pipette.drop_tip()
