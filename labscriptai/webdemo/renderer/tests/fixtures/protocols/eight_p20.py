"""One P20 multi-channel column transfer and a small destination mix."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: P20 multi-channel column",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_20ul", "1", "20 uL tips")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "2", "flat plate")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "3", "source reservoir")
    p20 = ctx.load_instrument("p20_multi_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "multi-channel source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 1000)

    # A multi-channel aspiration of 10 uL means 10 uL for each of 8 nozzles.
    # The single column destination therefore receives 8 x 10 uL total.
    p20.pick_up_tip(tips["A1"])
    p20.aspirate(10, reservoir["A1"].bottom(1))
    p20.dispense(10, plate["A1"].bottom(1))
    p20.mix(2, 5, plate["A1"].bottom(1))
    p20.drop_tip()
