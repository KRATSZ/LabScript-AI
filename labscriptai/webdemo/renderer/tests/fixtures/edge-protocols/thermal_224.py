from opentrons import protocol_api


requirements = {"robotType": "OT-2", "apiLevel": "2.24"}


def run(ctx: protocol_api.ProtocolContext):
    thermocycler = ctx.load_module("thermocyclerModuleV1")
    thermocycler.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    thermocycler.open_lid()
    thermocycler.close_lid()
    thermocycler.set_block_temperature(37, hold_time_seconds=2)
    thermocycler.open_lid()
