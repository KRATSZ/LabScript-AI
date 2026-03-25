import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''NEBNext Ultra II RNA Library Prep Kit for Illumina:
    E7770S Section 1 with Poly(A) Isolation using Oligo-dT Beads:
    Part-1 - Poly(A) RNA Isolation, Fragmentation and Priming''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_tempmod, labware_tempmod2, labware_magneticmodule,
     labware_reservoir, deadvol_reservoir, deadvol_plate,
     clearance_beadresuspension, clearance_reservoir, height_engage,
     time_engage, offset_x] = get_values(  # noqa: F821
      'sample_count', 'labware_tempmod', 'labware_tempmod2',
      'labware_magneticmodule', 'labware_reservoir', 'deadvol_reservoir',
      'deadvol_plate', 'clearance_reservoir', 'clearance_beadresuspension',
      'height_engage', 'time_engage', 'offset_x')

    # for testing
    skip_mixbeadsandrna = False
    skip_beadmix = False
    skip_supremoval = False
    skip_washes = False
    skip_1stelution = False
    skip_rebinding = False
    skip_supremoval2 = False
    skip_washbuffer = False
    skip_washremoval = False
    skip_2ndelution = False

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if not 8 <= sample_count <= 48:
        raise Exception('Number of samples must be 8-48.')

    # filter tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [8]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [6, 7, 10, 11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module with reagent plate at 4 degrees
    temp = ctx.load_module('Temperature Module', '1')
    reagent_plate = temp.load_labware(
     labware_tempmod, 'Reagent Plate at 4 Degrees C')
    temp.set_temperature(4)
    [fs_rxnbf_rprimer_2x] = [
     reagent_plate.columns_by_name()[name] for name in ['1']]
    bindingbf2x = [
     reagent_plate.columns_by_name()[name] for name in ['2', '3']]

    # binding buffer 2X 50 uL per sample
    for index, column in enumerate(bindingbf2x):
        if not index:
            num = num_cols if num_cols <= 3 else 3
        else:
            num = num_cols - 3 if num_cols > 3 else 0
        if num:
            column[0].liq_vol = 50*num + deadvol_plate
        else:
            column[0].liq_vol = 0

    # first strand reaction buffer random primer 2X 11.5 uL per sample
    fs_rxnbf_rprimer_2x[0].liq_vol = 11.5*num_cols + deadvol_plate

    # temperature module with output plate at 4 degrees
    temp2 = ctx.load_module('Temperature Module', '4')
    output_plate = temp2.load_labware(
     labware_tempmod2, 'Output Plate at 4 Degrees C')
    temp2.set_temperature(4)

    # magnetic module with RNA plate
    mag = ctx.load_module('magnetic module gen2', '9')
    mag_plate = mag.load_labware(
     labware_magneticmodule,
     'Magnetic Module Plate - 300 uL PCR Plate + Adapter')
    mag.disengage()

    # reagent reservoir
    reagent_reservoir = ctx.load_labware(
     labware_reservoir, '2', 'Reagent Reservoir')
    [tris] = [
     reagent_reservoir.wells_by_name()[well] for well in ['A4']]

    # wash buffer 180 uL per sample - for three washes
    washbf = [
     reagent_reservoir.wells_by_name()[well] for well in ['A6', 'A7', 'A8']]
    for well in washbf:
        well.liq_vol = 180*num_cols*p300m.channels + deadvol_reservoir

    waste = [reagent_reservoir.wells_by_name()[well] for well in [
     'A9', 'A10', 'A11', 'A12']]

    # tris - 50 uL per sample
    tris.liq_vol = 50*num_cols*p300m.channels + deadvol_reservoir

    # alert user to reagent volumes needed
    steps20 = 2
    steps200 = 14
    num_20 = math.ceil(steps20*num_cols*p20m.channels / 96)
    num_200 = math.ceil(
     steps200*num_cols*p300m.channels / 96) if math.ceil(
     steps200*num_cols*p300m.channels / 96) <= 4 else 4
    ctx.comment(
     """\nEnsure tips (20 uL tips - {0} boxes, 200 uL tips - {1} boxes)
     are present on deck\n""".format(num_20, num_200))
    ctx.comment(
     "\nEnsure output plate is placed on the temperature module in slot 4\n")
    ctx.comment("\nEnsure reagents in sufficient volume are present on deck\n")
    ctx.comment(
     "\n{0} total RNA samples (50 uL) + 50 uL oligo-dT beads in {1}\n".format(
      sample_count, mag_plate))
    for volume, reagent, location in zip(
     [[math.ceil(well.liq_vol) for well in washbf],
      math.ceil(fs_rxnbf_rprimer_2x[0].liq_vol),
      math.ceil(tris.liq_vol),
      [math.ceil(column[0].liq_vol) for column in bindingbf2x]],
     ['wash buffer', 'first strand rxn buffer + random primer', '0.1 X TE',
      '2x binding buffer'],
     [washbf, fs_rxnbf_rprimer_2x, tris, bindingbf2x]):
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

    ctx.comment("\nSTEP 1.2.11 - mix 50 uL beads with input RNA samples\n")

    if not skip_mixbeadsandrna:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):

            pick_up_or_refill(p300m)

            # mixes

            reps = 15

            for rep in range(reps):

                p300m.aspirate(80, column[0].bottom(1))
                p300m.dispense(80, column[0].bottom(8))

                if rep == reps - 1:

                    # side touch with blowout
                    p300m.move_to(
                     column[0].top(-2).move(types.Point(
                      x=column[0].diameter / 2, y=0, z=0)))
                    p300m.blow_out()
                    p300m.move_to(column[0].top())

            p300m.drop_tip()

    ctx.comment("\nSTEP 1.2.12 and 1.2.13 - denaturation of RNA\n")

    ctx.pause("""\nRemove magnetic module plate for off-deck incubation
    (65 degrees 5 min, cool to 4 degrees C). Return and resume.\n""")

    ctx.comment("\nSTEP 1.2.14 - binding of poly A RNA\n")

    if not skip_beadmix:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):

            # mix
            pick_up_or_refill(p300m)

            reps = 15

            for rep in range(reps):

                p300m.aspirate(80, column[0].bottom(1))
                p300m.dispense(80, column[0].bottom(8))

                if rep == reps - 1:

                    # side touch with blowout after last mix
                    p300m.move_to(
                     column[0].top(-2).move(types.Point(
                      x=column[0].diameter / 2, y=0, z=0)))
                    p300m.blow_out()
                    p300m.move_to(column[0].top())
                    p300m.air_gap(20)

            p300m.drop_tip()

    ctx.delay(minutes=5)

    ctx.comment("\nSTEP 1.2.15 - engage magnets\n")
    mag.engage(height_from_base=height_engage)
    ctx.delay(minutes=time_engage)

    ctx.comment("\nSTEP 1.2.16 - remove supernatant\n")

    if not skip_supremoval:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            p300m.move_to(column[0].top())
            p300m.air_gap(20)
            p300m.aspirate(75, column[0].bottom(2), rate=0.33)
            p300m.aspirate(
             75, column[0].bottom(1).move(types.Point(
              x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)),
             rate=0.33)
            p300m.dispense(170, waste[-2].top(), rate=2)
            ctx.delay(seconds=1)
            p300m.blow_out()
            p300m.air_gap(20)
            p300m.drop_tip()

    ctx.comment(
     "\nSTEP 1.2.17 - 1.2.22 - disengage, wash, engage, discard, repeat\n")

    if not skip_washes:

        for repeat in range(2):
            mag.disengage()
            # add wash buffer to all bead pellets
            pick_up_or_refill(p300m)
            for index, column in enumerate(mag_plate.columns()[:num_cols]):
                washbf[repeat].liq_vol -= 180*p300m.channels
                ht = liq_height(
                 washbf[repeat]) - 3 if liq_height(
                 washbf[repeat]) - 3 > 1 else 1
                p300m.move_to(washbf[repeat].top())
                p300m.air_gap(20)
                p300m.aspirate(180, washbf[repeat].bottom(ht))
                p300m.dispense(200, column[0].top(), rate=2)
                ctx.delay(seconds=1)
                p300m.blow_out()

            # mix all
            for index, column in enumerate(mag_plate.columns()[:num_cols]):
                if index:
                    pick_up_or_refill(p300m)
                for rep in range(15):
                    clearance_mixdispense = 6 if (
                     rep % 2) else clearance_beadresuspension
                    offset_x_mixdispense = 2.5 if rep % 2 else offset_x
                    loc = column[0].bottom(clearance_mixdispense).move(
                     types.Point(x={True: 1}.get(
                      not index % 2, -1)*offset_x_mixdispense, y=0, z=0))
                    p300m.aspirate(144, column[0].bottom(1))
                    p300m.dispense(144, loc, rate=3)
                p300m.blow_out(column[0].top())
                p300m.touch_tip(radius=0.6, v_offset=-2, speed=10)
                p300m.drop_tip()

            # remove sup
            mag.engage(height_from_base=height_engage)
            ctx.delay(minutes=time_engage)
            for index, column in enumerate(mag_plate.columns()[:num_cols]):
                pick_up_or_refill(p300m)
                loc = column[0].bottom(1).move(types.Point(x={True: -1}.get(
                  not index % 2, 1)*offset_x, y=0, z=0))
                p300m.aspirate(130, column[0].bottom(4), rate=0.2)
                p300m.aspirate(50, loc, rate=0.2)
                p300m.air_gap(20)
                p300m.dispense(200, waste[repeat].top())
                ctx.delay(seconds=0.5)
                p300m.blow_out()
                p300m.drop_tip()

            # complete removal of last wash
            if repeat:
                for index, column in enumerate(mag_plate.columns()[:num_cols]):
                    pick_up_or_refill(p300m)
                    for clearance in [0.7, 0.4, 0.2, 0]:
                        loc = column[0].bottom(clearance).move(
                         types.Point(x={True: -1}.get(
                          not index % 2, 1)*offset_x, y=0, z=0))
                        p300m.aspirate(25, loc)
                    p300m.drop_tip()

    ctx.comment("\nSTEP 1.2.23 - add Tris and mix\n")

    mag.disengage()

    if not skip_1stelution:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            p300m.aspirate(50, tris.bottom(clearance_reservoir))
            loc = column[0].bottom(clearance_beadresuspension).move(
             types.Point(x={True: 1}.get(
              not index % 2, -1)*offset_x, y=0, z=0))
            p300m.dispense(50, loc, rate=3)
            for rep in range(15):
                clearance_mixdispense = 6 if (
                 rep % 2) else clearance_beadresuspension
                offset_x_mixdispense = 2.5 if rep % 2 else offset_x
                loc = column[0].bottom(clearance_mixdispense).move(
                 types.Point(x={True: 1}.get(
                  not index % 2, -1)*offset_x_mixdispense, y=0, z=0))
                p300m.aspirate(43, column[0].bottom(1))
                p300m.dispense(43, loc, rate=3)
            p300m.blow_out(column[0].top())
            p300m.touch_tip(radius=0.6, v_offset=-2, speed=10)
            p300m.drop_tip()

    ctx.comment("\nSTEP 1.2.24 and 1.2.25 - first elution\n")
    ctx.pause("""\nRemove magnetic module plate for off-deck incubation
    (lid 90, 80 degrees 2 min, cool to 25 degrees C). Return and resume.\n""")

    ctx.comment("\nSTEP 1.2.26 and 1.2.27 - rebind RNA to beads\n")

    if not skip_rebinding:

        source = bindingbf2x[0][0]

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            if index > 2:
                source = bindingbf2x[1][0]
            p300m.aspirate(50, source.bottom(1))
            p300m.dispense(50, column[0].bottom(2))
            for rep in range(6):
                p300m.aspirate(80, column[0].bottom(2))
                p300m.dispense(80, column[0].bottom(2))
                if rep == 5:
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p300m, column[0])
                    p300m.move_to(
                     column[0].top(-2).move(types.Point(
                      x=column[0].diameter / 2, y=0, z=0)))
                    p300m.blow_out()
                    p300m.move_to(column[0].top())
            p300m.drop_tip()

    ctx.delay(minutes=5)

    ctx.comment("\nSTEP 1.2.28 and 1.2.29 - engage magnets and discard sup\n")
    mag.engage(height_from_base=height_engage)
    ctx.delay(minutes=time_engage)

    if not skip_supremoval2:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            p300m.move_to(column[0].top())
            p300m.air_gap(20)
            p300m.aspirate(75, column[0].bottom(2), rate=0.33)
            p300m.aspirate(
             75, column[0].bottom(1).move(
              types.Point(x={True: -1}.get(
               not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)
            p300m.dispense(170, waste[-2].top(), rate=2)
            ctx.delay(seconds=1)
            p300m.blow_out()
            p300m.air_gap(20)
            p300m.drop_tip()

    ctx.comment(
     "\nSTEP 1.2.30 and 1.2.31 - disengage magnets and add wash buffer\n")

    mag.disengage()

    if not skip_washbuffer:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)

            washbf[-1].liq_vol -= 180*p300m.channels
            ht = liq_height(
             washbf[-1]) - 3 if liq_height(washbf[-1]) - 3 > 1 else 1

            p300m.aspirate(180, washbf[-1].bottom(ht))

            p300m.dispense(180, column[0].bottom(2))

            # mix
            for rep in range(15):
                clearance_mixdispense = 6 if (
                 rep % 2) else clearance_beadresuspension
                offset_x_mixdispense = 2.5 if rep % 2 else offset_x
                loc = column[0].bottom(clearance_mixdispense).move(
                 types.Point(x={True: 1}.get(
                  not index % 2, -1)*offset_x_mixdispense, y=0, z=0))
                p300m.aspirate(144, column[0].bottom(1))
                p300m.dispense(144, loc, rate=3)
            p300m.blow_out(column[0].top())
            p300m.touch_tip(radius=0.6, v_offset=-2, speed=10)
            p300m.drop_tip()

    ctx.comment("\nSTEP 1.2.32 - 1.2.35 - engage, discard sup, disengage\n")

    mag.engage(height_from_base=height_engage)
    ctx.delay(minutes=time_engage)

    if not skip_washremoval:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)

            p300m.move_to(column[0].top())
            p300m.air_gap(20)
            p300m.aspirate(110, column[0].bottom(4), rate=0.33)

            p300m.aspirate(
             70, column[0].bottom(1).move(
              types.Point(x={True: -1}.get(
               not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)
            p300m.dispense(200, waste[-1].top(), rate=2)
            ctx.delay(seconds=1)
            p300m.blow_out()

            p300m.drop_tip()

        # complete removal
        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p300m)
            for clearance in [0.7, 0.4, 0.2, 0]:
                loc = column[0].bottom(clearance).move(types.Point(
                 x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0))
                p300m.aspirate(25, loc)
            p300m.drop_tip()

    mag.disengage()

    ctx.comment(
     "\nSTEP 1.2.36 - elution in 1st strand rxn bf + random primer\n")

    if not skip_2ndelution:

        for index, column in enumerate(mag_plate.columns()[:num_cols]):
            pick_up_or_refill(p20m)
            p20m.aspirate(11.5, fs_rxnbf_rprimer_2x[0].bottom(1))
            loc = column[0].bottom(clearance_beadresuspension).move(
             types.Point(x={True: -1}.get(
              not index % 2, 1)*offset_x, y=0, z=0))
            p20m.dispense(11.5, loc)
            ctx.delay(seconds=1)
            slow_tip_withdrawal(p20m, column[0])
            p20m.move_to(
             column[0].top(-2).move(types.Point(
              x=column[0].diameter / 2, y=0, z=0)))
            p20m.blow_out()
            p20m.move_to(column[0].top())
            p20m.drop_tip()

    ctx.comment("\nSTEP 1.2.37 - fragmentation\n")
    ctx.pause("""\nRemove mag plate and vortex, then off-deck incubation
    (lid 105, 94 degrees 15 min, cool to 4 degrees -
    on ice ASAP upon 65 degrees). Quick spin. Return plate and resume.\n""")

    ctx.comment("\nSTEP 1.2.38 and 1.2.39 - collect eluate\n")

    mag.engage(height_from_base=height_engage)
    ctx.delay(minutes=2)

    if not skip_2ndelution:

        for index, column1, column2 in zip(
         [*range(12)][:num_cols],
         mag_plate.columns()[:num_cols],
         output_plate.columns()[:num_cols]):
            pick_up_or_refill(p20m)
            p20m.transfer(
             10, column1[0].bottom(0.5).move(
              types.Point(x={True: -1}.get(
               not index % 2, 1)*1.5, y=0, z=0)), column2[0], new_tip='never')
            p20m.drop_tip()

    mag.disengage()

    ctx.comment("""\nfinished - confirm 10 uL eluate volumes
    (manually adjust if necessary), proceed with part-2 cDNA synthesis\n""")
