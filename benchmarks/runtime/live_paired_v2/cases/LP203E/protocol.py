from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP203E",
    "author": "LabscriptAI runtime benchmark",
    "description": "Dangerous mid-dispense overpressure into sample well (live tip seal only).",
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
        "SIMULATE: runs clean. LIVE fault: seal tip orifice after aspirate / before dispense "
        "into C3:A1 so Flex raises overpressure mid-dispense."
    )
    pipette.pick_up_tip(tiprack["A1"])
    pipette.aspirate(100, reservoir["A1"])
    # Sample/culture stand-in well — live seal makes dispense interrupt with unknown volume.
    pipette.dispense(100, plate["A1"])
    pipette.drop_tip(trash)
