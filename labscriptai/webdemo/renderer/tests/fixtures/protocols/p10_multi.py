"""Legacy P10 8-channel column transfer with a returned tip."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: legacy P10 multi"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_10ul", "1", "10 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "3", "destination plate")
    p10 = ctx.load_instrument("p10_multi", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "legacy P10 multi source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 1000)
    p10.pick_up_tip(tips["A1"])
    p10.aspirate(5, reservoir["A1"].bottom(1))
    p10.dispense(5, plate["A1"].bottom(1))
    p10.return_tip()
