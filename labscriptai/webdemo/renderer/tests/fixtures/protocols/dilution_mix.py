"""Two serial 50 uL links, with a fresh tip and mix at each destination."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: serial dilution and mix",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "2", "serial dilution plate")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "3", "diluent reservoir")
    p300 = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[tips])

    diluent = ctx.define_liquid("Diluent", "reservoir diluent", "#4EA5D9")
    sample = ctx.define_liquid("Sample", "50 uL starting sample", "#E0533C")
    reservoir["A1"].load_liquid(diluent, 500)
    for well_name in ("A1", "A2", "A3"):
        plate[well_name].load_liquid(sample, 50)

    # Link 1: 50 uL diluent into an already 50 uL A2, then mix 3 x 30 uL.
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(50, reservoir["A1"].bottom(1))
    p300.dispense(50, plate["A2"].bottom(1))
    p300.mix(3, 30, plate["A2"].bottom(1))
    p300.drop_tip()

    # Link 2: transfer 50 uL of the mixed A2 into an already 50 uL A3.
    p300.pick_up_tip(tips["A2"])
    p300.aspirate(50, plate["A2"].bottom(1))
    p300.dispense(50, plate["A3"].bottom(1))
    p300.mix(3, 30, plate["A3"].bottom(1))
    p300.drop_tip()
