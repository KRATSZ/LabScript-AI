import os
import csv

metadata = {
    'protocolName': 'Diluting DNA with TE, using .csv File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [csv_samp, dna_asp_rate, tip_track,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "csv_samp", "dna_asp_rate", "tip_track",
            "p20_mount", "p300_mount")

    # load Labware
    dna_plate = ctx.load_labware('kingfisher_96_wellplate_100ul', 1)
    final_plate = ctx.load_labware('starstedt_96_wellplate_200ul', 2)
    tuberack = ctx.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 3)
    tipracks20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
                  for slot in [4, 5]]
    tipracks300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                   for slot in [7, 8]]

    star_height = 2
    king_height = 2

    # load instrument
    p20 = ctx.load_instrument("p20_single_gen2", p20_mount,
                              tip_racks=tipracks20)

    p300 = ctx.load_instrument("p300_single_gen2", p300_mount,
                               tip_racks=tipracks300)

    # Tip tracking between runs
    file_path = '/data/csv/tiptracking.csv'

    if not ctx.is_simulating():
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
    print(tip_count_list)

    num_one = int(tip_count_list[0]) if tip_track else 0
    num_two = int(tip_count_list[1]) if tip_track else 0

    tips20 = [tip for rack in tipracks20 for tip in rack.wells()]
    tips300 = [tip for rack in tipracks300 for tip in rack.wells()]

    tipcount20 = num_one
    tipcount300 = num_two

    def pick_up20():
        nonlocal tipcount20

        if tipcount20 == 191:
            ctx.pause("Replace 20ul tip racks")
            tipcount20 = 0
            p20.pick_up_tip(tips20[tipcount20])
            tipcount20 += 1
        else:
            p20.pick_up_tip(tips20[tipcount20])
            tipcount20 += 1

    def pick_up300():
        nonlocal tipcount300

        if tipcount300 == 191:
            ctx.pause("Replace all 300ul tip racks")
            tipcount300 = 0
            p300.pick_up_tip(tips300[tipcount300])
            tipcount300 += 1
        else:
            p300.pick_up_tip(tips300[tipcount300])
            tipcount300 += 1

    # mapping and parsing
    te = tuberack.wells()[0]
    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv_samp.splitlines()
                if line.split(',')[0].strip()][1:]

    num_samp = 0
    for row in csv_rows:

        if len(row[4]) == 0:
            break
        else:
            num_samp += 1
    csv_rows = csv_rows[:num_samp]

    for row in csv_rows:
        if float(row[4]) >= 180:
            raise Exception("Volume greater than 180ul TE in csv file")
    num_samp = len(csv_rows)

    # transferring TE
    ctx.comment('\n\n TRANSFERRING TE TO PLATE\n')
    for row in csv_rows:
        well = row[0]
        te_vol = float(row[4])
        pip = p20 if te_vol < 20 else p300
        if not pip.has_tip and pip == p20:
            pick_up20()
        elif not pip.has_tip and pip == p300:
            pick_up300()
        if te_vol > 0:
            pip.aspirate(te_vol, te.bottom(z=3))
            pip.dispense(te_vol, final_plate.wells_by_name()[well].bottom(z=star_height))  # noqa: E501
        else:
            continue
    if p20.has_tip:
        p20.drop_tip()

    if p300.has_tip:
        p300.drop_tip()

    ctx.comment('\n\n TRANSFERRING DNA TO PLATE\n')

    for row in csv_rows:

        dna_vol = float(row[2])
        well = row[0]
        te_vol = float(row[4])
        total_vol = te_vol + dna_vol
        pip = p20 if dna_vol < 20 else p300
        if not pip.has_tip and pip == p20:
            pick_up20()
        elif not pip.has_tip and pip == p300:
            pick_up300()
        pip.aspirate(dna_vol, dna_plate.wells_by_name()[well].bottom(z=king_height), rate=dna_asp_rate)  # noqa: E501
        pip.dispense(dna_vol, final_plate.wells_by_name()[well].bottom(z=star_height))  # noqa: E501
        if total_vol*0.8 > 20:
            if not p300.has_tip:
                pick_up300()
                p300.mix(3, total_vol*0.8, final_plate.wells_by_name()[well].bottom(z=star_height))  # noqa: E501
                p300.drop_tip()
            else:
                p300.mix(3, total_vol*0.8, final_plate.wells_by_name()[well].bottom(z=star_height))  # noqa: E501
        else:
            pip.mix(3, total_vol*0.8, final_plate.wells_by_name()[well].bottom(z=star_height))  # noqa: E501
        pip.drop_tip()

    num_one = tipcount20
    num_two = tipcount300

    # write updated tipcount to CSV
    new_tip_count = str(num_one)+", "+str(num_two)+"\n"
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)
