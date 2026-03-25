from opentrons.types import Point

metadata = {
    'protocolName': 'Post RC-PCR Pooling of Nimagen SARS CoV-2 Library Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [step1, step2, quad1_exclude_cols, quad2_exclude_cols, quad3_exclude_cols,
        quad4_exclude_cols, m20_mount,
        p300_mount, donor_384_type, trans_vol1,
        step1_mix_vol, delay_after_asp, delay_after_disp,
        disp_speed, height_after_disp, stage2_asp_speed,
        stage2_disp_speed, stage1_dispense_height, stage2_dispense_height,
        stage2_height_after_disp] = get_values(  # noqa: F821
        "step1", "step2", "quad1_exclude_cols", "quad2_exclude_cols",
        "quad3_exclude_cols",
        "quad4_exclude_cols", "m20_mount", "p300_mount", "donor_384_type",
        "trans_vol1", "step1_mix_vol", "delay_after_asp",
        "delay_after_disp", "disp_speed", "height_after_disp",
        "stage2_asp_speed", "stage2_disp_speed", "stage1_dispense_height",
        "stage2_dispense_height", "stage2_height_after_disp")

    # Load Labware
    donor_384_plate = ctx.load_labware(donor_384_type, 1)
    recipient_96_plate = ctx.load_labware(
        'eppendorftwin.tec_96_wellplate_150ul', 2)
    tiprack_20ul = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                    for slot in [4, 5, 6, 7]]
    tiprack_200ul = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                     for slot in [8]]
    tuberack = ctx.load_labware(
            'opentrons_24_aluminumblock_nest_1.5ml_snapcap', 3)['A1']
    empty_racks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                   for slot in [9, 10, 11]]

    # Load Pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=tiprack_20ul)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tiprack_200ul)

    # Helper Functions

    switch = True
    drop_count = 0
    # number of tips trash will accommodate before prompting user to empty
    drop_threshold = 192

    def _drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        # pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count >= drop_threshold:
            pip.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            drop_count = 0
        return drop_loc

    def preWet(pipette, volume, location):
        for _ in range(1):
            pipette.aspirate(volume, location)
            pipette.dispense(volume, location)

    def excludeQuadCols(excludedCols, quadList):
        quad_exclude_cols = []
        if excludedCols != "":
            quad_exclude_cols = [int(i)-1 for i in excludedCols.split(",")]
            quad_dests = [col for i, col in enumerate(quadList) if i
                          not in quad_exclude_cols]
            return quad_dests
        else:
            quad_dests = [col for i, col in enumerate(quadList) if i
                          not in quad_exclude_cols]
            return quad_dests

    empty_racks_wells = [row for rack in empty_racks for row in rack.rows()[0]]

    def drop_loc(pip):
        nonlocal empty_racks_wells
        if len(empty_racks_wells) == 0:
            return _drop(pip)
        empty_slot = empty_racks_wells[0]
        empty_racks_wells.pop(0)
        return empty_slot

    def change_flow_rates(pip, asp_speed, disp_speed):
        pip.flow_rate.aspirate = asp_speed
        pip.flow_rate.dispense = disp_speed

    def reset_flow_rates(pip):
        if pip.name == 'p20_multi_gen2':
            pip.flow_rate.aspirate = 7.6
            pip.flow_rate.dispense = 7.6
        else:
            pip.flow_rate.aspirate = 92.86
            pip.flow_rate.dispense = 92.86

    def slow_tip_withdrawal(current_pipette, well_location, to_center=False):
        if current_pipette.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        ctx.max_speeds[axis] = 10
        if to_center is False:
            current_pipette.move_to(well_location.top())
        else:
            current_pipette.move_to(well_location.center())
        ctx.max_speeds[axis] = None

    # Get wells by quadrant
    quad1 = [col for col in donor_384_plate.rows()[0][::2]]
    quad2 = [col for col in donor_384_plate.rows()[0][1::2]]
    quad3 = [col for col in donor_384_plate.rows()[1][::2]]
    quad4 = [col for col in donor_384_plate.rows()[1][1::2]]

    quad1_dests = excludeQuadCols(quad1_exclude_cols, quad1)
    quad2_dests = excludeQuadCols(quad2_exclude_cols, quad2)
    quad3_dests = excludeQuadCols(quad3_exclude_cols, quad3)
    quad4_dests = excludeQuadCols(quad4_exclude_cols, quad4)

    # Step 1
    if step1 == "True":
        m20.flow_rate.dispense = disp_speed
        for quad in [quad1_dests, quad2_dests, quad3_dests, quad4_dests]:
            for col in quad:
                m20.pick_up_tip()
                ctx.comment('Pre-Wetting the tip')
                preWet(m20, trans_vol1, col)
                ctx.comment('Mixing before transfer to recepient plate.')
                m20.mix(3, step1_mix_vol, col)
                ctx.comment('Starting transfer to recipient plate.')
                m20.aspirate(trans_vol1, col)
                slow_tip_withdrawal(m20, col)
                ctx.delay(seconds=delay_after_asp, msg=f'''{delay_after_asp}
                          second delay after aspirating.''')
                m20.dispense(trans_vol1, recipient_96_plate['A1'].bottom(
                             stage1_dispense_height))
                m20.move_to(recipient_96_plate['A1'].bottom(height_after_disp))
                ctx.delay(seconds=delay_after_disp, msg=f'''{delay_after_disp}
                          second delay after dispensing.''')
                slow_tip_withdrawal(m20, recipient_96_plate['A1'])
                m20.air_gap(10)
                m20.drop_tip(drop_loc(m20))

    # Step 2
    if step2 == "True":
        # Calculate max volume per well
        source_wells = recipient_96_plate.columns()[0]

        for source in source_wells:
            max_well_vol = (len(quad1_dests) + len(quad2_dests) +
                            len(quad3_dests) + len(quad4_dests)) * trans_vol1
            ctx.comment(f'The max well volume is {max_well_vol}')
            p300.pick_up_tip()
            change_flow_rates(p300, stage2_asp_speed, stage2_disp_speed)
            mix_vol = 200 if max_well_vol*0.75 > 200 else max_well_vol*0.75
            p300.mix(3, mix_vol, source)
            while max_well_vol > 200:
                p300.aspirate(200, source)
                slow_tip_withdrawal(p300, source)
                p300.dispense(200, tuberack.bottom(stage2_dispense_height))
                p300.move_to(tuberack.bottom(stage2_height_after_disp))
                ctx.delay(seconds=delay_after_disp, msg=f'''{delay_after_disp}
                          second delay after dispensing.''')
                slow_tip_withdrawal(p300, tuberack)
                max_well_vol -= 200
            p300.aspirate(max_well_vol, source)
            slow_tip_withdrawal(p300, source)
            p300.dispense(max_well_vol,
                          tuberack.bottom(stage2_dispense_height))
            p300.move_to(tuberack.bottom(stage2_height_after_disp))
            ctx.delay(seconds=delay_after_disp, msg=f'''{delay_after_disp}
                          second delay after dispensing.''')
            slow_tip_withdrawal(p300, tuberack)
            reset_flow_rates(p300)
            p300.air_gap(20)
            p300.drop_tip()
