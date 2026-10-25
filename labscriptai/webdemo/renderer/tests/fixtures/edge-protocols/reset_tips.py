from opentrons import protocol_api


requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext):
    tips = ctx.load_labware("opentrons_96_tiprack_20ul", 1)
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", 2)
    pipette = ctx.load_instrument("p20_single_gen2", "right", tip_racks=[tips])
    liquid = ctx.define_liquid("sample", "sample", "#ff0000")
    plate["A1"].load_liquid(liquid, 100)
    plate["A2"].load_liquid(liquid, 0)
    pipette.pick_up_tip()
    pipette.drop_tip()
    ctx.pause("replace tips")
    pipette.reset_tipracks()
    pipette.pick_up_tip()
    pipette.aspirate(10, plate["A1"])
    pipette.dispense(10, plate["A2"])
    pipette.drop_tip()
