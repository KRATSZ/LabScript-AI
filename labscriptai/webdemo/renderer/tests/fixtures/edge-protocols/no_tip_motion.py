from opentrons import protocol_api
metadata = {"protocolName": "Unloaded nozzle positioning"}
requirements = {"robotType": "OT-2", "apiLevel": "2.20"}
def run(ctx: protocol_api.ProtocolContext):
    plate = ctx.load_labware('nest_96_wellplate_200ul_flat', 2)
    pipette = ctx.load_instrument('p300_single_gen2', 'left')
    pipette.move_to(plate['A1'].top(10))
    ctx.delay(seconds=1)
    pipette.move_to(plate['H12'].top(10))
