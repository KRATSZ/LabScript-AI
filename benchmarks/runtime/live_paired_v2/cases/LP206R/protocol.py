from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP206R",
    "author": "LabscriptAI runtime benchmark",
    "description": "Evidence-sufficient mild reconcile then continue (no camera in simulate).",
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
        "SIMULATE: no camera hardware. LIVE decision-layer only — inject YOLO/VLM/reconcile "
        "summaries via agent_context at the pause gate. Never invent Flex errorType for this pair."
    )
    pipette.pick_up_tip(tiprack["A1"])
    pipette.aspirate(50, reservoir["A1"])
    protocol.pause(
        "DECISION GATE (live): evaluate evidence sufficiency (YOLO+VLM+reconcile summaries). "
        "Do NOT auto fine-tune / nudge plate position. Reconcile-or-abstain only."
    )
    pipette.dispense(50, plate["A1"])
    pipette.drop_tip(trash)
