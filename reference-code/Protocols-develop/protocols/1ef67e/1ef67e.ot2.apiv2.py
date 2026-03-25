import os
import csv

metadata = {
    'protocolName': 'NCI Panel 1',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [num_samps, n_cor, cd4_dil, cd8_dil, fox_dil, pdl1_dil, ki_dil, pan_dil,
     ds_520, ds_570, ds_540,
     ds_620, ds_650, ds_690] = get_values(  # noqa: F821
        'num_samps', 'n_cor', 'cd4_dil', 'cd8_dil', 'fox_dil', 'pdl1_dil',
        'ki_dil', 'pan_dil', 'ds_520', 'ds_570', 'ds_540',
        'ds_620', 'ds_650', 'ds_690')

    init_cond_dict = {
      '520': [0, 'A1'],
      '540': [0, 'B1'],
      '570': [0, 'C1'],
      '620': [0, 'D1'],
      '650': [0, 'E1'],
      '690': [0, 'F1'],
      'CD3': [0, 'A2'],
      'CD4': [0, 'B2'],
      'CD8': [0, 'C2'],
      'CD20': [0, 'D2'],
      'CD56': [0, 'E2'],
      'CD68': [0, 'F2'],
      'CD163': [0, 'G2'],
      'PD1': [0, 'H2'],
      'PDL1': [0, 'A3'],
      'FOXP3': [0, 'B3'],
      'PANCK': [0, 'C3'],
      'KI67': [0, 'D3'],
      '520_src': [75, 'A1'],
      '540_src': [75, 'B1'],
      '570_src': [75, 'C1'],
      '620_src': [75, 'D1'],
      '650_src': [75, 'A2'],
      '690_src': [75, 'B2'],
      'CD3_src': [1000, 'A3'],
      'CD4_src': [100, 'B3'],
      'CD8_src': [100, 'C3'],
      'CD20_src': [250, 'D3'],
      'CD56_src': [1000, 'A4'],
      'CD68_src': [100, 'B4'],
      'CD163_src': [100, 'C4'],
      'PD1_src': [100, 'D4'],
      'PDL1_src': [100, 'A5'],
      'FOXP3_src': [500, 'B5'],
      'PANCK_src': [1000, 'C5'],
      'KI67_src1': [2000, 'D5'],
      'KI67_src2': [2000, 'A6'],
      'KI67_src3': [2000, 'B6'],
      'KI67_src4': [2000, 'C6'],
      'KI67_src5': [2000, 'D6'],
      'ab_dil': [50000, '93'],
      'amp_dil': [50000, '93'],
      'p10tip': [0, 'tip'],
      'p1ktip': [0, 'tip']
      }
    if not protocol.is_simulating():
        file_path = '/data/csv/ReagentVols.csv'
        file_dir = os.path.dirname(file_path)
        # check for file directory
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # check for file; if not there, create initial volumes csv
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as outfile:
                for key in init_cond_dict:
                    outfile.write("%s,%s,%s\n" % (key, init_cond_dict[key][0],
                                  init_cond_dict[key][1]))

    # create volumes dictionary based on csv file
    volumes_dict = {}
    if protocol.is_simulating():
        volumes_dict = init_cond_dict
    else:
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                volumes_dict[row[0]] = [float(row[1]), row[2]]

    # create labware
    tips10 = protocol.load_labware('opentrons_96_tiprack_10ul', '4')
    tips1k = protocol.load_labware('opentrons_96_tiprack_1000ul', '1')

    p10 = protocol.load_instrument('p10_single', 'right', tip_racks=[tips10])
    p1k = protocol.load_instrument('p1000_single', 'left', tip_racks=[tips1k])

    plate_als = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '3', 'Aliquots Plate')
    tube_rack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '6',
        'Tube Rack for Reagents'
        )
    big_tubes = protocol.load_labware(
        'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical',
        '5',
        '15mL & 50mL Tubes'
        )
    ab_dilutent = big_tubes['A3']
    amp_dilutent = big_tubes['A4']

    tubes6 = protocol.load_labware('custom_tuberack_6ml', '2')

    # constants definition
    tip10count = volumes_dict['p10tip'][0]
    tip1kcount = volumes_dict['p1ktip'][0]
    ab_ht = float(volumes_dict['ab_dil'][1])
    ab_vol = volumes_dict['ab_dil'][0]
    amp_ht = float(volumes_dict['amp_dil'][1])
    amp_vol = volumes_dict['amp_dil'][0]

    def pick_up(pip):
        nonlocal tip10count
        nonlocal tip1kcount

        pipp = p10 if pip == p10 else p1k
        tipc = tip10count if pip == p10 else tip1kcount
        tipr = tips10 if pip == p10 else tips1k

        if tipc == 96:
            pipp.home()
            protocol.pause('Out of tips for respective pipette. Please replace \
            and click RESUME.')
            tipr.reset()
            tipc = 0

        pipp.pick_up_tip()

        if pip == p10:
            tip10count += 1
        else:
            tip1kcount += 1

    def ab_d_transfer(vol, dest):
        nonlocal ab_ht
        nonlocal ab_vol

        if vol >= ab_vol:
            protocol.pause('More antibody dilutent needed, please replace. \
            When replaced in A3, click RESUME.')
            ab_vol = 50000
            ab_ht = 93
        pick_up(p1k)

        while vol > 1000:
            p1k.transfer(
                1000, ab_dilutent.bottom(ab_ht),
                dest.top(), new_tip='never')
            p1k.blow_out(dest.top())
            vol -= 1000

        p1k.transfer(
            vol, ab_dilutent.bottom(ab_ht), dest.top(), new_tip='never')
        p1k.mix(8, 800, dest.bottom(25))
        p1k.blow_out(dest.top())
        p1k.drop_tip()

        new_ht = 1.10 * (vol / (3.14*13.9)**2)

        ab_ht -= new_ht
        ab_vol -= vol

        if ab_ht <= 4:
            ab_ht = 1

    def amp_transfer(vol, dest):
        nonlocal amp_ht
        nonlocal amp_vol

        if vol >= amp_vol:
            protocol.pause('More opal dilutent needed, please replace. \
            When replaced in A4, click RESUME.')
            amp_vol = 50000
            amp_ht = 93

        pick_up(p1k)

        while vol > 1000:
            p1k.transfer(
                1000, amp_dilutent.bottom(amp_ht),
                dest.top(), new_tip='never')
            p1k.blow_out(dest.top())
            vol -= 1000

        p1k.transfer(
            vol, amp_dilutent.bottom(amp_ht), dest.top(), new_tip='never')
        p1k.mix(8, 800, dest.bottom(25))
        p1k.blow_out(dest.top())
        p1k.drop_tip()

        new_ht = 1.10 * (vol / (3.14*13.9)**2)

        amp_ht -= new_ht
        amp_vol -= vol

        if amp_ht <= 4:
            amp_ht = 1

    def ab_transfer(vol, src, dest):
        ab = volumes_dict[src]
        ab_src = volumes_dict[src+'_src']

        ab_vol = ab[0]
        ab_well = plate_als[ab[1]]

        ab_src_vol = ab_src[0]
        ab_src_well = tube_rack[ab_src[1]]

        pause_msg = 'Please add more '+src+' antibody to well '+ab_src[1]+' \
        in slot 6. When ready, click RESUME.'

        if vol >= ab_vol:
            if ab_src_vol <= 50:
                protocol.pause(pause_msg)
                ab_src[0] += init_cond_dict[src+'_src'][0]
            p10.transfer(50, ab_src_well, ab_well, new_tip='never')
            ab_src[0] -= 50
            ab[0] += 50
            p10.blow_out(ab_well.top())

        p10.transfer(vol, ab_well, dest, new_tip='never')
        p10.blow_out(dest.top())
        ab[0] -= vol

    def ki67_helper(vol, src, dest):
        """This is a helper function that will check the value of the volume \
        bening transferred and will do the appropriate transfer. Finally, \
        it will update the volume as a return value.
        """
        src_vol = src[0]
        src_well = src[1]

        if vol > 0:
            if vol > src_vol:
                p1k.transfer(
                    src_vol, tube_rack[src_well], dest, new_tip='never')
                p1k.blow_out(dest.top())
                src[0] = 0
                vol -= src_vol
            else:
                p1k.transfer(
                    vol, tube_rack[src_well], dest, new_tip='never')
                p1k.blow_out(dest.top())
                src[0] -= vol
                vol = 0

        return vol

    def ki67_transfer(vol, dest):
        """This function that will use 'ki67_helper' (above) to make the the \
        source list based on the dictionary. This way, the dictionary will be \
        updated appropriately.
        """
        srcs = [volumes_dict['KI67_src'+str(i)] for i in range(1, 6)]

        x = vol
        # Make the transfers from the appropriate tubes
        for src in srcs:
            x = ki67_helper(x, src, dest)
        # Refills tube if there is still volume left after transfers
        while x > 0:
            protocol.pause('Please refill all KI67 source tubes. Tubes D3, E3, \
            F3, G3, and H3 should each have 2mL in them. After refilling, \
            please click RESUME.')
            for src in srcs:
                src[0] = 2000
            for src in srcs:
                x = ki67_helper(x, src, dest)

    # Antibody amount calculations
    ab_dilutions = [cd4_dil, cd8_dil, fox_dil, pdl1_dil, pan_dil, ki_dil]
    ab_vol = 150*(num_samps+n_cor)
    ab_needed = [ab_vol/dil for dil in ab_dilutions]
    dil_needed = [ab_vol - ab_n for ab_n in ab_needed]

    ab_tubes = tubes6.wells()[:len(ab_dilutions)]

    # AB transfer
    ab_list = ['CD4', 'CD8', 'FOXP3', 'PDL1', 'PANCK']

    for ab, vol, well in zip(ab_list, ab_needed, ab_tubes):
        pick_up(p10)
        ab_transfer(vol, ab, well)
        p10.drop_tip()

    # KI67 transfer
    pick_up(p1k)
    ki67_transfer(ab_needed[5], ab_tubes[5])
    p1k.drop_tip()

    # AB dilutent transfer
    for well, vol in zip(ab_tubes, dil_needed):
        ab_d_transfer(vol, well)

    # Antibodies done - now need to complete opals
    # opal amount calculations
    op_list = [ds_520, ds_570, ds_540, ds_620, ds_650, ds_690]
    op_total = [ab_vol*i for i in op_list]
    op_needed = [(num_samps+n_cor)*i for i in op_list]
    op_dil = [b-a for b, a in zip(op_total, op_needed)]
    # determine which tubes to use
    big_dil = sum(i > 6000 for i in op_total)
    if big_dil > 0:
        op_tubes = [w for w in big_tubes.columns()[0]+big_tubes.columns()[1]]
    else:
        op_tubes = tubes6.wells()[len(ab_dilutions):]
    # opal transfers
    opals = ['520', '570', '540', '620', '650', '690']

    for op, vol, well in zip(opals, op_needed, op_tubes):
        pick_up(p10)
        ab_transfer(vol, op, well)
        p10.drop_tip()

    # dilutent transfer
    for well, vol in zip(op_tubes, op_dil):
        amp_transfer(vol, well)

    # update dictionary
    volumes_dict['p10tip'][0] = tip10count
    volumes_dict['p1ktip'][0] = tip1kcount
    volumes_dict['ab_dil'][1] = str(ab_ht)
    volumes_dict['ab_dil'][0] = ab_vol
    volumes_dict['amp_dil'][1] = str(amp_ht)
    volumes_dict['amp_dil'][0] = amp_vol

    # write updated dictionary to CSV
    if not protocol.is_simulating():
        with open(file_path, 'w') as outfile:
            for key in volumes_dict:
                outfile.write("%s,%s,%s\n" % (key, volumes_dict[key][0],
                              volumes_dict[key][1]))
