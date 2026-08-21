"""Minimal Opentrons protocol strings for authoring-check / llmreview tests."""

from __future__ import annotations

PROTOCOL_HEADER = """from opentrons import protocol_api

metadata = {"protocolName": "wave2-fixture", "apiLevel": "2.21"}

def run(protocol: protocol_api.ProtocolContext):
"""

PROTOCOL_VOLUME_MISMATCH = (
    PROTOCOL_HEADER
    + """
    tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "B1")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D1")
    pipette = protocol.load_instrument("flex_1channel_200", "left", tip_racks=[tips])
    water = protocol.define_liquid("water", "water", "#0000ff")
    plate["A1"].load_liquid(water, 200)
    pipette.pick_up_tip()
    pipette.aspirate(100, plate["A1"])
    pipette.dispense(100, plate["B1"])
    pipette.drop_tip()
"""
)

PROTOCOL_MATCHING_100UL = PROTOCOL_VOLUME_MISMATCH

PROTOCOL_SAME_TIP_STOCK = (
    PROTOCOL_HEADER
    + """
    tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "B1")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D1")
    stock = protocol.load_labware("nest_12_reservoir_15ml", "C1")
    pipette = protocol.load_instrument("flex_1channel_200", "left", tip_racks=[tips])
    pipette.pick_up_tip()
    pipette.aspirate(50, plate["A1"])
    pipette.dispense(50, plate["B1"])
    pipette.aspirate(50, stock["A1"])
    pipette.dispense(50, plate["C1"])
    pipette.drop_tip()
"""
)

PROTOCOL_EMPTY_SOURCE = (
    PROTOCOL_HEADER
    + """
    tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "B1")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D1")
    pipette = protocol.load_instrument("flex_1channel_200", "left", tip_racks=[tips])
    water = protocol.define_liquid("water", "water", "#0000ff")
    plate["A1"].load_liquid(water, 20)
    pipette.pick_up_tip()
    pipette.aspirate(200, plate["A1"])
    pipette.dispense(200, plate["B1"])
    pipette.drop_tip()
"""
)

PROTOCOL_PIPETTE_OVERVOLUME = (
    PROTOCOL_HEADER
    + """
    tips = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B1")
    plate = protocol.load_labware("nest_96_wellplate_2ml_deep", "D1")
    pipette = protocol.load_instrument("flex_1channel_200", "left", tip_racks=[tips])
    water = protocol.define_liquid("water", "water", "#0000ff")
    plate["A1"].load_liquid(water, 800)
    pipette.pick_up_tip()
    pipette.aspirate(500, plate["A1"])
    pipette.dispense(500, plate["B1"])
    pipette.drop_tip()
"""
)
