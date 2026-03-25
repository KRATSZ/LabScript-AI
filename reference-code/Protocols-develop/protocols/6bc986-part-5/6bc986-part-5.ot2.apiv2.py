import math
from opentrons import types

metadata = {
    'protocolName': '2. Elution Buffer-edit',
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
    tips300 = [ctx.load_labware("opentrons_96_tiprack_300ul", '4')]
    p50m = ctx.load_instrument(
        "p50_multi", 'left', tip_racks=tips300)

    # thermo 96 well plate on slot 6
    thermo_plate = ctx.load_labware("thermo_96_wellplate_200ul", '6')

    # aspir8 reservoir in slot 2
    elution_buffer = ctx.load_labware("aspir8_1_reservoir_taped", '2')

    # to distribute and blow out with control over location within the well
    def create_chunks(list_name, n):
        for i in range(0, len(list_name), n):
            yield list_name[i:i+n]

    def repeat_dispense(dist_vol, source, dest, max_asp=tip_max, disposal=0):
        # chunk size math.floor((max_asp - disposal) / dist_vol) for multi disp
        for chunk in create_chunks(dest.columns()[:num_cols], 1):
            if disposal > 0:
                p50m.aspirate(disposal, source)
            p50m.aspirate(dist_vol*len(chunk), source)
            for column in chunk:
                p50m.dispense(dist_vol, column[0].bottom(clearance_dispense))
            p50m.dispense(disposal, source.move(types.Point(x=0, y=0, z=0)))

    # distribute 20 ul elution buffer, blow out to bottom of reservoir, repeat
    p50m.pick_up_tip()
    repeat_dispense(20, elution_buffer.wells_by_name()[
     'A1'].bottom(clearance_aspirate), thermo_plate, disposal=10)
    p50m.drop_tip()
