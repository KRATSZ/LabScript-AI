"""One P20 transfer with a deliberate liquid/air-gap boundary."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: P20 single air gap and return",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_20ul", "1", "20 uL tips")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "2", "flat plate")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "3", "source reservoir")
    p20 = ctx.load_instrument("p20_single_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "P20 source water", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 100)

    # The 10 uL liquid plug is followed by a 2 uL air gap.  Dispensing 12 uL
    # therefore leaves 10 uL liquid in A1; the air is not liquid inventory.
    p20.pick_up_tip(tips["A1"])
    p20.aspirate(10, reservoir["A1"].bottom(1))
    p20.air_gap(2)
    p20.dispense(12, plate["A1"].bottom(1))
    p20.touch_tip(plate["A1"])
    p20.blow_out(plate["A1"].top())
    ctx.delay(seconds=2)
    p20.return_tip()
