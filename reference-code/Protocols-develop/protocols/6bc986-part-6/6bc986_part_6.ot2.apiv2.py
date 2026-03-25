import math
from opentrons import types

metadata = {
    'protocolName': '1. QIAGEN Prot. K-edit',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [clearance_aspirate, clearance_dispense, sample_count
     ] = get_values(  # noqa: F821
      'clearance_aspirate', 'clearance_dispense', 'sample_count')

    num_cols = math.ceil(sample_count / 8)
    tip_max = 50

    # p50 multi and tips
    tips20 = [ctx.load_labware("opentrons_96_tiprack_20ul", '4')]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'right', tip_racks=tips20)

    # Elution plate 1 on slot 6
    elution_plate1 = ctx.load_labware("thermo_96_wellplate_200ul", '6')

    # Elution plate 2 on slot 8
    elution_plate2 = ctx.load_labware("thermo_96_wellplate_200ul", '8')

    # to distribute and blow out with control over location within the well
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    def repeat_dispense(dist_vol, source, dest, max_asp=tip_max, disposal=0):
        for chunk in create_chunks(dest.columns()[
         :num_cols], math.floor((max_asp - disposal) / dist_vol)):
            if disposal > 0:
                p20m.aspirate(disposal, source)
            p20m.aspirate(dist_vol*len(chunk), source)
            for column in chunk:
                p20m.dispense(dist_vol, column[0].bottom(clearance_dispense))
            p20m.blow_out(source.move(types.Point(x=0, y=0, z=0)))

    # distribute 4 uL Prot K, blow out to bottom of reservoir, and repeat
    p20m.pick_up_tip()
    repeat_dispense(4, elution_plate1.wells_by_name()[
        'A1'].bottom(clearance_aspirate), elution_plate2, disposal=3,
        max_asp=15)
    p20m.drop_tip()
