# flake8: noqa
import math
from opentrons import types
from opentrons import protocol_api

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 2:
    Sample Cleanup for Covaris Samples''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.9'
}


def run(ctx):

    # get parameter values from json above
    [sample_count, labware_plates, x, y, engage_height, engage_time, dry_time, offset_x, offset_x_resuspension] = get_values(  # noqa: F821
      'sample_count', 'labware_plates', 'x', 'y', 'engage_height',
      'engage_time', 'dry_time', 'offset_x', 'offset_x_resuspension')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)
    if sample_count < 48 or sample_count > 96:
        raise Exception('Number of samples must be 48-96')
    if x < 30 or x > 50:
        raise Exception('Sample volume must be 30-50 uL')
    if y < 1 or y > 1.2:
        raise Exception('Bead ratio must be 1-1.2')


    # tips, p20 single, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [2, 3, 4, 7, 11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)
    num_batches = math.ceil(num_cols / 4)

    # temperature module at 4 C with reagent tubes
    ctx.load_module('Temperature Module', '1')

    mag = ctx.load_module('magnetic module gen2', '9')
    mag_plate = mag.load_labware(labware_plates, 'PCR Plate (96xA)')

    reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '5', '12-well Reservoir')
    [beads, te] = [reservoir.wells_by_name()[name] for name in ['A1', 'A12']]
    deadvol_reservoir_1 = 1800

    etoh = ctx.load_labware(
     'agilent_1_reservoir_290ml', '6', '80 Percent Ethanol').wells()[0]
    deadvol_reservoir_2 = 10000

    waste = ctx.load_labware(
     'agilent_1_reservoir_290ml', '8', 'Waste Reservoir').wells()[0]

    beads.liq_vol = num_cols*8*x*y + deadvol_reservoir_1
    te.liq_vol = num_cols*8*15 + deadvol_reservoir_1
    etoh.liq_vol = num_cols*8*240 + deadvol_reservoir_2

    # alert user to reagent volumes needed
    ctx.comment("Ensure reagents in sufficient volume are present on deck.")
    for volume, units, reagent, location in zip([round(
     beads.liq_vol / 1000, 1),
     math.ceil(te.liq_vol / 1000),
     math.ceil(etoh.liq_vol / 1000)],
     ['mL', 'mL', 'mL'],
     ['beads', 'te', 'etoh'],
     [beads, te, etoh]):
        ctx.comment(
         "{0} {1} {2} in {3}".format(
          str(volume), units, reagent.upper(), location))

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f"Replace empty tip rack for {pip}")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # return liquid height in a well
    def liq_height(well):
        if well.diameter is not None:
            radius = well.diameter / 2
            cse = math.pi*(radius**2)
        elif well.length is not None:
            cse = well.length*well.width
        else:
            cse = None
        if cse:
            return well.liq_vol / cse
        else:
            raise Exception("""Labware definition must
                supply well radius or well length and width.""")

    # apply speed limit to departing tip
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

    ctx.comment("Step - add beads and mix")

    # dispense volume is (sample volume * bead ratio)
    vol = x*y

    for index, column in enumerate(mag_plate.columns()[:num_cols]):

        # height of top of liquid for beads
        ht_premix = liq_height(beads) + 3 if liq_height(beads) + 3 > 1 else 1

        # bead premix - aspirate 2 mm, dispense at top of liquid
        pick_up(p300m)

        if not index % 2:    # sets frequency of premixing
            for rep in range(5):
                p300m.aspirate(
                 200, beads.bottom(2), rate=0.5)
                p300m.dispense(200, beads.bottom(ht_premix), rate=0.5)

        # increment bead volume downward for each aspiration
        beads.liq_vol -= vol*8

        # aspirate beads
        p300m.aspirate(
         vol, beads.bottom(1), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p300m, beads)

        # reservoir tip touch
        p300m.move_to(
         beads.top(-2).move(types.Point(x=beads.length / 2, y=0, z=0)))
        p300m.move_to(beads.top())

        # dispense beads
        p300m.dispense(vol, column[0].bottom(4))

        # mix with 80 percent of total volume
        v = 0.8*(vol + x)

        for rep in range(10):
            p300m.aspirate(v, column[0].bottom(3))
            p300m.dispense(v, column[0].bottom(3))

        # tip touch and blowout
        p300m.move_to(
         column[0].top(-2).move(types.Point(
          x=column[0].diameter / 2, y=0, z=0)))
        p300m.blow_out()
        p300m.move_to(column[0].top())

        p300m.drop_tip()

    ctx.comment("Step - incubate 5 minutes")

    ctx.delay(minutes=5)

    ctx.comment("Step - engage magnets and wait")

    mag.engage(height_from_base=engage_height)
    ctx.delay(minutes=engage_time)

    ctx.comment("Step - discard supernatant")

    col_ctr = num_cols

    for i, batch in enumerate(range(num_batches)):
        ctx.comment('\n\n poop \n')

        col_add = 4 if col_ctr >= 4 else col_ctr


        for index, column in enumerate(mag_plate.columns()[4*i:4*i+col_add]):
            pick_up(p300m)


            # pre air gap
            p300m.move_to(column[0].top())
            p300m.air_gap(20)

            # take most liquid with tip at 4 mm and slow flow rate
            p300m.aspirate(130, column[0].bottom(4), rate=0.33)

            # take remaining with tip at 1 mm and offset_x mm to side
            p300m.aspirate(
             50, column[0].bottom(1).move(types.Point(
              x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)

            # top dispense liquid plus air at fast flow rate
            p300m.dispense(200, waste.top(), rate=2)

            # delayed blow out
            ctx.delay(seconds=1)

            p300m.drop_tip()

        ctx.comment("Step - wash twice with 80 percent ethanol")

        for repeat in range(2):

            pick_up(p300m)
            for column in mag_plate.columns()[4*i:4*i+col_add]:

                # increment etoh volume downward for each aspiration
                etoh.liq_vol -= 960

                # height of top of etoh
                ht = liq_height(etoh) - 3 if liq_height(etoh) - 3 > 1 else 1

                # at ht mm - avoid overimmersion, avoid ridge in reservoir bottom
                p300m.aspirate(
                 120, etoh.bottom(ht).move(types.Point(x=4.5, y=0, z=0)))
                p300m.air_gap(20)  # post air gap

                # etoh top dispense with delayed blow out
                p300m.dispense(140, column[0].top())
                ctx.delay(seconds=0.5)

                # # post-dispense air gap to avoid drips
                # p300m.air_gap(20)

            p300m.drop_tip()

            ctx.delay(seconds=30)

            # remove sup
            for index, column in enumerate(mag_plate.columns()[4*i:4*i+col_add]):

                pick_up(p300m)

                # aspiration location offset to side to avoid bead pellet
                loc = column[0].bottom(1).move(types.Point(x={True: -1}.get(
                  not index % 2, 1)*offset_x, y=0, z=0))

                # take most liquid with tip at 4 mm, slow flow rate
                p300m.aspirate(100, column[0].bottom(4), rate=0.2)

                # take remaining at 1 mm, avoid beads, slow flow rate, post air gap
                p300m.aspirate(60, loc, rate=0.2)
                p300m.air_gap(20)

                # top dispense to waste with delayed blowout
                p300m.dispense(180, waste.top())
                ctx.delay(seconds=0.5)

                # post-dispense air gap to avoid drips
                p300m.air_gap(20)

                # to improve completeness of removal
                if repeat:

                    p300m.move_to(column[0].top())
                    p300m.aspirate(20, column[0], rate=0.05)
                    p300m.aspirate(20, column[0].bottom(z=0.5), rate=0.1)
                    p300m.aspirate(20, column[0].bottom(z=0.1), rate=0.1)
                    p300m.aspirate(20, column[0].bottom(z=0), rate=0.1)
                    p300m.aspirate(20, column[0].bottom(z=-0.4), rate=0.1)

                p300m.drop_tip()

        ctx.comment("Step - wait for beads to dry")

        ctx.delay(minutes=dry_time)

        ctx.comment("Step - resuspend beads in 1x TE")

        mag.disengage()

        for index, column in enumerate(mag_plate.columns()[4*i:4*i+col_add]):
            pick_up(p20m)
            p20m.aspirate(15, te.bottom(1))

            # location targeting bead pellet for resuspension
            loc = column[0].bottom(1).move(types.Point(
              x={True: 1}.get(not index % 2, -1)*offset_x_resuspension, y=0, z=column[0].depth/1.5))  # noqa:E501

            p20m.dispense(16, loc, rate=3)

            # mix with dispenses targeting bead pellet
            for rep in range(20):
                p20m.aspirate(15, column[0].bottom(1))
                rt = 3 if rep < 18 else 0.5
                p20m.dispense(15, loc, rate=rt)

                # wait, depart slowly, tip touch and blowout after final mix
                if rep == 19:
                    p20m.mix(15, 15, column[0], rate=1.5)
                    ctx.delay(seconds=1)
                    slow_tip_withdrawal(p20m, column[0])
                    p20m.move_to(
                     column[0].top(-2).move(types.Point(
                      x=column[0].diameter / 2, y=0, z=0)))
                    p20m.blow_out()
                    p20m.move_to(column[0].top())

            p20m.drop_tip()
        col_ctr -= col_add

    ctx.comment("Step - incubate 2 minutes")

    ctx.delay(minutes=2)

    ctx.comment("Step - engage magnets and wait")

    mag.engage(height_from_base=engage_height)
    ctx.delay(minutes=engage_time)

    ctx.comment("Finished")
