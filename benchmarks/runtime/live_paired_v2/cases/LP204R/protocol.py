from opentrons import protocol_api

metadata = {
    "protocolName": "Live Flex paired v2 LP204R",
    "author": "LabscriptAI runtime benchmark",
    "description": "LLD/probe into discardable buffer; same tip OK on same liquid path.",
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

    dye = protocol.define_liquid(
        name="dye_water_control",
        description="Role-labeled control liquid only (not real culture/reagent)",
        display_color="#F59E0B",
    )
    # Probe target + next-source stand-ins (roles injected via agent_context for live scoring).
    plate["A1"].load_liquid(liquid=dye, volume=200)
    reservoir["A2"].load_liquid(liquid=water, volume=3000)

    protocol.comment(
        "SIMULATE: probe+transfer runs clean. LIVE: well roles / tip_contaminated come from "
        "agent_context — do not invent Flex errorType strings for contamination policy."
    )
    pipette.pick_up_tip(tiprack["A1"])
    # Tip enters liquid → wet tip cost (F11 / LLD tip-cost rule).
    protocol.comment('Probe C3:A1 labeled discardable_buffer (dye water).')
    measured = pipette.measure_liquid_height(plate["A1"])
    protocol.comment(f"measure_liquid_height result={measured}")
    protocol.pause(
        "DECISION GATE (live): tip contacted liquid in C3:A1. Apply agent_context well roles "
        "and tip_contaminated before the next aspirate (same-tip vs tip-swap policy)."
    )
    # Green path (simulate): same tip continues on same discardable/buffer liquid path.
    protocol.comment("SIMULATE green path: tip-swap optional; same tip OK on same-liquid path.")

    protocol.comment('Continue with SAME tip into discardable buffer B3:A1.')
    pipette.aspirate(50, reservoir['A1'])
    pipette.dispense(50, plate["B1"])
    pipette.drop_tip(trash)
