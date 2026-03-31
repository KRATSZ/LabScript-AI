import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''NEBNext Ultra II RNA Library Prep Kit for Illumina:
    E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads:
    Part-4 - End Prep and Adapter Ligation''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_tempmod, labware_tempmod2, labware_magneticmodule,
     deadvol_plate] = get_values(  # noqa: F821
      'sample_count', 'labware_tempmod', 'labware_tempmod2',
      'labware_magneticmodule', 'deadvol_plate')

    # for testing
    skip_epmix = False
    skip_adapter = False
    skip_mmenh = False
    skip_user = False

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if not 8 <= sample_count <= 48:
        raise Exception('Number of samples must be 8-48.')

    # filter tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [5, 7]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [6]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module with cDNA at 4 degrees
    temp = ctx.load_module('Temperature Module', '1')
    input_plate = temp.load_labware(
     labware_tempmod, 'cDNA at 4 Degrees C')
    temp.set_temperature(4)

    # temperature module with reagent plate at 4 degrees
    temp2 = ctx.load_module('Temperature Module', '4')
    reagent_plate = temp2.load_labware(
     labware_tempmod2, 'Reagent Plate at 4 Degrees C')
    temp2.set_temperature(4)

    [ep_mix, adapter, user] = [
     reagent_plate.columns_by_name()[name] for name in ['5', '7', '10']]

    vol_ep_rxnbf = 7
    vol_ep_enz = 3
    ep_mix[0].liq_vol = (vol_ep_rxnbf + vol_ep_enz)*num_cols + deadvol_plate
    adapter[0].liq_vol = 2.5*num_cols + deadvol_plate
    user[0].liq_vol = 3*num_cols + deadvol_plate

    # 30 uL mastermix per input sample split between two columns
    mm_enh = [reagent_plate.columns_by_name()[name] for name in ['8', '9']]
    for index, column in enumerate(mm_enh):
        if not index:
            num = num_cols if num_cols <= 6 else 6
        else:
            num = num_cols - 6 if num_cols > 6 else 0
        if num:
            column[0].liq_vol = 31*num + deadvol_plate + 5
        else:
            column[0].liq_vol = 0

    # magnetic module empty
    mag = ctx.load_module('magnetic module gen2', '9')
    mag.disengage()

    # alert user to reagent volumes needed
    steps20 = 3
    num_20 = math.ceil(steps20*num_cols*p20m.channels / 96)
    num_200 = 1
    ctx.comment(
     """\nEnsure tips (20 uL tips - {0} boxes, 200 uL tips - {1} boxes)
     are present on deck\n""".format(num_20, num_200))
    ctx.comment("\nEnsure reagents in sufficient volume are present on deck\n")
    ctx.comment(
     "\n{0} double-stranded cDNA samples (50 uL) in {1}\n".format(
      sample_count, input_plate))
    for volume, reagent, location in zip(
     [math.ceil(ep_mix[0].liq_vol),
      math.ceil(adapter[0].liq_vol), math.ceil(user[0].liq_vol),
      [math.ceil(column[0].liq_vol) for column in mm_enh]],
     ['end prep mix (for 7 uL buffer + 3 uL enzyme transfer)', 'adapter',
      'user enzyme', 'ligation mastermix + enhancer'],
     [ep_mix, adapter, user, mm_enh]):
        ctx.comment(
         "\n{0} uL {1} in {2}\n".format(
          str(volume), reagent.upper(), location))

    # return liquid height in a well
    def liq_height(well, effective_diameter=None):
        if well.diameter:
            if effective_diameter:
                radius = effective_diameter / 2
            else:
                radius = well.diameter / 2
            csa = math.pi*(radius**2)
        else:
            csa = well.length*well.width
        return well.liq_vol / csa

    def slow_tip_withdrawal(pipette, well_location, to_center=False):
        if pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            pipette.move_to(well_location.top())
        else:
            pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # notify user to replenish tips
    def pick_up_or_refill(pip):
        try:
            pip.pick_up_tip()
        except OutOfTipsError:
            ctx.pause(
             """Please Refill the {} Tip Boxes
             and Empty the Tip Waste""".format(pip))
            pip.reset_tipracks()
            pip.pick_up_tip()

    ctx.comment("\nSTEP 1.6.1 - 1.6.2 - assemble end prep reaction\n")

    # add end prep mix

    if not skip_epmix:

        for column in input_plate.columns()[:num_cols]:
            pick_up_or_refill(p20m)
            p20m.aspirate(10, ep_mix[0].bottom(1))
            p20m.dispense(10, column[0].bottom(1))
            # mix well
            for rep in range(10):
                p20m.aspirate(20, column[0].bottom(1), rate=3)
                p20m.dispense(20, column[0].bottom(3), rate=3)
            p20m.drop_tip()

    ctx.comment("\nSTEP 1.6.3 - 1.6.4 - end prep reaction\n")

    ctx.pause("""\nRemove cDNA plate for off-deck incubation
    (lid 75, 20 degrees 30 min, 65 degrees 30 min, cool to 4 degrees).
    Return plate and resume\n""")

    ctx.comment("\nSTEP 1.7.2 - 1.7.3 - assemble adapter ligation\n")

    # add diluted adapter

    if not skip_adapter:

        p20m.transfer(
         2.5, adapter[0], [column[0] for column in input_plate.columns()[
          :num_cols]], new_tip='always')

    # add ligation mastermix + ligation enhancer

    if not skip_mmenh:

        source = mm_enh[0][0]
        for index, column in enumerate(input_plate.columns()[:num_cols]):

            if index >= 6:
                source = mm_enh[1][0]

            source.liq_vol -= 31

            ht = liq_height(
             source, effective_diameter=0.8*source.diameter) - 3 if liq_height(
             source, effective_diameter=0.8*source.diameter) - 3 > 1 else 1

            # report tip height to log during testing
            ctx.comment(" tip height during aspiration {}".format(ht))

            pick_up_or_refill(p300m)

            p300m.aspirate(31, source.bottom(ht), rate=0.2)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(p300m, source)

            p300m.dispense(31, column[0].bottom(2))
            ctx.delay(seconds=1)
            # mix well
            for rep in range(10):
                p300m.aspirate(80, column[0].bottom(1))
                p300m.dispense(80, column[0].bottom(4))
            p300m.blow_out(column[0].top())
            p300m.touch_tip(v_offset=-2)

            p300m.drop_tip()

    ctx.comment("\nSTEP 1.7.4 - ligation\n")

    ctx.pause("""\nRemove cDNA plate for off-deck incubation
    (20 degrees 15 min). Return plate and resume\n""")

    ctx.comment("\nSTEP 1.7.5 - add USER enzyme\n")

    if not skip_user:

        for column in input_plate.columns()[:num_cols]:
            pick_up_or_refill(p20m)
            p20m.aspirate(3, user[0].bottom(1))
            p20m.dispense(3, column[0].bottom(1))
            for rep in range(10):
                p20m.aspirate(20, column[0].bottom(1))
                p20m.dispense(20, column[0].bottom(5))
            p20m.drop_tip()

    ctx.comment("""\nfinished - Remove cDNA plate for off-deck incubation
    (lid 45, 37 degrees 15 min) and proceed with part-5
    bead cleanup of ligation reaction\n""")
