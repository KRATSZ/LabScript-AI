from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP202E",
    "author": "LabscriptAI runtime benchmark",
    "description": "Empty primary; same-liquid backup exists but volume short of required aspirate.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    liquid = protocol.define_liquid(
        name="wash_buffer",
        description="Control liquid identity for annotated backup discrimination (water/dye only)",
        display_color="#10B981",
    )
    # Primary A1 starts empty; A2 holds the annotated same-liquid_id backup.
    reservoir["A2"].load_liquid(liquid=liquid, volume=40)
    protocol.comment(
        "A1 must start empty for liquidNotFound; A2 is annotated same-liquid backup "
        "(40 uL wash_buffer)"
    )

    pipette.pick_up_tip(tiprack["A1"])
    pipette.require_liquid_presence(reservoir["A1"])
    pipette.aspirate(100, reservoir["A1"])
    pipette.dispense(100, plate["A1"])
    pipette.drop_tip(trash)
