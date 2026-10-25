from opentrons import protocol_api, types


requirements = {"robotType": "OT-2", "apiLevel": "2.24"}


def run(ctx: protocol_api.ProtocolContext):
    rack = ctx.load_labware("opentrons_96_tiprack_20ul", 1)
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", 2)
    pipette = ctx.load_instrument("p20_single_gen2", "right", tip_racks=[rack])
    liquid = ctx.define_liquid("sample", "sample", "#ff0000")
    plate["A1"].load_liquid(liquid, 100)
    pipette.pick_up_tip()
    pipette.aspirate(10, plate["A1"])
    pipette.move_to(types.Location(types.Point(200, 300, 100), None))
    pipette.dispense(10)
    pipette.return_tip()
