from opentrons import protocol_api
metadata = {"protocolName": "Two cycles with explicit thermal holds"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}
def run(ctx: protocol_api.ProtocolContext):
    tc = ctx.load_module('thermocyclerModuleV1')
    tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tc.close_lid()
    tc.execute_profile(steps=[{'temperature': 42, 'hold_time_seconds': 1}, {'temperature': 25, 'hold_time_seconds': 2}], repetitions=2)
    tc.open_lid()
