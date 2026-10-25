"""One-tip P1000 distribute with a separately accounted disposal reserve."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: P1000 distribute and disposal",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_1000ul", "1", "1000 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    plate = ctx.load_labware("corning_96_wellplate_360ul_flat", "3", "destination plate")
    p1000 = ctx.load_instrument("p1000_single_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "P1000 source water", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 1000)
    destinations = [plate[well] for well in ("A1", "A2", "A3")]

    # One tip delivers 100 uL to each destination.  distribute() reserves a
    # separate 10 uL disposal volume; it is not counted as delivered liquid.
    p1000.pick_up_tip(tips["A1"])
    p1000.distribute(
        100,
        reservoir["A1"].bottom(1),
        [well.bottom(1) for well in destinations],
        disposal_volume=10,
        new_tip="never",
    )
    p1000.blow_out(destinations[-1].top())
    p1000.drop_tip()
