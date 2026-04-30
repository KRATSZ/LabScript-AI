import math
from opentrons import types

metadata = {
    'protocolName': 'Apostle Sample Lysis 4',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [clearance_aspirate, clearance_dispense, sample_count
     ] = get_values(  # noqa: F821
      'clearance_aspirate', 'clearance_dispense', 'sample_count')

    num_cols = math.ceil(sample_count / 8)

    # p50 multi and tips
    tips300 = [ctx.load_labware("opentrons_96_tiprack_300ul", '4')]
    p50m = ctx.load_instrument(
        "p50_multi", 'left', tip_racks=tips300)

    # 96 deep well plate on slot 8
    deep_well_plate = ctx.load_labware("nest_96_wellplate_2ml_deep", '8')

    # aspir8 reservoir in slot 2
    reservoir = ctx.load_labware("aspir8_1_reservoir_taped", '2')

    # dispense and blow out 10 ul sample lysis buffer to v-bottom deep wells
    for column in deep_well_plate.columns()[:num_cols]:
        p50m.pick_up_tip()
        p50m.aspirate(
         10, reservoir.wells_by_name()['A1'].bottom(clearance_aspirate))
        p50m.move_to(column[0].bottom(clearance_dispense))
        p50m.move_to(column[0].bottom(
         clearance_dispense).move(types.Point(x=-1, y=0, z=1)))
        p50m.dispense(10)
        p50m.blow_out()
        p50m.drop_tip()
