from itertools import groupby
import os
import csv
import math

metadata = {
    'protocolName': 'Normalization with Input .CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    [csv_samp, reset_tipracks, include_pause, v_0_tube1,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "csv_samp", "reset_tipracks",
        "include_pause", "v_0_tube1", "p20_mount", "p300_mount")

    # load labware
    source_plates = [ctx.load_labware('biorad_96_wellplate_200ul_pcr', slot)
                     for slot in ['2', '5', '8']]
    dest_plates = [ctx.load_labware('biorad_96_wellplate_200ul_pcr', slot)
                   for slot in ['3', '6', '9']]
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['1', '4', '7']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    diluent_rack = ctx.load_labware(
                    'opentrons_6_tuberack_50000ul', '11')

    # load instrument
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tiprack200)
    p300.starting_tip = tiprack200[0].wells()[reset_tipracks-1]

    plate_map = [[val.strip() for val in line.split(',')]
                 for line in csv_samp.splitlines()
                 if line.split(',')[0].strip()][1:]

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
    elif reset_tipracks:
        tip_count_list = [0, 0]
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            tip_count_list = next(csv_reader)

    num_one = int(tip_count_list[0])
    p300.starting_tip = tiprack200[0].wells()[num_one]

    def pick_up300(sample_tip=num_one, use_park=False):
        nonlocal num_one
        if num_one == 95:
            ctx.pause("Replace all 300ul non-filter tip racks")
            num_one = 0
            p300.pick_up_tip(tiprack200[0].wells()[num_one])
        else:
            p300.pick_up_tip(tiprack200[0].wells()[num_one])
            num_one += 1

    # liquid height tracking
    v_naught1 = v_0_tube1
    radius = diluent_rack.wells()[0].diameter/2
    h_naught1 = v_naught1/(math.pi*radius**2)
    h1 = h_naught1

    def adjust_height(vol):
        nonlocal h1
        dh = vol/(math.pi*radius**2)*5
        h1 -= dh
        if h1 < 5:
            h1 = 1
        else:
            return h1 - 10

    # csv numbers
    plate_num = 0
    well = 1
    dil_vol = 3
    sample_vol = 4

    plate_lengths = []
    for row in plate_map:
        plate_lengths.append(row[plate_num])

    grouped_plates = [list(b) for a, b in groupby(plate_lengths)]

    # TRANSFER DILUENT
    pick_up300()
    for row in plate_map:
        if float(row[dil_vol]) > 0:
            p300.aspirate(float(row[dil_vol]),
                          diluent_rack.wells()[0].bottom(z=h1))
            p300.dispense(float(row[dil_vol]),
                          dest_plates[int(row[plate_num])-1].wells_by_name()[
                            row[well]])
            adjust_height(float(row[dil_vol]))
            p300.blow_out()
            p300.touch_tip()
    p300.drop_tip()
    ctx.comment('\n\n\n')

    if include_pause:
        ctx.pause('''
                     Diluent is transferred to all plates.
                     Place the first sample source plate in slot 3 to begin
                     after selecting "Resume" on the Opentrons App.
                 ''')

    # TRANSFER SAMPLE
    row_ctr = 0
    for i, chunk in enumerate(grouped_plates):
        for row, plate in zip(plate_map[row_ctr:], chunk):
            p20.pick_up_tip(tiprack20[int(row[plate_num])-1].wells_by_name()
                            [row[well]])
            p20.transfer(float(row[sample_vol]),
                         source_plates[int(row[plate_num])-1].wells_by_name()
                         [row[well]],
                         dest_plates[int(row[plate_num])-1].wells_by_name()[
                              row[well]],
                         new_tip='never')
            p20.mix(1, 15, dest_plates[int(row[plate_num])-1].wells_by_name()[
               row[well]])
            p20.blow_out()
            p20.touch_tip()
            p20.drop_tip()
            row_ctr += 1
            ctx.comment('\n')
        if i < 2 and include_pause:
            ctx.pause(f'''Source plate {i+1} is transferred,
                    please load source plate {i+2}
                    and select "Resume on the Opentrons App."
                    ''')

    # write updated tipcount to CSV
    num_two = 0
    new_tip_count = str(num_one)+", "+str(num_two)+"\n"
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(new_tip_count)
