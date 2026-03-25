from opentrons import protocol_api
from opentrons.types import Point
import os
import json

metadata = {
    'protocolName': 'Cell Culture Prep with CSV Input',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [csv, m300_mount, p300_mount, temp_mod_temp, asp_rate_step1,
     pbs_dispense_rate,
     incubation_time, first_media_x, second_media_y, track_tips
     ] = get_values(  # noqa: F821
        "csv", "m300_mount", "p300_mount", "temp_mod_temp",
        "asp_rate_step1", "pbs_dispense_rate",
        "incubation_time", "first_media_x", "second_media_y", "track_tips")

    # LABWARE
    temp_mod = ctx.load_module('temperature module gen2', '10')
    reagents = ctx.load_labware('nest_12_reservoir_15ml', '11')
    waste_res = ctx.load_labware('nest_12_reservoir_15ml', '7')
    plate = temp_mod.load_labware(
                'corning_96_wellplate_360ul_flat', '10')

    # TIPRACKS
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                for slot in ['4', '5', '6']]

    # INSTRUMENTS
    p300 = ctx.load_instrument('p300_single_gen2',
                               p300_mount,
                               tip_racks=tipracks)
    m300 = ctx.load_instrument('p300_multi_gen2',
                               m300_mount,
                               tip_racks=tipracks)

    tips_by_col = [tip for rack in tipracks
                   for col in rack.columns() for tip in col[::-1]]
    tip_cols = [tips_by_col[i:i+8] for i in range(0, len(tips_by_col), 8)]

    """ TIP-TRACKING BETWEEN RUNS. """
    total_tip_cols = 36

    file_path = '/data/csv/tiptracking.json'
    file_dir = os.path.dirname(file_path)

    tips_by_col = [tip for rack in tipracks
                   for col in rack.columns() for tip in col[::-1]]
    tip_cols = [tips_by_col[i:i+8] for i in range(0, len(tips_by_col), 8)]

    if track_tips and not ctx.is_simulating():
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # if no file, then use standard tip_chunks definition, and the
        # end of the code will write to updated tip_chunks list to
        # the file created. This if statement handles the case in which
        # tip tracking is selected for the first time.
        if not os.path.isfile(file_path):
            tip_chunks = [tips_by_col[i:i+8] for i in range(0,
                          len(tips_by_col), 8)]
        else:
            # grab nested list tip_chunks from file.
            source = open(file_path, 'rb').read()
            # see below for conversion of tip_chunks nested list to bools.
            # in order to dump the well objects in tip_chunks to a json file,
            # they had to be serializable (int, string, bool). The end of the
            # protocol does this conversion.
            tip_bool_chunks = json.loads(source)

            # convert bools back to well objects to use.
            tip_chunks = [[] for _ in range(total_tip_cols)]
            for i, (bool_chunk, tip_chunk) in enumerate(zip(tip_bool_chunks,
                                                            tip_cols)):
                if len(bool_chunk) == 0:
                    continue
                for true_tip, tip_loc in zip(bool_chunk, tip_chunk):
                    if true_tip:
                        tip_chunks[i].append(tip_loc)
                    else:
                        continue

    else:
        # standard definition of tip_chunks if not tracking tips.
        tip_chunks = [tips_by_col[i:i+8] for i in range(0,
                      len(tips_by_col), 8)]
    """PROTOCOL BEGINS """
    csv_rows = [[val.strip() for val in line.split(',')]
                for line in csv.splitlines()
                if line.split(',')[0].strip()][1:]

    """FIND INVOLVED WELLS"""
    values_from_csv = []
    wells_from_csv = []
    for row in csv_rows:
        well, value = row[:2]
        value = int(value)
        values_from_csv.append(value)
        wells_from_csv.append(well)

    # create nested list of all values in csv (by column).
    value_chunk_cols = [values_from_csv[i:i+8]
                        for i in range(0, len(values_from_csv), 8)]
    list_well_tips = []

    """CREATE A LIST OF # TIPS FOR EACH WELL"""
    start_point = 0
    tip_count = 0
    for i, chunk in enumerate(value_chunk_cols):
        start_point = 0

        # check for the values in each column.
        # if we find a well with a value of 85 or greater,
        # use that index (j) as the starting point and see how many values
        # after that are also greater than 85. Once we don't find one,
        # break.
        for j, value in enumerate(chunk[start_point:]):
            if value >= 85:
                for check_values in chunk[j:]:
                    if check_values >= 85:
                        tip_count += 1
                    else:
                        break

                list_well_tips.append(tip_count)
                tip_count = 0
                continue

            else:
                list_well_tips.append(0)

    # create a dictionary which says how many tips go to each well.
    # For example, if the entire first column has values higher than 85,
    # the first value in the dictionary will be "A1: 8". If first four wells
    # in column 2 are greater than 85, "B1:4".
    dict_tips_per_well = {}
    tip_ctr = 0
    for j, (well, num_tips) in enumerate(zip(wells_from_csv,
                                             list_well_tips)):
        if tip_ctr > 0:
            tip_ctr -= 1
            continue

        if num_tips > 0:
            tip_ctr = num_tips - 1
            dict_tips_per_well[well] = num_tips

    # print('\n\n', dict_tips_per_well, '\n\n')

    """PICKUP FUNCTION"""
    def pick_up(num_channels_per_pickup):
        nonlocal tip_chunks
        if num_channels_per_pickup > 1:
            pip = m300
        else:
            pip = p300
        try:
            col = 0
            # based on the demand of the next well (1-8 tips), this for loop
            # will find the first available column having adequate number
            # of tips starting from the first. If the tip pick up order is:
            # 6, 8, 2 for the first 3 pick ups, then 6 tips will be taken from
            # column 1, 8 tips from column 2, and 2 tips back from column 1.
            # efficient tip pick up instead of "throwing away" a whole column
            # after pick up.
            for _ in range(36):
                if num_channels_per_pickup <= len(tip_chunks[col]):
                    break
                else:
                    col += 1
            pip.pick_up_tip(tip_chunks[col][num_channels_per_pickup-1])

            # remove as many tips as we picked up in that column
            # from the 0 index.
            for _ in range(num_channels_per_pickup):
                tip_chunks[col].pop(0)

        # replace tip exception
        except IndexError:
            ctx.pause("Replace empty tip racks on slots 4, 5, and 6")
            pip.reset_tipracks()
            tip_chunks = [tips_by_col[i:i+8] for i in range(0,
                          len(tips_by_col), 8)]
            col = 0
            for _ in range(36):
                if num_channels_per_pickup <= len(tip_chunks[col]):
                    break
                else:
                    col += 1

            pip.pick_up_tip(tip_chunks[col][num_channels_per_pickup-1])

            for _ in range(num_channels_per_pickup):
                tip_chunks[col].pop(0)

                if len(tip_chunks[col]) == 0:
                    tip_chunks.remove(tip_chunks[col])

    # DUMP WASTE
    vol_ctr = 0
    waste_well = 0

    # move to next well in reservoir once we fill one.
    def check_waste_vol(vol):
        nonlocal vol_ctr
        nonlocal waste_well
        vol_ctr += vol
        if vol_ctr > 12000:
            waste_well += 1
            vol_ctr = 0
    waste = waste_res.wells()[waste_well]
    temp_mod.set_temperature(temp_mod_temp)

    ctx.pause("""
    Ensure temperature module is at correct temperature, then,
    select "Resume" on the Opentrons app.
    """)

    # REAGENTS
    pbs = reagents.wells()[0]
    trypsin = reagents.wells()[1]
    media = reagents.wells()[-1]

    airgap = 20

    ctx.comment("MOVING INCLUDED WELLS TO WASTE")
    for i, well in enumerate(dict_tips_per_well):
        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        # aspirate from side so as to not disturb cell culture.
        pip.aspirate(200, plate_well.bottom(z=1).move(
                Point(x=(plate_well.diameter/2-2))), rate=asp_rate_step1)
        pip.dispense(200, waste)
        check_waste_vol(200)
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')
    ctx.comment("\n\n\nMOVING PBS TO PLATE")
    for i, well in enumerate(dict_tips_per_well):
        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(150, pbs, rate=pbs_dispense_rate)
        pip.dispense(150, plate_well.bottom(z=1).move(
                Point(x=(plate_well.diameter/2-2))))
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    ctx.comment("\n\n\nREMOVING PBS FROM PLATE")
    for i, well in enumerate(dict_tips_per_well):
        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(175, plate_well.bottom(z=1).move(
                Point(x=(plate_well.diameter/2-2))))
        pip.dispense(175, waste)
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    ctx.comment("\n\n\nMOVING TRYPSIN TO PLATE")
    for i, well in enumerate(dict_tips_per_well):

        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(25, trypsin)
        pip.dispense(25, plate_well)
        pip.blow_out()
        pip.touch_tip()
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    ctx.delay(minutes=incubation_time)

    ctx.comment("\n\n\nMOVING MEDIA TO PLATE")
    for i, well in enumerate(dict_tips_per_well):

        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(140, media)
        pip.dispense(140, plate_well)
        pip.blow_out()
        pip.touch_tip()
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    ctx.comment("\n\n\nASPIRATE FIRST MEDIA FROM PLATE")
    for i, well in enumerate(dict_tips_per_well):

        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(first_media_x, plate_well.bottom(z=1).move(
                Point(x=(plate_well.diameter/2-2))))
        pip.dispense(first_media_x, waste)
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    ctx.comment("\n\n\nDISPENSE SECOND MEDIA TO PLATE")
    for i, well in enumerate(dict_tips_per_well):

        num_tips = dict_tips_per_well[well]
        plate_well = plate.wells_by_name()[well]
        if num_tips > 1:
            pip = m300
        else:
            pip = p300

        pick_up(num_tips)
        pip.aspirate(second_media_y, media)
        pip.dispense(second_media_y, plate_well)
        pip.air_gap(airgap)
        pip.drop_tip()
        ctx.comment('\n')

    tip_data = []
    for i, chunk in enumerate(tip_chunks):
        tip_data.append([])
        if len(chunk) > 0:
            for value in chunk:
                tip_data[i].append(True)
        else:
            continue

    # write to the ot-2 no matter what in case the user would like to start
    # tracking tips for the next run
    if not ctx.is_simulating():
        with open(file_path, 'w') as outfile:
            outfile.write(json.dumps(tip_data))
