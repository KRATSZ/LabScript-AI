import math
import os
import csv

metadata = {
    'protocolName': 'Dilution with CSV File and Custom Tube Rack',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [csv_samp, init_vol_dil, tip_track,
        p20_mount, p1000_mount] = get_values(  # noqa: F821
        "csv_samp", "init_vol_dil", "tip_track", "p20_mount", "p1000_mount")

    # load Labware and modules
    temp_mod = ctx.load_module('temperature module gen2', 1)
    temp_mod.set_temperature(4)

    final_rack = temp_mod.load_labware('sh_48_wellplate_2500ul')
    sample_plate = ctx.load_labware('nest_96_wellplate_200ul_flat', 2)
    diluent_rack = ctx.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 4)  # noqa: E501
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', 5)]
    tips1000 = [ctx.load_labware('geb_96_tiprack_1000ul', 6)]

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips)
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tips1000)

    # Tip tracking between runs
    if not ctx.is_simulating():
        file_path = '/data/csv/tiptracking.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial tip count tracking
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                outfile.write("0, 0\n")

    tip_count_list = []
    if ctx.is_simulating():
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    num_one = int(tip_count_list[0]) if tip_track else 0
    num_two = int(tip_count_list[1]) if tip_track else 0

    tips20 = [tip for tip in tips[0].wells()]
    tips1000 = [tip for tip in tips1000[0].wells()]

    tipcount20 = num_one
    tipcount1000 = num_two

    def pick_up20():
        nonlocal tipcount20

        if tipcount20 == 95:
            ctx.pause("Replace 20ul tip rack")
            tipcount20 = 0
            p20.pick_up_tip(tips20[tipcount20])
            tipcount20 += 1
        else:
            p20.pick_up_tip(tips20[tipcount20])
            tipcount20 += 1

    def pick_up1000():
        nonlocal tipcount1000

        if tipcount1000 == 95:
            ctx.pause("Replace 1000ul tip rack")
            tipcount1000 = 0
            p1000.pick_up_tip(tips1000[tipcount1000])
            tipcount1000 += 1
        else:
            p1000.pick_up_tip(tips1000[tipcount1000])
            tipcount1000 += 1

    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv_samp.splitlines()
                if line.split(',')[0].strip()][1:]

    # liquid height tracking
    v_naught_dil = init_vol_dil*1000
    radius = diluent_rack.wells()[0].diameter/2
    h_naught_dil = 0.85*v_naught_dil/(math.pi*radius**2)
    h = h_naught_dil

    def adjust_height(vol):
        nonlocal h
        dh = vol/(math.pi*radius**2)
        h -= dh
        if h < 12:
            h = 1

    # protocol
    ctx.comment('\n~~~~ADDING DILUENT~~~~\n\n')
    for row in csv_rows:
        dil_vol = int(row[0])
        disp_tube = row[1]

        pick_up1000()
        p1000.aspirate(dil_vol, diluent_rack.wells()[0].bottom(z=h))
        p1000.dispense(dil_vol,
                       final_rack.wells_by_name()[disp_tube].top(z=-1))
        ctx.delay(seconds=2)
        p1000.blow_out()
        p1000.air_gap(100)
        p1000.drop_tip()
        adjust_height(dil_vol)
        ctx.comment('\n')

    ctx.comment('\n~~~~ADDING SAMPLE~~~~\n\n')
    for row in csv_rows:
        sample_vol = int(row[3])
        samp_well = sample_plate.wells_by_name()[row[2]]
        disp_tube = final_rack.wells_by_name()[row[1]]

        pick_up20()
        p20.transfer(sample_vol, samp_well, disp_tube.bottom(z=5),
                     new_tip='never')
        p20.mix(2, p20.max_volume, disp_tube.bottom(z=5), rate=2)
        p20.blow_out()
        p20.drop_tip()
        ctx.comment('\n')

    num_one = tipcount20
    num_two = tipcount1000

    # write updated tipcount to CSV
    new_tip_count = str(num_one)+", "+str(num_two)+"\n"
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)
