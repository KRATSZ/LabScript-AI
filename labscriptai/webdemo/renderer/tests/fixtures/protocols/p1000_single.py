"""Legacy P1000 single-channel transfer with a returned tip."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: legacy P1000 single"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_1000ul", "1", "1000 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "3", "destination plate")
    p1000 = ctx.load_instrument("p1000_single", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "legacy P1000 source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 1000)
    p1000.pick_up_tip(tips["A1"])
    p1000.aspirate(100, reservoir["A1"].bottom(1))
    p1000.dispense(100, plate["A1"].bottom(1))
    p1000.return_tip()
