from opentrons import protocol_api


requirements = {"robotType": "OT-2", "apiLevel": "2.24"}


def run(ctx: protocol_api.ProtocolContext):
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", 2)
    ctx.move_labware(plate, 3, use_gripper=False)
    ctx.delay(seconds=1)
