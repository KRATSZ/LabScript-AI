# flake8: noqa

metadata = {
    'protocolName': 'Ribogreen Assay',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [csv_samp, plate_standard, diluent_buff_col,
        duplicate_plating, user_input_pause, m300_mount, p300_mount] = get_values(  # noqa: F821
        "csv_samp", "plate_standard", "diluent_buff_col",
            "duplicate_plating", "user_input_pause", "m300_mount", "p300_mount")

    # p300_mount = 'left'
    # m300_mount = 'right'
    # plate_standard = True
    # diluent_buff_col = 4
    # duplicate_plating = False
    # csv_samp = """


    #
    # source slot, source well, dest well
    # 7, A1, A1
    # 8, A1, A2
    # 7, A3, A3
    #
    # """
    #
    # user_input_pause = True

    def Transfer_With_TT(Pipette, Source, Destination, Vol, Dispense_Top):
        # Split transfer up to allow for more control over touch tip height
        ## p300.transfer(vol, matrix_buff, well, new_tip='never')

        # Loop is used if volume is more than pipette max
        current_vol = Vol
        while current_vol > Pipette.max_volume:
            # Aspirate max volume
            Pipette.aspirate(Pipette.max_volume, Source.bottom(z = 4))
            # Touch tip
            Pipette.move_to(Source.top(z = -3))
            Pipette.touch_tip(v_offset=1)

            # Dispense max volume
            if not Dispense_Top:
                Pipette.dispense(Pipette.max_volume, Destination.bottom(z = 3)) # With z offset
            else:
                Pipette.dispense(Pipette.max_volume, Destination.top())

            # Touch tip
            Pipette.move_to(Destination.top(z = -3))
            Pipette.touch_tip(v_offset=1)

            # Update current volume
            current_vol -= Pipette.max_volume

        # If volume to transfer is 0, do nothing
        if current_vol == 0:
            return()

        # If volume more than 0 but less than or equal to max

        # Aspirate volume
        Pipette.aspirate(current_vol, Source.bottom(z = 4))
        # Touch tip
        Pipette.move_to(Source.top(z = -3))
        Pipette.touch_tip(v_offset=1)

        # Dispense volume
        if not Dispense_Top:
            Pipette.dispense(current_vol, Destination.bottom(z = 3)) # With z offset
        else:
            Pipette.dispense(current_vol, Destination.top())
        # Touch tip
        Pipette.move_to(Destination.top(z = -3))
        Pipette.touch_tip(v_offset=1)


    # labware
    reservoir = ctx.load_labware('corning_12_reservoir', 2)
    try:
        heater_shaker = ctx.load_module('heaterShakerModuleV1', 6)
        heater_shaker.close_labware_latch()
        hs_plate = heater_shaker.load_labware('nunc_96_wellplate_400ul')
    except ValueError:
        hs_plate = ctx.load_labware('nunc_96_wellplate_400ul', 6)

    deep_plate = ctx.load_labware('pyramid_96_wellplate_2000ul', 4)
    tuberack_15 = ctx.load_labware('opentrons_15_tuberack_5000ul', 7)
    tuberack_24 = ctx.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 8)
    tuberack_24 = tuberack_24

    tips = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
            for slot in [1]]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    csv_lines = [[val.strip() for val in line.split(',')]
                 for line in csv_samp.splitlines()
                 if line.split(',')[0].strip()][1:]

    # mapping
    matrix_buff = reservoir.wells_by_name()['A1']

    triton = reservoir.wells_by_name()['A3']

    te = reservoir.wells_by_name()['A5']

    dye = reservoir.wells_by_name()['A7']

    calibration_solution = tuberack_15.wells()[0]


    # protocol
    diluent_buff_col = deep_plate.columns()[diluent_buff_col-1]
    if plate_standard:
        ctx.comment('\n------------ADDING BUFFER TO PLATE------------\n\n')
        buffer_vols = [0, 250, 500, 750, 900, 950, 980, 1000]

        p300.pick_up_tip()
        p300.mix(1, 300, matrix_buff.bottom(z=4))

        for vol, well in zip(buffer_vols, diluent_buff_col):

            Transfer_With_TT(
                Pipette = p300,
                Source = matrix_buff,
                Destination = well,
                Vol = vol,
                Dispense_Top = False
            )

        p300.drop_tip()

        ctx.comment('\n------------ADDING CALIBRATION-----------\n\n')
        calibration_vols = [1000, 750, 500, 250, 100, 50, 20, 0]

        p300.pick_up_tip() # Moved to outside of loop
        p300.mix(1, 300, calibration_solution.bottom(z=4)) # Moved to outside of loop

        for vol, well in zip(calibration_vols, diluent_buff_col):
            if vol == 0:
                continue

            Transfer_With_TT(
                Pipette = p300,
                Source = calibration_solution,
                Destination = well,
                Vol = vol,
                Dispense_Top = True
            )

        p300.drop_tip() # Moved to outside of loop

    if duplicate_plating:
        ctx.comment('\n------------DUPLICATE PLATING------------\n\n')
        dispense_wells = [hs_plate.wells_by_name()[well]
                          for well in ['A1', 'A2', 'A11', 'A12']]
        source_col = diluent_buff_col[0]
        m300.pick_up_tip()
        m300.mix(5, 300, source_col.bottom(z = 3)) # Added in pre-wet
        m300.aspirate(200, source_col.bottom(z = 3))

        # Added in touch tip
        m300.move_to(source_col.top(z = -3))
        m300.touch_tip(v_offset=1)

        for well in dispense_wells:
            m300.dispense(50, well.bottom(z = 4))

            # Added in touch tip
            m300.move_to(well.top(z = -3))
            m300.touch_tip(v_offset=1)

        m300.drop_tip()

    else:
        ctx.comment('\n------------TRIPLICATE PLATING------------\n\n')
        dispense_wells = [hs_plate.wells_by_name()[well]
                          for well in ['A1', 'A2', 'A3', 'A10', 'A11', 'A12']]
        source_col = diluent_buff_col[0]
        m300.pick_up_tip()
        m300.mix(5, 300, source_col.bottom(z = 3)) # Added in pre-wet
        m300.aspirate(300, source_col.bottom(z = 3))

        # Added in touch tip
        m300.move_to(source_col.top(z = -3))
        m300.touch_tip(v_offset=1)

        for well in dispense_wells:
            m300.dispense(50, well.bottom(z = 4))

            # Added in touch tip
            m300.move_to(well.top(z = -3))
            m300.touch_tip(v_offset=1)

        m300.drop_tip()


    ctx.comment('\n------------ADDING SAMPLE------------\n\n')

    # Modified for faster sample addition with less tip wastage
    if duplicate_plating:
        reps = 2 * 2
    else:
        reps = 3 * 2

    for index, line in enumerate(csv_lines):
        csv_slot = int(line[0])

        csv_well = line[1]
        source_well = ctx.loaded_labwares[csv_slot].wells_by_name()[csv_well]
        dest_well = line[2]

        # Only pick up tip and aspirate if start of new replicate batch
        if index%reps == 0:
            p300.pick_up_tip()
            p300.mix(1, 50*reps, source_well.bottom(z = 4)) # Added in pre-wet
            p300.aspirate(50*reps, source_well.bottom(z = 4))
            p300.move_to(source_well.top(-3))
            p300.touch_tip()

        p300.dispense(50, hs_plate.wells_by_name()[dest_well].bottom(z = 4)) # Set z offset
        p300.move_to(hs_plate.wells_by_name()[dest_well].top(-3))
        p300.touch_tip()

        # Only drop up tip if end of new replicate batch
        if index%reps == reps - 1:
            p300.drop_tip()

    ctx.comment('\n------------PLATING TRITON------------\n\n')

    # Slow down aspirate and dispense rate
    m300.flow_rate.dispense *= 2.128
    m300.flow_rate.aspirate *= 2.128

    dispense_wells = hs_plate.rows()[0][:6]
    m300.pick_up_tip()
    m300.mix(1, 300, triton.bottom(z = 3))
    m300.aspirate(300, triton.bottom(z = 3))

    # Added in touch tip
    m300.move_to(triton.top(z = -3))
    m300.touch_tip(v_offset=1)


    for well in dispense_wells:
        m300.dispense(50, well.top())
        ctx.delay(seconds = 1)
        m300.move_to(well.top(z = 0))
        m300.touch_tip(v_offset=1)
        ctx.delay(seconds = 1)

    m300.drop_tip()

    ctx.comment('\n------------PLATING TE------------\n\n')
    dispense_wells = hs_plate.rows()[0][6:]
    m300.pick_up_tip()
    m300.mix(1, 300, te.bottom(z = 3))
    m300.aspirate(300, te.bottom(z = 3))
    for well in dispense_wells:
        m300.dispense(50, well.top())
        ctx.delay(seconds = 1)
        m300.move_to(well.top(z = 0))
        m300.touch_tip(v_offset=1)
        ctx.delay(seconds = 1)

    m300.drop_tip()

    try:
        if user_input_pause:
            ctx.pause('Place lid on plate on heater shaker')
            heater_shaker.set_and_wait_for_temperature(37)
            ctx.delay(minutes=10)
            heater_shaker.deactivate_heater()
            ctx.delay(minutes=5)
            ctx.pause('Remove lid on plate on heater shaker')
        else:
            heater_shaker.set_and_wait_for_temperature(37)
            ctx.delay(minutes=10)
            heater_shaker.deactivate_heater()
            ctx.delay(minutes=5)

    except:
        ctx.pause('The protocol did not do the heater shaker steps - please cancel')

    ctx.comment('\n------------PLATING DYE------------\n\n')

    m300.pick_up_tip()
    m300.mix(1, 300, dye.bottom(z = 3))

    # Changed how dye is dispensed so that each well only has one transfer action to preserve accuracy
    for i in range(0, 12, 3):
        wells = [well for well in hs_plate.rows()[0][i : i+3]]
        m300.aspirate(300, dye.bottom(z = 3))
        m300.touch_tip(v_offset=1)

        for well in wells:
            m300.dispense(100, well.top())
            ctx.delay(seconds = 1)
            m300.move_to(well.top(z = 0))
            m300.touch_tip(v_offset=1)
            ctx.delay(seconds = 1)

#     for _ in range(2):
#         m300.distribute(50, dye, [well.top() for well in hs_plate.rows()[0]],
#                         new_tip='never')

    m300.drop_tip()

    ctx.pause('''
    Plate is ready! Please remove, seal, and transport to the plate reader for
    analysis. Please remember to tidy the robot deck and dispose of any waste.
    ''')
