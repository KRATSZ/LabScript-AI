metadata = {
    'protocolName': 'Guanidine and PBS Transfer with CSV',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
    }


def run(protocol):
    [v_csv, p10_mnt, p50_mnt] = get_values(  # noqa: F821
        'v_csv', 'p10_mnt', 'p50_mnt')

    # create pipettes and labware
    tips10 = protocol.load_labware(
        'opentrons_96_tiprack_10ul',
        '1',
        '10uL Tips')
    tips50 = protocol.load_labware(
        'opentrons_96_tiprack_300ul',
        '4',
        '50uL Tips')

    trough = protocol.load_labware(
        'usascientific_12_reservoir_22ml',
        '2',
        '12-Channel Trough')
    guan = trough['A1']
    pbs = trough['A2']

    plate = protocol.load_labware(
        'corning_384_wellplate_112ul_flat',
        '3',
        '384-Well Plate')

    pip10 = protocol.load_instrument('p10_single', p10_mnt, tip_racks=[tips10])
    pip50 = protocol.load_instrument('p50_single', p50_mnt, tip_racks=[tips50])

    data_dict = {}  # creates dictionary of wells as key and floats of volumes
    for row in v_csv.strip().splitlines():
        if row:
            row = row.split(',')
            if row[0].lower() == 'well':
                pass
            else:
                data_dict[row[0].strip()] = [float(row[1]), float(row[2])]

    # transfer guanidine
    for k in data_dict:
        vol = data_dict[k][0]
        pip = pip10 if vol < 10 else pip50
        if not pip.hw_pipette['has_tip']:
            pip.pick_up_tip()
        pip.transfer(vol, guan, plate[k], new_tip='never')

    if pip10.hw_pipette['has_tip']:
        pip10.drop_tip()
    if pip50.hw_pipette['has_tip']:
        pip50.drop_tip()

    # transfer PBS/buffer
    for k in data_dict:
        vol = data_dict[k][1]
        if vol < 10:
            pip = pip10
            vol_mix = 8
        else:
            pip = pip50
            vol_mix = 45
        pip.pick_up_tip()
        pip.transfer(vol, pbs, plate[k], new_tip='never')
        pip.mix(5, vol_mix, plate[k])
        pip.drop_tip()
