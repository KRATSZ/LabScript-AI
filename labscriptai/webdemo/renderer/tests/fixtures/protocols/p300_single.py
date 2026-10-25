"""Legacy P300 single-channel transfer with a returned tip."""

from opentrons import protocol_api

metadata = {"protocolName": "OT-2 fixture: legacy P300 single"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "3", "destination plate")
    p300 = ctx.load_instrument("p300_single", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "legacy P300 source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 300)
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(100, reservoir["A1"].bottom(1))
    p300.dispense(100, plate["A1"].bottom(1))
    p300.return_tip()
