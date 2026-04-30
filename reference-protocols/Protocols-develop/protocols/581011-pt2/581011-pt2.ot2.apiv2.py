import math
from itertools import groupby

metadata = {
    'protocolName': 'Cherrypicking with Multi-Channel Pipette and CSV-Part 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):
    [csv_samp] = get_values(  # noqa: F821
        "csv_samp")

    # plate map excluding 1st column and row
    if csv_samp[0] == ',':
        csv_samp = csv_samp[1:]

    fields = [[val.strip() for val in line.split(',')][1:]
              for line in csv_samp.splitlines()
              if line.split(',')[0].strip()][17:19]

    day2 = fields[1]
    vol_effector_cell = int(day2[0])
    pre_mix = day2[1].lower().startswith("yes")
    mix_asp_height = float(day2[2])
    mix_disp_height = float(day2[3])
    premix_reps = int(day2[4])
    mix_vol = int(day2[5])
    mix_rate = float(day2[6])
    disp_res_height = float(day2[7])
    asp_height = float(day2[8])
    disp_height = float(day2[9])
    asp_rate = float(day2[10])
    disp_rate = float(day2[11])
    m300_mount = day2[12]

    # load labware
    plate = ctx.load_labware('corning_384_wellplate_112ul_flat', '4')
    effector_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '5')
    tiprack = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['6']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack)

    m300.well_bottom_clearance.aspirate = asp_height
    m300.well_bottom_clearance.dispense = disp_height
    m300.flow_rate.aspirate = asp_rate*m300.flow_rate.aspirate
    m300.flow_rate.dispense = disp_rate*m300.flow_rate.dispense

    # plate map excluding 1st column and row
    # remove first comma in csv sample if found
    if csv_samp[0] == ',':
        csv_samp = csv_samp[1:]
    plate_map = [[val.strip() for val in line.split(',')][1:]
                 for line in csv_samp.splitlines()
                 if line.split(',')[0].strip()][1:]

    # FIND NUMBER OF TIPS PER COLUMN
    letter_to_num = {'A': '1', 'B': '2', 'C': '3', 'D': '4',
                     'E': '5', 'F': '6', 'G': '7', 'H': '8'}
    num_tips_in_each_column = []

    for column in range(24):
        check_highest_letter = []
        for row in plate_map:
            well = row[column]

            if '/' in well:
                elements = well.split('/')
                if elements[1] == '0' or elements[0] == '0':
                    continue
                else:
                    check_highest_letter.append(int(
                        letter_to_num[elements[1][0]]))
        if len(check_highest_letter) > 0:
            num_tips_in_each_column.append(max(check_highest_letter))
        else:
            num_tips_in_each_column.append('x')

    # pick up function
    tip_count = 0

    def pickup(num_channels_per_pickup):
        nonlocal tip_count
        tips_ordered = [
            tip for rack in tiprack
            for row in rack.rows()[
                len(rack.rows())-num_channels_per_pickup::
                -1*num_channels_per_pickup]
            for tip in row]

        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    def check_volume(counter, tot_vol, chunk, source_well):
        if m300.current_volume < vol_effector_cell:
            if m300.current_volume > 0:
                m300.dispense(m300.current_volume,
                              source_well.bottom(disp_res_height))
            if counter != len(chunk)-1:
                if pre_mix:
                    mix_diff_height(source_well)
            if counter < len(chunk) and tot_vol >= vol_effector_cell:
                m300.aspirate(tot_vol if tot_vol < 200 else
                              200-0.15*vol_effector_cell, source_well)

    def mix_diff_height(well):
        m300.flow_rate.aspirate = m300.flow_rate.aspirate/asp_rate
        m300.flow_rate.dispense = m300.flow_rate.dispense/disp_rate
        for rep in range(premix_reps):
            m300.aspirate(mix_vol,
                          well.bottom(
                           mix_asp_height),
                          rate=mix_rate)
            m300.dispense(mix_vol,
                          well.bottom(
                           mix_disp_height),
                          rate=mix_rate)
        m300.flow_rate.aspirate = asp_rate*m300.flow_rate.aspirate
        m300.flow_rate.dispense = disp_rate*m300.flow_rate.dispense

    # find start well
    start_well = 0
    for row in plate_map:
        for well in row:
            if '/' in well:
                break
            start_well += 1
        if '/' in well:
            break
    start_row = math.floor(start_well/24)

    # find effecor cell column
    effector_columns = []

    for well in plate_map[start_row]:
        if '/' in well:
            left_and_right = well.split('/')
            right = left_and_right[1]
            effector_columns.append(right)
        else:
            effector_columns.append(well)

    # transfer target cell
    dispense_wells = [list(b) for a, b in groupby(effector_columns)]

    # transfer effector cell
    tip_col_ctr = 0
    wells_by_row = [well for row in plate.rows() for well in row]
    for j, chunk in enumerate(dispense_wells):
        # print(tip_col_ctr)

        if 'x' in chunk or 'X' in chunk or chunk[0][0] == '0':
            if j > 0:
                start_well += len(chunk)
                tip_col_ctr += len(chunk)
            else:
                tip_col_ctr += len(chunk)
            continue

        pickup(num_tips_in_each_column[tip_col_ctr])
        tot_vol = vol_effector_cell*len(chunk)*2+20
        for i, well in enumerate(chunk):
            source_well = effector_plate.wells_by_name()[str(chunk[0])]
            if vol_effector_cell >= 100:
                if pre_mix:
                    mix_diff_height(source_well)
                m300.aspirate(vol_effector_cell, source_well)
                m300.dispense(vol_effector_cell, wells_by_row[start_well])
                if pre_mix:
                    mix_diff_height(source_well)
                m300.aspirate(vol_effector_cell,
                              source_well)
                m300.dispense(vol_effector_cell, wells_by_row[start_well+24])
                start_well += 1
                tip_col_ctr += 1

            else:
                if m300.current_volume < vol_effector_cell:
                    if pre_mix:
                        mix_diff_height(source_well)
                    m300.aspirate(tot_vol if tot_vol < 200
                                  else 200-0.15*vol_effector_cell,
                                  source_well)

                # first row dispense
                m300.dispense(vol_effector_cell, wells_by_row[start_well])
                tot_vol -= vol_effector_cell
                check_volume(i, tot_vol, chunk, source_well)

                # second row dispense
                m300.dispense(vol_effector_cell,
                              wells_by_row[start_well+24])
                tot_vol -= vol_effector_cell
                check_volume(i, tot_vol, chunk, source_well)

                start_well += 1
                tip_col_ctr += 1
        if m300.current_volume > 0:
            m300.dispense(m300.current_volume,
                          source_well)
        m300.drop_tip()
        ctx.comment('\n\n')
