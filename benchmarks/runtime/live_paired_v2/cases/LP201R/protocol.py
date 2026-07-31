from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP201R",
    "author": "LabscriptAI runtime benchmark",
    "description": "Tip-missing recovery with enough global tip budget for ten work units.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    water = protocol.define_liquid(
        name="water_control",
        description="Non-biological live recovery control liquid",
        display_color="#3B82F6",
    )
    reservoir["A1"].load_liquid(liquid=water, volume=2200)
    tip_names = ['A1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2']
    destination_names = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2']

    for tip_name, destination_name in zip(tip_names, destination_names):
        pipette.pick_up_tip(tiprack[tip_name])
        pipette.aspirate(20, reservoir["A1"])
        pipette.dispense(20, plate[destination_name])
        pipette.drop_tip(trash)
