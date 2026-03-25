import math

metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [transfer_csv, left_pipette_type, right_pipette_type, tip_type,
     dest_lw_def, dest_slot] = get_values(  # noqa: F821
        'transfer_csv', 'left_pipette_type', 'right_pipette_type', 'tip_type',
        'dest_lw_def', 'dest_slot')

    # labware map
    labware_map = {
        '4x6 2ml screw true': {
            'labware': 'opentrons_24_tuberack_2000ul',
            'top': 86.5,
            'depth': 42.3
        },
        '4x6 2ml screw false': {
            'labware': 'opentrons_24_tuberack_2000ul',
            'top': 86.5,
            'depth': 42.8
        },
        '4x6 1.5ml snap': {
            'labware': 'opentrons_24_tuberack_2000ul',
            'top': 81.55,
            'depth': 38.5
        },
        '4x6 1.5ml screw': {
            'labware': 'opentrons_24_tuberack_2000ul',
            'top': 86.5,
            'depth': 42.8
        },
        '8x12 strip': {
            'labware': 'thermoscientificmatrix_96_tuberack_1000ul',
            'top': 33.04,
            'depth': 20.1
        },
        '8x12 1ml plug': {
            'labware': 'thermoscientificmatrix_96_tuberack_1000ul',
            'top': 35.5,
            'depth': 32.3
        },
        '8x12 0.5ml snap': {
            'labware': 'thermoscientificmatrix_96_tuberack_1000ul',
            'top': 30.37,
            'depth': 29.4
        },
        '96 wellplate': {
            'labware': 'sorenson_96_wellplate_350ul',
            'top': 23.17,
            'depth': 20.34
        },
        '384 wellplate': {
            'labware': 'eppendorf_384_wellplate_45ul',
            'top': 10.25,
            'depth': 9
        }
    }

    tiprack_map = {
        'p10': {
            'standard': 'opentrons_96_tiprack_10ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p50': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p300': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p20': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p1000': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        }
    }

    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[1:3] + line[5:7]
        lw_loadname = labware_map[s_lw]['labware']
        if not int(s_slot) in ctx.loaded_labwares:
            ctx.load_labware(lw_loadname.lower(), s_slot)
    dest_lw = ctx.load_labware(dest_lw_def, dest_slot, 'destination labware')

    # load tipracks in remaining slots
    slot_order = {
        '10': 0,
        '11': 1,
        '7': 2,
        '8': 3,
        '9': 4,
        '4': 5,
        '5': 6,
        '6': 7,
        '1': 8,
        '2': 9,
        '3': 10
    }

    avail_slots = [str(slot) for slot in range(1, 13)
                   if slot not in ctx.loaded_labwares]
    sorted_slots_tup = sorted(slot_order.items(), key=lambda x: x[1])
    sorted_slots = [
        slot_tup[0] for slot_tup in sorted_slots_tup
        if slot_tup[0] in avail_slots]
    num_avail_slots = len(avail_slots)
    num_pipettes = len([pip for pip in [left_pipette_type, right_pipette_type]
                        if pip])
    if num_pipettes == 0:
        raise Exception('Must select at least 1 pipette.')
    pipettes = {
        'left': None,
        'right': None
    }
    for i, (pip_type, side) in enumerate(
            zip([left_pipette_type, right_pipette_type], pipettes.keys())):
        if pip_type:
            tiprack_type = tiprack_map[pip_type.split('_')[0]][tip_type]
            tipracks = []
            if i == 0:
                num_racks = math.ceil(num_avail_slots/num_pipettes)
                slots = sorted_slots[:num_racks]
                for slot in slots:
                    sorted_slots.remove(slot)
            else:
                slots = sorted_slots
            for slot in slots:
                tipracks.append(ctx.load_labware(tiprack_type, str(slot)))
        # load pipette
        pipettes[side] = ctx.load_instrument(pip_type, side,
                                             tip_racks=tipracks)

    tip_log = {}
    for mount, pip in pipettes.items():
        if pip.type == 'single':
            tip_log[pip] = {
                'tips': [
                    tip for rack in pip.tip_racks for tip in rack.wells()],
                'max': len(pip.tip_racks*96)}
        else:
            tip_log[pip] = {
                'tips': [
                    tip for rack in pip.tip_racks for tip in rack.rows()[0]],
                'max': len(pip.tip_racks*96)}
        tip_log[pip]['count'] = 0

    def pick_up(pip):
        if tip_log[pip]['count'] == tip_log[pip]['max']:
            ctx.pause(f'Please refill {pip.max_volume}µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
        tip_log[pip]['count'] += 1

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    for line in transfer_info:
        [pip, s_lw_key, s_slot, s_well, h, d_well, vol] = line[:7]
        source_lw = ctx.loaded_labwares[int(s_slot)]
        dest = dest_lw.wells_by_name()[parse_well(d_well)]
        s_top_offset = labware_map[s_lw_key]['top'] - source_lw.highest_z - \
            labware_map[s_lw_key]['depth'] + float(h)
        source = source_lw.wells_by_name()[parse_well(s_well)].top(
            s_top_offset)
        pipette = pipettes[pip]
        pick_up(pipette)
        pipette.transfer(float(vol), source, dest, new_tip='never')
        pipette.drop_tip()
