import math
from opentrons.protocol_api.labware import OutOfTipsError

metadata = {
    'protocolName': '''NEBNext Ultra II RNA Library Prep Kit for Illumina:
    E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads:
    Part-2 - cDNA Synthesis''',
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
    skip_mix1 = False
    skip_mix2 = False

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if not 8 <= sample_count <= 48:
        raise Exception('Number of samples must be 8-48.')

    # filter tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [7]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [6]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module with reagent plate at 4 degrees
    temp = ctx.load_module('Temperature Module', '1')
    reagent_plate = temp.load_labware(
     labware_tempmod, 'Reagent Plate at 4 Degrees C')
    [mix1] = [reagent_plate.columns_by_name()[name] for name in [
     '2']]
    temp.set_temperature(4)

    vol_water1 = 8
    vol_fs_enz = 2
    mix1[0].liq_vol = (vol_water1 + vol_fs_enz)*num_cols + deadvol_plate

    vol_ss_rxnbf = 8
    vol_ss_enz = 4
    vol_water2 = 48

    # 60 uL mix2 per input sample split between two columns
    mix2 = [reagent_plate.columns_by_name()[name] for name in ['3', '4']]
    for index, column in enumerate(mix2):
        if not index:
            num = num_cols if num_cols <= 3 else 3
        else:
            num = num_cols - 3 if num_cols > 3 else 0
        if num:
            column[0].liq_vol = (
             vol_ss_rxnbf + vol_ss_enz + vol_water2)*num + deadvol_plate + 5
        else:
            column[0].liq_vol = 0

    # fragmented and primed poly(A) RNA at 4 degrees
    temp2 = ctx.load_module('Temperature Module', '4')
    input_plate = temp2.load_labware(
     labware_tempmod2, 'Fragmented, Primed Poly(A) RNA at 4 Degrees C')
    temp2.set_temperature(4)

    # magnetic module
    mag = ctx.load_module('magnetic module gen2', '9')
    mag.disengage()

    # alert user to reagent volumes needed
    steps20 = 1
    steps200 = 1
    num_20 = math.ceil(steps20*num_cols*p20m.channels / 96)
    num_200 = math.ceil(steps200*num_cols*p300m.channels / 96)
    ctx.comment(
     """\nEnsure tips (20 uL tips - {0} boxes, 200 uL tips - {1} boxes)
     are present on deck\n""".format(num_20, num_200))
    ctx.comment("\nEnsure reagents in sufficient volume are present on deck\n")
    ctx.comment("""\n{0} fragmented, primed Poly(A) RNA samples (10 uL)
    in {1}\n""".format(sample_count, input_plate))
    for volume, reagent, location in zip(
     [math.ceil(mix1[0].liq_vol),
      [math.ceil(column[0].liq_vol) for column in mix2]],
     ['''water + first strand enzyme mix
     (for 8 uL water + 2 uL enzyme transfer)''',
      '''second strand reaction buffer + second strand enzyme mix + water
      (for 8 uL + 4 uL + 48 uL transfer)'''],
     [mix1, mix2]):
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

    ctx.comment("\nSTEP 1.3.1 - 1.3.3 - first strand reaction\n")

    if not skip_mix1:

        for column in input_plate.columns()[:num_cols]:

            pick_up_or_refill(p20m)
            p20m.transfer(
             10, mix1[0].bottom(1), column[0].bottom(1), mix_after=(10, 16),
             new_tip='never')
            p20m.drop_tip()

    ctx.pause("""\nRemove the RNA plate for off-deck incubation
    (25 C 10 min, 42 C 15 min, 70 C 15 min, cool to 4), return and resume\n""")

    ctx.comment("\nSTEP 1.4.1 - 1.4.3 - second strand reaction\n")

    if not skip_mix2:

        source = mix2[0][0]

        for index, column in enumerate(input_plate.columns()[:num_cols]):

            pick_up_or_refill(p300m)

            if index >= 3:
                source = mix2[1][0]

            source.liq_vol -= 60

            ht = liq_height(
             source, effective_diameter=0.8*source.diameter) - 3 if liq_height(
             source, effective_diameter=0.8*source.diameter) - 3 > 1 else 1

            # report tip height to log during testing
            ctx.comment(" tip height during aspiration {}".format(ht))

            p300m.aspirate(60, source.bottom(ht), rate=0.2)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(p300m, source)

            p300m.dispense(60, column[0].bottom(2))
            p300m.mix(10, 64)

            p300m.drop_tip()

    ctx.comment("""\nRemove the RNA plate for off-deck incubation (16 C 1 hour)
    then finished - proceed with part-3 bead cleanup\n""")
