"""Open-lid transfer followed by a one-second 37 C block hold."""

from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 fixture: thermocycler transfer and hold",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext) -> None:
    tips = ctx.load_labware("opentrons_96_tiprack_300ul", "1", "300 uL tips")
    reservoir = ctx.load_labware("nest_12_reservoir_15ml", "2", "source reservoir")
    thermocycler = ctx.load_module("thermocyclerModuleV1", "7")
    plate = thermocycler.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", "PCR plate"
    )
    p300 = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[tips])

    water = ctx.define_liquid("Water", "thermocycler source", "#4EA5D9")
    reservoir["A1"].load_liquid(water, 500)

    thermocycler.open_lid()
    p300.pick_up_tip(tips["A1"])
    p300.aspirate(25, reservoir["A1"].bottom(1))
    p300.dispense(25, plate["A1"].bottom(1))
    thermocycler.close_lid()
    thermocycler.set_block_temperature(37, hold_time_seconds=1)
    thermocycler.open_lid()
    p300.drop_tip()
