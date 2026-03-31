from opentrons.types import Point
metadata = {
    'protocolName': 'Pierce NiNTA Magnetic Beads Part 2',
    'author': 'Boren Lin <boren.lin@opentrons.com>',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')
    [asp_height, length_from_side, p300_mount] = [0.5, 2.5, 'left']
    ELUTE_TIMES = 2

    total_cols = int(num_samples//8)
    r1 = int(num_samples % 8)
    if r1 != 0:
        total_cols = total_cols + 1

    # load labware

    # eql_res= ctx.load_labware(
    # 'nest_12_reservoir_15ml', '4', 'equilibration stock')
    wash_res = ctx.load_labware('nest_12_reservoir_15ml', '4', 'wash buffer')
    eln_res = ctx.load_labware('nest_12_reservoir_15ml', '2', 'elution buffer')

    # bead_tube = ctx.load_labware(
    # 'opentrons_15_tuberack_nest_15ml_conical', '5', 'beads')

    mag_mod = ctx.load_module('magnetic module gen2', '1')
    mag_rack = mag_mod.load_labware('nest_96_wellplate_2ml_deep')

    # sample_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '7')
    elution_plate = ctx.load_labware(
     'nest_96_wellplate_2ml_deep', '3', 'eluates')

    # tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
    # for slot in ['9', '10']]
    tiprack = ctx.load_labware('opentrons_96_tiprack_300ul', '6')
    tiprack_wash = ctx.load_labware('opentrons_96_tiprack_300ul', '7')
    tiprack_eln = ctx.load_labware('opentrons_96_tiprack_300ul', '5')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '8', 'waste')

    # load pipette
    pip300 = ctx.load_instrument('p300_multi_gen2',
                                 p300_mount,
                                 tip_racks=[tiprack])

    # liquids
    # eql = eql_res.wells()[:total_cols]
    wash = wash_res.wells()[:total_cols]
    eln = eln_res.wells()[:total_cols]

    # beads = bead_res.wells()[0]
    # beads = bead_tube.wells()[0][0]

    waste = waste_res.wells()[0]
    # samples = sample_plate.rows()[0][:total_cols]
    working_cols = mag_rack.rows()[0][:total_cols]
    final_cols = elution_plate.rows()[0][:total_cols]

    def add_wash(vol2):
        pip300.pick_up_tip()
        if vol2 > 250:
            vol2 = vol2/2
            for wash_wells, working_wells in zip(wash, working_cols):
                for _ in range(2):
                    pip300.aspirate(vol2, wash_wells)
                    pip300.dispense(vol2, working_wells.bottom(7.5))
            pip300.drop_tip()
        else:
            for wash_wells, working_wells in zip(wash, working_cols):
                pip300.aspirate(vol2, wash_wells)
                pip300.dispense(vol2, working_wells.bottom(7.5))
                # x = x + 8
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
    ctx.pause('load sample plate')

    ctx.comment('\n\n\n~~~~~~~~REMOVING ACCESS~~~~~~~~\n')
    mag_mod.engage(height_from_base=4.2)
    ctx.delay(minutes=3)
    remove_supernatant(500)
    mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~TWO WASHES~~~~~~~~\n')
    for i in range(2):
        ctx.comment('\n\n\n~~~~~~~~ADDING WASH~~~~~~~~\n')
        add_wash(500)
        x = 0
        for wells in working_cols:
            pip300.pick_up_tip(tiprack_wash.well(x))
            pip300.mix(10, 200, wells.bottom(z=2), rate=3)
            pip300.return_tip()
            x = x + 8
        mag_mod.engage(height_from_base=4.2)
        ctx.delay(minutes=2)
        remove_supernatant(500)
        # if i == 1: remove_residue(20)
        mag_mod.disengage()

    ctx.comment('\n\n\n~~~~~~~~ELUTION~~~~~~~~\n')
    vol6 = 250
    for _ in range(ELUTE_TIMES):
        ctx.comment('\n\n\n~~~~~~~~ADDING ELUTION BUFFER~~~~~~~~\n')
        x = 0
        for eln_wells, working_wells in zip(eln, working_cols):
            pip300.pick_up_tip(tiprack_eln.well(x))
            pip300.aspirate(vol6, eln_wells)
            pip300.dispense(vol6, working_wells.bottom(z=15))
            pip300.mix(10, vol6, working_wells.bottom(z=2))
            pip300.return_tip()
            x = x + 8
        ctx.pause('10 min gentle shaking, room temp')

        ctx.comment('\n\n\n~~~~~~~~TRANSFERRING ELUTE TO CLEAN TUBE~~~~~~~~\n')
        mag_mod.engage(height_from_base=4.2)
        ctx.delay(minutes=2)
        y = 0
        for i, col in enumerate(working_cols):
            side = -1 if i % 2 == 0 else 1
            aspirate_loc = col.bottom(z=asp_height).move(
                        Point(x=(col.length/2-length_from_side)*side))
            pip300.pick_up_tip(tiprack_eln.well(y))
            pip300.aspirate(vol6, aspirate_loc)
            pip300.dispense(vol6, final_cols[i].bottom(z=10))
            pip300.blow_out()
            pip300.return_tip()
            y = y + 8

        mag_mod.disengage()
