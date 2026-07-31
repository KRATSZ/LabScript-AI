from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP203R",
    "author": "LabscriptAI runtime benchmark",
    "description": "Ordinary overpressure path into waste trough (live seal is operator-only).",
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
    reservoir["A1"].load_liquid(liquid=water, volume=3000)
    protocol.comment(
        "SIMULATE: runs clean. LIVE fault: seal waste well B3:A12 (parafilm) before dispense."
    )
    pipette.pick_up_tip(tiprack["A1"])
    pipette.aspirate(100, reservoir["A1"])
    # Waste trough A12 — live colleague seals orifice/well to raise overpressure.
    pipette.dispense(100, reservoir["A12"])
    pipette.drop_tip(trash)
