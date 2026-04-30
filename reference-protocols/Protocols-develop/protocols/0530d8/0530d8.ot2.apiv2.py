import math

metadata = {
    'protocolName': 'DNA Extraction with Heater Shaker - Part 1',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_plates, csv_samp1, csv_samp2, csv_samp3,
        p300_mount, m300_mount] = get_values(  # noqa: F821
        "num_plates", "csv_samp1", "csv_samp2", "csv_samp3",
            "p300_mount", "m300_mount")

    # labware
    dw_plates = [ctx.load_labware('abgene_96_wellplate_2000ul', slot)
                 for slot in [1, 2, 3]][:num_plates]
    reag_plate = ctx.load_labware('abgene_96_wellplate_2000ul', 8)
    mag_mod = ctx.load_module('magnetic module gen2', 4)
    mag_plate = mag_mod.load_labware('abgene_96_wellplate_2000ul')
    print(mag_plate)

    heater_shaker = ctx.load_module('heaterShakerModuleV1', 10)
    hs_plate = heater_shaker.load_labware('abgene_96_wellplate_2000ul')
    heater_shaker.close_labware_latch()
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [5, 6, 7, 9]]

    # single and multi pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    # mapping
    csv_rows1 = [[val.strip() for val in line.split(',')]
                 for line in csv_samp1.splitlines()
                 if line.split(',')[0].strip()][1:]
    csv_rows2 = [[val.strip() for val in line.split(',')]
                 for line in csv_samp2.splitlines()
                 if line.split(',')[0].strip()][1:]
    csv_rows3 = [[val.strip() for val in line.split(',')]
                 for line in csv_samp3.splitlines()
                 if line.split(',')[0].strip()][1:]

    all_csvs = [csv_rows1, csv_rows2, csv_rows3][:num_plates]

    num_samp = len(csv_rows1) + len(csv_rows2) + len(csv_rows3)
    if not 1 <= num_samp <= 90:
        raise Exception("Enter a sample number between 1-90")
    for csv in all_csvs:
        for row in csv:
            num_samp += 1
    num_col = math.ceil(num_samp/8)

    ctx.comment('\n---------------ADDING SAMPLE----------------\n\n')
    dest_well_ctr = 0
    for i, csv in enumerate(all_csvs):
        for row in csv:
            source_plate = dw_plates[i]
            source_well = row[6] + row[7]

            source = source_plate.wells_by_name()[source_well]
            dest = hs_plate.wells()[dest_well_ctr]

            p300.pick_up_tip()
            for _ in range(2):
                p300.aspirate(150, source)
                p300.dispense(150, dest)
                p300.blow_out(dest.top(z=-2))
            p300.drop_tip()
            dest_well_ctr += 1
            ctx.comment('\n')

    ctx.comment('\n---------------ADDING CONTROLS----------------\n\n')
    control_source = reag_plate.columns()[0]
    controls_dest = hs_plate.columns()[11][2:]
    for source, dest in zip(control_source, controls_dest):
        p300.pick_up_tip()
        for _ in range(2):
            p300.aspirate(150, source)
            p300.dispense(150, dest)
            p300.blow_out(dest.top(z=-2))
        p300.drop_tip()
        ctx.comment('\n')

    ctx.comment('\n---------------ADDING 50ul REAGENT----------------\n\n')
    for col in hs_plate.rows()[0][:num_col]:
        m300.pick_up_tip()
        m300.aspirate(50, reag_plate.rows()[0][1])
        m300.dispense(50, col)
        m300.mix(3, 200, col)
        m300.blow_out(col.top(z=-2))
        m300.drop_tip()
        ctx.comment('\n')

    if num_samp <= 88:
        m300.pick_up_tip()
        m300.aspirate(50, reag_plate.rows()[0][1])
        m300.dispense(50, hs_plate.rows()[0][11])
        m300.mix(3, 200, hs_plate.rows()[0][11])
        m300.blow_out(col.top(z=-2))
        m300.drop_tip()
        ctx.comment('\n')

    heater_shaker.set_and_wait_for_temperature(37)
    heater_shaker.set_and_wait_for_shake_speed(200)
    ctx.delay(minutes=60)
    heater_shaker.deactivate_heater()
    heater_shaker.deactivate_shaker()

    ctx.comment('\n---------------ADDING 60ul REAGENT----------------\n\n')
    for col in hs_plate.rows()[0][:num_col]:
        m300.pick_up_tip()
        m300.aspirate(60, reag_plate.rows()[0][2])
        m300.dispense(60, col)
        m300.blow_out(col.top(z=-2))
        m300.drop_tip()
        ctx.comment('\n')

    if num_samp <= 88:
        m300.pick_up_tip()
        m300.aspirate(60, reag_plate.rows()[0][2])
        m300.dispense(60, hs_plate.rows()[0][11])
        m300.blow_out(col.top(z=-2))
        m300.drop_tip()
        ctx.comment('\n')

    heater_shaker.set_and_wait_for_temperature(55)
    ctx.delay(minutes=30)
    heater_shaker.deactivate_heater()
    heater_shaker.deactivate_shaker()
