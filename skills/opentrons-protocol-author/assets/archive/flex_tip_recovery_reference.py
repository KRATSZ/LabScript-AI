from opentrons import protocol_api

metadata = {
    "protocolName": "Flex Tip Recovery Reference",
    "author": "Opentrons-Lab-Agent",
    "description": "Small Flex reference protocol for exercising pickup and recovery-oriented troubleshooting.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.22"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    tip_rack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tip_rack])

    pipette.pick_up_tip(tip_rack["A1"])
    protocol.comment("tip pickup reference complete")
    pipette.drop_tip()
