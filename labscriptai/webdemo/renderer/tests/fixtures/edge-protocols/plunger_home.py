from opentrons import protocol_api


requirements = {"robotType": "OT-2", "apiLevel": "2.24"}


def run(ctx: protocol_api.ProtocolContext):
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", 2)
    pipette = ctx.load_instrument("p20_single_gen2", "right")
    pipette.move_to(plate["A1"].top(10))
    pipette.home_plunger()
    ctx.delay(seconds=1)
