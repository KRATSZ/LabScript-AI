"""Protocol."""
metadata = {
    'protocolName': 'ReliaPrep™ Viral TNA Miniprep System, Custom Workflow',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    """Protocol..."""
    [num_samp, sample_tube_clearance, p20_rate, p1000_rate,
        p20_mount, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "sample_tube_clearance",
        "p20_rate", "p1000_rate", "p20_mount", "p1000_mount")

    # load labware
    samples = ctx.load_labware('opentrons_15_tuberack_8000ul', '1',
                               label='Sample Tube Rack')
    final_tuberack = ctx.load_labware(
                'binding_column_tuberack', '2',
                label='Final tube rack')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml',
                                 '3', label='Reservoir')
    final_plate_384 = ctx.load_labware('filtrouslab_384_wellplate_50ul', '8')
    tiprack1000 = ctx.load_labware('opentrons_96_tiprack_1000ul', '4')
    tiprack20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['5', '6']]

    if not 1 <= num_samp <= 12:
        raise Exception('Enter a sample number between 1-12')

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=[tiprack1000])

    p20.flow_rate.dispense = p20_rate*p20.flow_rate.dispense
    p1000.flow_rate.dispense = p1000_rate*p1000.flow_rate.dispense

    # PROTOCOL
    final_tubes_pt1 = [tube for column in final_tuberack.columns()[::2]
                       for tube in column][:num_samp]
    final_tubes_pt2 = [tube for column in final_tuberack.columns()[1::2]
                       for tube in column][:num_samp]

    # reagents
    pro_k = reservoir.wells()[0]
    cell_lysis_buffer = reservoir.wells()[1]
    isoprop = reservoir.wells()[2]
    wash_solution = reservoir.wells()[3]
    water = reservoir.wells()[4]

    # move pro k to final tube rack
    ctx.comment('\n\nAdding Pro-K to Tube Rack\n')
    p20.pick_up_tip()
    for tube in final_tubes_pt1:
        p20.aspirate(20, pro_k)
        p20.dispense(20, tube)
        p20.blow_out()
        p20.touch_tip()
    p20.drop_tip()

    # move sample to final tube rack
    ctx.comment('\n\nAdding Sample to Tube Rack\n')
    for sample_tube, final_tube in zip(samples.wells(),
                                       final_tubes_pt1):
        p1000.pick_up_tip()
        p1000.aspirate(200, sample_tube.bottom(z=sample_tube_clearance))
        p1000.dispense(200, final_tube)
        p1000.blow_out()
        p1000.touch_tip()
        p1000.drop_tip()

    # move cell lysis buffer to tube rack
    ctx.comment('\n\nAdding Cell Lysis Buffer to Tube Rack\n')
    for tube in final_tubes_pt1:
        p1000.pick_up_tip()
        p1000.aspirate(200, cell_lysis_buffer)
        p1000.dispense(200, tube)
        p1000.mix(12, 380, tube)
        p1000.blow_out()
        p1000.touch_tip()
        p1000.drop_tip()

    # incubate for 10 minutes
    ctx.comment('\n\nIncubating and Adding Isopropanol\n')
    ctx.delay(minutes=10)
    p1000.home()
    ctx.comment('''
              Incubation complete. Please ensure empty tubes have binding
              columns prepped.''')

    # move isopropanol and sample to binding column
    ctx.comment('\n\nAdding Isopropanol to Tube Rack, then Binding Column\n')
    for sample_tube, binding_tube in zip(final_tubes_pt1, final_tubes_pt2):
        p1000.pick_up_tip()
        p1000.aspirate(250, isoprop)
        p1000.dispense(250, sample_tube)
        p1000.mix(12, 600, sample_tube)
        p1000.aspirate(670, sample_tube)
        p1000.dispense(670, binding_tube)
        p1000.blow_out()
        p1000.drop_tip()

    p1000.home()
    ctx.pause('''
            Centrifuge samples with binding columns for 1 minute at 15000 RPM.
            Remove the binding column/collection tube from the centrifuge.
            Discard the collection tube containing flowthrough.
            Place the binding column into a new collection tube.
            Select "Resume" on the Opentrons App to continue.
            ''')

    # 3 washes
    ctx.comment('\n\n3 Washes\n')
    p1000.flow_rate.dispense = 0.75*p1000.flow_rate.dispense

    for _ in range(3):
        p1000.pick_up_tip()
        for tube in final_tubes_pt2:
            p1000.aspirate(500, wash_solution)
            p1000.dispense(500, tube.top())
            p1000.home()
        p1000.drop_tip()
        ctx.pause('''
                Recap samples, centrifuge for approximately 1 minute at
                approximately 15000 RPM. Discard the collection tube
                containing the flowthrough and place the column into a new
                collection tube. Place back on the tube rack
                and select "Resume".
                ''')
    p1000.home()
    ctx.pause('''
            Please ensure that empty tubes are on the even columns of the final
            tube rack on Slot 2. Select "Resume" on the Opentrons App for
            100ul of Nuclease free water to be added to these empty tubes
            on the odd number columns of the tube rack.
            ''')

    p1000.flow_rate.dispense = 1.33*p1000.flow_rate.dispense
    ctx.comment('\n\nAdding Water to Tube Rack\n')
    p1000.pick_up_tip()
    for tube in final_tubes_pt2:
        p1000.aspirate(100, water)
        p1000.dispense(100, tube)
        p1000.blow_out()
        p1000.touch_tip()
    p1000.drop_tip()
    p1000.home()

    ctx.pause('''
            Place binding column in tubes populated with nuclease free water.
            Select "Resume" on the Opentrons App for 100ul of Nuclease free
            water to be added to these binding column tubes on the odd number
            columns of the tube rack.
             ''')

    ctx.comment('\n\nAdding Water to Tube Rack\n')
    p1000.flow_rate.dispense = 0.75*p1000.flow_rate.dispense
    p1000.pick_up_tip()
    for tube in final_tubes_pt2:
        p1000.aspirate(100, water)
        p1000.dispense(100, tube.top())
        p1000.blow_out()
        p1000.touch_tip()
    p1000.drop_tip()
    p1000.home()
    ctx.pause('''
            Centrifuge tubes for approximately 1 minute at 1500 RPM.
            Be careful with the 1.5 ml tube caps.
            Point the cap toward the bottom of the centrifuge.
             ''')

    # Final transfer to 384
    plate_map_A = [well for col in range(0, len(final_plate_384.columns()))
                   for row in final_plate_384.rows()[::2]
                   for well in row[col*4:col*4+4]]
    plate_map_B = [well for col in range(0, len(final_plate_384.columns()))
                   for row in final_plate_384.rows()[1::2]
                   for well in row[col*4:col*4+4]]
    chunks_A = [plate_map_A[i:i+4] for i in range(0, len(plate_map_A), 4)]
    chunks_B = [plate_map_B[i:i+4] for i in range(0, len(plate_map_B), 4)]

    airgap = 4
    col_counter = 0
    for i, elute in enumerate(final_tubes_pt2[:num_samp]):
        if i % 2 == 0:
            chunks = chunks_A

        else:
            chunks = chunks_B
        if i % 2 == 0 and i > 0:
            col_counter += 1

        for i, chunk in enumerate(chunks[col_counter*8:col_counter*8+8]):

            p20.pick_up_tip()
            p20.aspirate(20, elute.bottom(z=-20))
            p20.touch_tip()
            for well in chunk:
                if well == final_plate_384.wells_by_name()["O23"]:
                    continue
                elif well == final_plate_384.wells_by_name()["P23"]:
                    continue
                p20.dispense(4, well)
            p20.air_gap(airgap)
            # p20.dispense(p20.current_volume, elute.top())
            # p20.blow_out()
            p20.drop_tip()

        ctx.comment('\n\n')
