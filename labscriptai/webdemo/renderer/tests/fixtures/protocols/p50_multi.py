"""Legacy P50 8-channel column transfer with a returned tip."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: legacy P50 multi"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    # The 8.8.2 official catalog has no 200 uL tiprack; P50 uses 300 uL tips.
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "P50-compatible tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "3", "destination plate")
    p50 = ctx.load_instrument("p50_multi", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "legacy P50 multi source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 1000)
    p50.pick_up_tip(tips["A1"])
    p50.aspirate(10, reservoir["A1"].bottom(1))
    p50.dispense(10, plate["A1"].bottom(1))
    p50.return_tip()
