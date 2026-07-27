from opentrons import protocol_api

metadata = {
    "protocolName": "Flex Tip Recovery Validation",
    "author": "Cursor",
    "description": "Intentionally starts from a known empty tip well so runtime fixit recovery can be validated.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.22"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    pipette.pick_up_tip(tiprack["A1"])
    protocol.comment("recovery pickup succeeded")
    pipette.drop_tip()
