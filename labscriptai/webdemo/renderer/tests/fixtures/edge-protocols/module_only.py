from opentrons import protocol_api
metadata = {"protocolName": "Module only, explicit hold"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}
def run(ctx: protocol_api.ProtocolContext):
    tc = ctx.load_module('thermocyclerModuleV1')
    tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tc.open_lid()
    tc.close_lid()
    tc.set_block_temperature(37, hold_time_seconds=2)
    tc.open_lid()
