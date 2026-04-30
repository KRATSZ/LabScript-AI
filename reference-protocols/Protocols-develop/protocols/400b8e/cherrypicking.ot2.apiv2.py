metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [pipette_type, pipette_mount, tip_type,
     tip_reuse, transfer_csv, tempdeck_slot, tempdeck_name,
     temp] = get_values(  # noqa: F821
        "pipette_type", "pipette_mount", "tip_type", "tip_reuse",
        "transfer_csv", "tempdeck_slot", "tempdeck_name", "temp")

    tiprack_map = {
        'p10_single': {
            'standard': 'opentrons_96_tiprack_10ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p50_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p300_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        },
        'p20_single_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p300_single_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single_gen2': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        }
    }

    # load labware and module
    if tempdeck_slot:
        tempdeck = ctx.load_module(tempdeck_name, tempdeck_slot)
        tempdeck.set_temperature(temp)

    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    block_inds = []
    for i, line in enumerate(transfer_info):
        if line[0].strip().lower() != 'pause':
            s_lw, s_slot, d_lw, d_slot = line[1:3] + line[5:7]
            for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
                if not int(slot) in ctx.loaded_labwares:
                    if not int(slot) in ctx.loaded_modules:
                        ctx.load_labware(lw.lower(), slot)
                    else:
                        ctx.loaded_modules[int(slot)].load_labware(lw.lower(),
                                                                   slot)

        else:
            block_inds.append(i)

    # load tipracks in remaining slots
    tiprack_type = tiprack_map[pipette_type][tip_type]
    tipracks = []
    for slot in range(1, 13):
        if int(slot) not in ctx.loaded_labwares \
                and int(slot) not in ctx.loaded_modules:
            tipracks.append(ctx.load_labware(tiprack_type, str(slot)))

    # setup blocks
    block_inds.insert(0, -1)
    block_inds.insert(len(block_inds), len(transfer_info))
    transfer_blocks = []
    for i in range(len(block_inds)-1):
        transfer_blocks.append(transfer_info[block_inds[i]+1:block_inds[i+1]])

    # load pipette
    pip = ctx.load_instrument(pipette_type, pipette_mount, tip_racks=tipracks)

    tip_count = 0
    tip_max = len(tipracks*96)

    def pick_up():
        nonlocal tip_count
        if tip_count == tip_max:
            ctx.pause('Please refill tipracks before resuming.')
            pip.reset_tipracks()
            tip_count = 0
        pip.pick_up_tip()
        tip_count += 1

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    pip.home()

    for i, block in enumerate(transfer_blocks):
        if tip_reuse == 'never':
            pick_up()

        # calculate time estimate based on 30s/transfer
        time_est_min = round(len(block)*30.0/60, 1)

        # find plate IDs
        id_dict = {}
        for line in block:
            id, _, slot = line[0:3]
            if id not in id_dict:
                id_dict[id] = slot
        comments = ', '.join(
            [f'plate {key} in slot {val}' for key, val in id_dict.items()])
        ctx.pause(f'Please load {comments}. This set of transfers will take \
approximately {time_est_min} minutes. Resume when loaded.')

        for line in block:
            _, s_slot, s_well, h, _, d_slot, d_well, vol = line[1:9]
            source = ctx.loaded_labwares[
                int(s_slot)].wells_by_name()[
                    parse_well(s_well)].bottom(float(h))
            dest = ctx.loaded_labwares[
                int(d_slot)].wells_by_name()[parse_well(d_well)]
            if tip_reuse == 'always':
                pick_up()
            pip.transfer(float(vol), source, dest, new_tip='never')
            if tip_reuse == 'always':
                pip.drop_tip()

        if pip.hw_pipette['has_tip']:
            pip.drop_tip()
