from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP205E",
    "author": "LabscriptAI runtime benchmark",
    "description": "Door pause beyond max_pause_s; escalate even if backup/deck look fine.",
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
        "SIMULATE: pause returns immediately. LIVE: open door at this checkpoint; "
        "record injected observed_pause_s in agent_context (do not wait real 20 min)."
    )
    pipette.pick_up_tip(tiprack["A1"])
    pipette.aspirate(100, reservoir["A1"])
    protocol.pause(
        "LIVE ONLY: open Flex door briefly for pause-window case; close door; "
        "do NOT blind resume — await YOLO+VLM+reconcile and injected pause clock."
    )
    pipette.dispense(100, plate["A1"])
    pipette.drop_tip(trash)
