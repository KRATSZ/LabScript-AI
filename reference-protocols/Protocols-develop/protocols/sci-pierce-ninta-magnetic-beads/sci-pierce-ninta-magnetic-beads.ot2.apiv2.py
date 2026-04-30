from opentrons.types import Point
metadata = {
    'protocolName': 'Pierce NiNTA Magnetic Beads Part 1',
    'author': 'Boren Lin <boren.lin@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')
    [asp_height, length_from_side, p300_mount] = [0.5, 2.5, 'left']

    total_cols = int(num_samples//8)
    r1 = int(num_samples % 8)
    if r1 != 0:
        total_cols = total_cols + 1

    ASP_COUNT = num_samples//5
    LEFTOVER = num_samples % 5

    #########################

    # load labware

    eql_res = ctx.load_labware(
     'nest_12_reservoir_15ml', '4', 'equilibration buffer')
    # wash_res = ctx.load_labware('nest_12_reservoir_15ml', '6', 'wash buffer')
    # eln_res= ctx.load_labware(
    # 'nest_12_reservoir_15ml', '2', 'elution buffer')

    bead_tube = ctx.load_labware(
     'opentrons_15_tuberack_nest_15ml_conical', '5', 'beads')

    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_rack = mag_mod.load_labware('nest_96_wellplate_2ml_deep')

    sample_plate = ctx.load_labware(
     'nest_96_wellplate_2ml_deep', '7', 'samples')
    # elution_plate = ctx.load_labware(
    # 'nest_96_wellplate_2ml_deep', '3', 'eluates')

    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['9', '10']]
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '8', 'waste')

    # load pipette
    pip300 = ctx.load_instrument(
     'p300_multi_gen2', p300_mount, tip_racks=[*tiprack])
    pip300_single = ctx.load_instrument(
     'p300_single_gen2', 'right', tip_racks=[*tiprack])

    # liquids
    eql = eql_res.wells()[:total_cols]
    # wash = wash_res.wells()[:total_cols]
    # eln = eln_res.wells()[:total_cols]

    beads = bead_tube.rows()[0][0]

    waste = waste_res.wells()[0]
    samples = sample_plate.rows()[0][:total_cols]
    working_cols = mag_rack.rows()[0][:total_cols]
    # final_cols = elution_plate.rows()[0][:total_cols]

    def add_equilibration(vol1):
        ctx.comment('\n\n\n~~~~~~~~ADDING EQUILIBRATION BUFFER~~~~~~~~\n')
        pip300.pick_up_tip()

        if vol1 > 250:
            vol1 = vol1/2
            for eql_wells, working_wells in zip(eql, working_cols):
                for _ in range(2):
                    pip300.aspirate(vol1, eql_wells)
                    pip300.dispense(vol1, working_wells.bottom(7.5))
            pip300.drop_tip()
        else:
            for eql_wells, working_wells in zip(eql, working_cols):
                pip300.aspirate(vol1, eql_wells)
                pip300.dispense(vol1, working_wells.bottom(7.5))
            pip300.drop_tip()

    def remove_supernatant(vol3):
        ctx.comment('\n\n\n~~~~~~~~REMOVING SUPERNATANT~~~~~~~~\n')
        pip300.pick_up_tip()
        pip300.flow_rate.aspirate = 45

        if vol3 > 250:
            vol3 = vol3/2
            for i, col in enumerate(working_cols):
                side = -1 if i % 2 == 0 else 1
                aspirate_loc = col.bottom(z=asp_height).move(
                            Point(x=(col.length/2-length_from_side)*side))
                for _ in range(2):
                    pip300.transfer(vol3,
                                    aspirate_loc,
                                    waste.bottom(z=25),
                                    new_tip='never',
                                    blow_out=True,
                                    blowout_location='destination well')
        else:
            for i, col in enumerate(working_cols):
                side = -1 if i % 2 == 0 else 1
                aspirate_loc = col.bottom(z=asp_height).move(
                            Point(x=(col.length/2-length_from_side)*side))
                pip300.transfer(vol3,
                                aspirate_loc,
                                waste.bottom(z=25),
                                new_tip='never',
                                blow_out=True,
                                blowout_location='destination well')

        pip300.flow_rate.aspirate = 92
        pip300.drop_tip()

    # protocol
    mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~MIXING BEADS~~~~~~~~\n')
    pip300_single.pick_up_tip()
    for i in range(total_cols):
        h = 5 + i * 3
        pip300_single.mix(5, 250, beads.bottom(z=h), rate=5)

    ctx.comment(
     '\n\n\n~~~~~~~~TRANSFERRING BEADS AND EQUILIBRATION BUFFER~~~~~~~~\n')
    for i in range(0, ASP_COUNT):
        pip300_single.mix(5, 250, beads.bottom(z=2), rate=5)
        pip300_single.aspirate(250, beads.bottom(z=1))
        for j in range(0, 5):
            beads_well = mag_rack.wells()[j+i*5]
            pip300_single.dispense(50, beads_well.bottom(z=10))
        pip300_single.touch_tip()
    if LEFTOVER != 0:
        pip300_single.mix(5, LEFTOVER*50, beads.bottom(z=2), rate=5)
        pip300_single.aspirate(LEFTOVER*50, beads.bottom(z=1))
        for j in range(0, LEFTOVER):
            beads_well = mag_rack.wells()[j+ASP_COUNT*5]
            pip300_single.dispense(50, beads_well.bottom(z=10))
        pip300_single.touch_tip()
    pip300_single.drop_tip()

    add_equilibration(450)

    ctx.comment('\n\n\n~~~~~~~~REMOVING ACCESS~~~~~~~~\n')
    mag_mod.engage(height_from_base=4.2)
    ctx.delay(minutes=2)
    remove_supernatant(520)
    mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~EQUILIBRATING BEADS~~~~~~~~\n')

    add_equilibration(500)
    pip300.pick_up_tip()
    for wells in working_cols:
        pip300.mix(10, 200, wells.bottom(z=2), rate=3)
    pip300.drop_tip()
    mag_mod.engage(height_from_base=4.2)
    ctx.delay(minutes=2)
    remove_supernatant(520)
    mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~TRANSFERRING SAMPLES~~~~~~~~\n')

    vol4 = 500
    for source, dest in zip(samples, working_cols):
        pip300.pick_up_tip()
        for _ in range(2):
            pip300.transfer(vol4/2,
                            source,
                            dest.bottom(z=15),
                            new_tip='never',
                            blow_out=True,
                            blowout_location='destination well')
        pip300.mix(10, 200, dest.bottom(z=2), rate=3)
        pip300.drop_tip()

    ctx.pause('30 min gentle shaking, room temp')
