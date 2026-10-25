from opentrons import protocol_api


requirements = {"robotType": "OT-2", "apiLevel": "2.20"}


def run(ctx: protocol_api.ProtocolContext):
    tips = ctx.load_labware("opentrons_96_tiprack_20ul", 1)
    tubes = ctx.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 2)
    plate = ctx.load_labware("nest_96_wellplate_200ul_flat", 3)
    pipette = ctx.load_instrument("p20_single_gen2", "right", tip_racks=[tips])
    liquid = ctx.define_liquid("sample", "sample", "#ff0000")
    tubes["A3"].load_liquid(liquid, 100)
    plate["A1"].load_liquid(liquid, 0)
    pipette.pick_up_tip()
    pipette.aspirate(10, tubes["A3"])
    pipette.air_gap(2, height=1)
    pipette.dispense(2, plate["A1"])
    pipette.return_tip()
