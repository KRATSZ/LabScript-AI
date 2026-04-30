import math
from opentrons.protocol_api.labware import OutOfTipsError
from opentrons import types

metadata = {
    'protocolName': '''NEBNext Quarter Volume Library Prep Step 5:
    Size Selection''',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    # get parameter values from json above
    [size, sample_count, labware_plates, engage_height, engage_time, dry_time,
     offset_x, offset_x_resuspension] = get_values(  # noqa: F821
      'size', 'sample_count', 'labware_plates', 'engage_height',
      'engage_time', 'dry_time', 'offset_x', 'offset_x_resuspension')

    ctx.set_rail_lights(True)
    ctx.delay(seconds=10)

    if sample_count < 48 or sample_count > 96:
        raise Exception('\nNumber of samples must be 48-96\n')

    if size not in [270, 500, 700]:
        raise Exception('\nSize must be 270, 500 or 700 bp\n')

    # water and bead volumes are determined by fragment size
    vol_dict = {270: [0, 12.5, 6.25],
                500: [24, 22, 7],
                700: [0, 3.75, 2.5]}

    [volh2o, volbeads1, volbeads2] = [
     vol_dict[size][index] for index in [*range(3)]]

    # tips, p20 multi, p300 multi
    tips20 = [
     ctx.load_labware("opentrons_96_filtertiprack_20ul", str(
      slot)) for slot in [10]]
    tips300 = [
     ctx.load_labware("opentrons_96_filtertiprack_200ul", str(
      slot)) for slot in [2, 4, 7, 11]]
    p20m = ctx.load_instrument(
        "p20_multi_gen2", 'left', tip_racks=tips20)
    p300m = ctx.load_instrument(
        "p300_multi_gen2", 'right', tip_racks=tips300)

    num_cols = math.ceil(sample_count / 8)

    # temperature module empty
    ctx.load_module('Temperature Module', '1')

    mag = ctx.load_module('magnetic module gen2', '9')
    mag_plate = mag.load_labware(labware_plates, 'PCR Plate (96xA)')
    mag.disengage()

    reservoir = ctx.load_labware(
     'nest_12_reservoir_15ml', '5', '12-well Reservoir')
    [beads, water, te] = [
     reservoir.wells_by_name()[name] for name in ['A1', 'A11', 'A12']]
    deadvol_reservoir_1 = 1800

    etoh = ctx.load_labware(
     'agilent_1_reservoir_290ml', '6', '80 Percent Ethanol').wells()[0]
    deadvol_reservoir_2 = 10000

    waste = ctx.load_labware(
     'agilent_1_reservoir_290ml', '8', 'Waste Reservoir').wells()[0]

    size_plate = ctx.load_labware(labware_plates, '3', 'Size Plate')

    beads.liq_vol = num_cols*8*(volbeads1 + volbeads2) + deadvol_reservoir_1
    te.liq_vol = num_cols*8*12 + deadvol_reservoir_1
    water.liq_vol = num_cols*8*volh2o + deadvol_reservoir_1
    etoh.liq_vol = num_cols*8*200 + deadvol_reservoir_2

    # alert user to reagent volumes needed
    ctx.comment(
     "\n***\nEnsure reagents in sufficient volume are present on deck\n***\n")
    for volume, units, reagent, location in zip([round(
     beads.liq_vol / 1000, 1),
     math.ceil(te.liq_vol / 1000),
     math.ceil(water.liq_vol / 1000),
     math.ceil(etoh.liq_vol / 1000)],
     ['mL', 'mL', 'mL', 'mL'],
     ['beads', 'te', 'water', 'etoh'],
     [beads, te, water, etoh]):
        ctx.comment(
         "\n***\n{0} {1} {2} in {3}\n***\n".format(
          str(volume), units, reagent.upper(), location))

    # notify user to replenish tips
    def pick_up_or_refill(pip):
        try:
            pip.pick_up_tip()
        except OutOfTipsError:
            ctx.pause(
             """\n***\nPlease Refill the {} Tip Boxes
             and Empty the Tip Waste\n***\n""".format(pip))
            pip.reset_tipracks()
            pip.pick_up_tip()

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

    if volh2o:

        ctx.comment("\n***\nStep - add water to sample\n***\n")
        pick_up_or_refill(p300m)
        for column in mag_plate.columns()[:num_cols]:
            p300m.move_to(water.top())
            p300m.air_gap(20)
            p300m.aspirate(24, water)
            p300m.dispense(44, column[0].top(), rate=2)
            ctx.delay(seconds=0.5)
            p300m.blow_out()
        p300m.drop_tip()

    ctx.comment("\n***\nStep - add 1st beads to sample and mix\n***\n")

    for index, column in enumerate(mag_plate.columns()[:num_cols]):

        pip = p20m if volbeads1 <= 20 else p300m

        pick_up_or_refill(pip)

        ht_premix = liq_height(beads) if liq_height(beads) > 1 else 1

        # bead premix - aspirate 2 mm, dispense at top of liquid
        if not index % 2:    # sets frequency of premixing
            ctx.comment("\n***\nStep - pre-mixing beads\n***\n")
            if not p300m.has_tip:
                pick_up_or_refill(p300m)
            for rep in range(5):
                p300m.aspirate(
                 200, beads.bottom(2), rate=0.5)
                p300m.dispense(200, beads.bottom(ht_premix), rate=0.5)

        # aspirate beads
        pip.aspirate(
         volbeads1, beads.bottom(1), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(pip, beads)

        # reservoir tip touch
        pip.move_to(
         beads.top(-2).move(types.Point(x=beads.length / 2, y=0, z=0)))
        pip.move_to(beads.top())

        # dispense beads
        pip.dispense(volbeads1, column[0].bottom(2))

        # mix with 80 percent of total volume
        v = 0.8*(volbeads1 + volh2o + 15) if 0.8*(
         volbeads1 + volh2o + 15) <= pip.max_volume else pip.max_volume

        for rep in range(10):
            pip.aspirate(v, column[0].bottom(2))
            pip.dispense(v, column[0].bottom(2))

        # tip touch and blowout
        pip.move_to(
         column[0].top(-2).move(types.Point(
          x=column[0].diameter / 2, y=0, z=0)))
        pip.blow_out()
        pip.move_to(column[0].top())

        pip.drop_tip()

    if p300m.has_tip:
        p300m.drop_tip()

    ctx.comment("\n***\nStep - incubate 5 minutes\n***\n")

    ctx.delay(minutes=5)

    ctx.comment("\n***\nStep - engage magnets and wait\n***\n")

    mag.engage(height_from_base=engage_height)
    ctx.delay(minutes=engage_time)

    ctx.comment("\n***\nStep - transfer 1st supernatant to size plate\n***\n")

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)

        # take top liquid with tip at 4 mm and slow flow rate
        p300m.aspirate(70, column[0].bottom(4), rate=0.33)

        # take remaining with tip at 1 mm and offset_x mm to side
        p300m.aspirate(
         70, column[0].bottom(1).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)

        p300m.dispense(140, size_plate.columns()[index][0])

        p300m.drop_tip()

    mag.disengage()

    ctx.pause(
     "\n***\nMove size plate (slot 3) to the magnetic module. Resume\n***\n")

    ctx.comment("\n***\nStep - add 2nd beads to sample and mix\n***\n")

    pick_up_or_refill(p300m)

    for index, column in enumerate(mag_plate.columns()[:num_cols]):

        pick_up_or_refill(p20m)

        ht_premix = liq_height(beads) if liq_height(beads) > 1 else 1

        # bead premix - aspirate 2 mm, dispense at top of liquid
        if not index % 2:    # sets frequency of premixing
            ctx.comment("\n***\nStep - pre-mixing beads\n***\n")
            for rep in range(5):
                p300m.aspirate(
                 200, beads.bottom(2), rate=0.5)
                p300m.dispense(200, beads.bottom(ht_premix), rate=0.5)

        # aspirate beads
        p20m.aspirate(
         volbeads2, beads.bottom(1), rate=0.5)
        ctx.delay(seconds=1)
        slow_tip_withdrawal(p20m, beads)

        # reservoir tip touch
        p20m.move_to(
         beads.top(-2).move(types.Point(x=beads.length / 2, y=0, z=0)))
        p20m.move_to(beads.top())

        # dispense beads
        p20m.dispense(volbeads2, column[0].bottom(2))

        # mix
        for rep in range(10):
            p20m.aspirate(20, column[0].bottom(2))
            p20m.dispense(20, column[0].bottom(2))

        # tip touch and blowout
        p20m.move_to(
         column[0].top(-2).move(types.Point(
          x=column[0].diameter / 2, y=0, z=0)))
        p20m.blow_out()
        p20m.move_to(column[0].top())

        p20m.drop_tip()

    if p300m.has_tip:
        p300m.drop_tip()

    ctx.comment("\n***\nStep - incubate 5 minutes\n***\n")

    ctx.delay(minutes=5)

    ctx.comment("\n***\nStep - engage magnets and wait\n***\n")

    mag.engage(height_from_base=engage_height)
    ctx.delay(minutes=engage_time)

    ctx.comment("\n***\nStep - discard supernatant\n***\n")

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p300m)

        # pre air gap
        p300m.move_to(column[0].top())
        p300m.air_gap(20)

        # take most liquid with tip at 4 mm and slow flow rate
        p300m.aspirate(90, column[0].bottom(4), rate=0.33)

        # take remaining with tip at 1 mm and offset_x mm to side
        p300m.aspirate(
         90, column[0].bottom(1).move(types.Point(
          x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0)), rate=0.33)

        # top dispense liquid plus air at fast flow rate
        p300m.dispense(200, waste.top(), rate=2)

        # delayed blow out
        ctx.delay(seconds=1)
        p300m.blow_out()

        p300m.drop_tip()

    ctx.comment("\n***\nStep - wash twice with 80 percent ethanol\n***\n")

    for repeat in range(2):

        pick_up_or_refill(p300m)
        for column in mag_plate.columns()[:num_cols]:

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
            p300m.blow_out()

            # post-dispense air gap to avoid drips
            p300m.air_gap(20)

        p300m.drop_tip()

        ctx.delay(seconds=30)

        # remove sup
        for index, column in enumerate(mag_plate.columns()[:num_cols]):

            pick_up_or_refill(p300m)

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
            p300m.blow_out()

            # post-dispense air gap to avoid drips
            p300m.air_gap(20)

            # to improve completeness of removal
            if repeat:
                p300m.move_to(column[0].top())
                for clearance in [0.7, 0.4, 0.2, 0]:
                    loc = column[0].bottom(clearance).move(types.Point(
                       x={True: -1}.get(not index % 2, 1)*offset_x, y=0, z=0))
                    p300m.aspirate(25, loc)

            p300m.drop_tip()

    ctx.comment("\n***\nStep - wait for beads to dry\n***\n")

    ctx.delay(minutes=dry_time)

    ctx.comment("\n***\nStep - resuspend beads in 1x TE\n***\n")

    mag.disengage()

    for index, column in enumerate(mag_plate.columns()[:num_cols]):
        pick_up_or_refill(p20m)
        p20m.aspirate(15, te.bottom(1))

        # location targeting bead pellet for resuspension
        loc = column[0].bottom(1).move(types.Point(
          x={True: 1}.get(not index % 2, -1)*offset_x_resuspension, y=0, z=0))

        p20m.dispense(16, loc, rate=3)

        # mix with dispenses targeting bead pellet
        for rep in range(10):
            p20m.aspirate(12, column[0].bottom(1))
            rt = 3 if rep < 9 else 0.5
            p20m.dispense(12, loc, rate=rt)

            # wait, depart slowly, tip touch and blowout after final mix
            if rep == 9:
                ctx.delay(seconds=1)
                slow_tip_withdrawal(p20m, column[0])
                p20m.move_to(
                 column[0].top(-2).move(types.Point(
                  x=column[0].diameter / 2, y=0, z=0)))
                p20m.blow_out()
                p20m.move_to(column[0].top())

        p20m.drop_tip()

    ctx.comment("\n***\nStep - incubate 2 minutes\n***\n")

    ctx.delay(minutes=2)

    ctx.comment("\n***\nStep - engage magnets and wait\n***\n")

    mag.engage(height_from_base=engage_height)
    ctx.delay(minutes=engage_time)

    mag.disengage()

    ctx.comment("\n***\nFinished\n***\n")
