"""P300 multi-channel transfer of one plate column with tip return."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: P300 multi-channel column transfer",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", "2", "source and destination")
    p300 = ctx.load_instrument("p300_multi_gen2", "right", tip_racks=[tips])

    sample = ctx.define_liquid("Sample", "100 uL in source column", "#E0533C")
    for well in plate.columns()[0]:
        well.load_liquid(sample, 100)

    # The multi-channel transfer withdraws 20 uL from each A1:H1 well and
    # deposits 20 uL into the corresponding A2:H2 well.
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(20, plate["A1"].bottom(1))
    p300.dispense(20, plate["A2"].bottom(1))
    p300.return_tip()
