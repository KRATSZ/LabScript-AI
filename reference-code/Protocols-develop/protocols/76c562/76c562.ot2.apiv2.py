import math

metadata = {
    'protocolName': 'Cherrypicking and Normalization',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.10'
}


def run(ctx):

    [left_pipette_type, right_pipette_type, left_pip_slot, right_pip_slot,
     left_pip_tip, right_pip_tip, d_csv1, s_csv, diluent_scheme,
     mix] = get_values(  # noqa: F821
        'left_pipette_type', 'right_pipette_type', 'left_pip_slot',
        'right_pip_slot', 'left_pip_tip', 'right_pip_tip', 'd_csv1', 's_csv',
        'diluent_scheme', 'mix')

    tiprack_map = {
        'p10_single': 'opentrons_96_filtertiprack_10ul',
        'p50_single': 'opentrons_96_filtertiprack_200ul',
        'p300_single_gen1': 'opentrons_96_filtertiprack_200ul',
        'p1000_single_gen1': 'opentrons_96_filtertiprack_1000ul',
        'p20_single_gen2': 'opentrons_96_filtertiprack_20ul',
        'p300_single_gen2': 'opentrons_96_filtertiprack_200ul',
        'p1000_single_gen2': 'opentrons_96_filtertiprack_1000ul'
    }

    # load labware
    transfer_info_d = [[val.strip().lower() for val in line.split(',')]
                       for line in d_csv1.splitlines()
                       if line.split(',')[0].strip()][1:]

    transfer_info_s = [[val.strip().lower() for val in line.split(',')]
                       for line in s_csv.splitlines()
                       if line.split(',')[0].strip()][1:]

    sides = ['left', 'right']
    pipettes = {
        'left': {},
        'right': {}
    }

    pipettes['left']['use-count'] = 0
    pipettes['right']['use-count'] = 0

    for line in transfer_info_d:
        s_lw, s_slot, d_lw, d_slot, pip = line[:2] + line[4:6] + [line[9]]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)
        pipettes[pip]['use-count'] += 1

    for line in transfer_info_s:
        s_lw, s_slot, d_lw, d_slot, pip = line[:2] + line[4:6] + [line[9]]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)
        pipettes[pip]['use-count'] += 1

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
    for i, (pip_type, side) in enumerate(
            zip([left_pipette_type, right_pipette_type], sides)):
        if pip_type:
            tiprack_type = tiprack_map[pip_type]
            tipracks = []
            if i == 0:
                proportion = pipettes[
                    side]['use-count']/(len(transfer_info_d) +
                                        len(transfer_info_s))
                # num_racks = math.ceil(num_avail_slots/num_pipettes)
                num_racks = math.ceil(num_avail_slots*proportion)
                slots = sorted_slots[:num_racks]
                if right_pipette_type and '11' in slots:
                    slots.remove('11')
                for slot in slots:
                    sorted_slots.remove(slot)
            else:
                slots = sorted_slots
            for slot in slots:
                tipracks.append(ctx.load_labware(tiprack_type, str(slot)))
            # load pipette
            pipettes[side]['instrument'] = ctx.load_instrument(
                pip_type, side, tip_racks=tipracks)

    tip_log = {}
    for mount in pipettes.keys():
        if 'instrument' in pipettes[mount]:
            pip = pipettes[mount]['instrument']
            if mount == 'left':
                start_slot = left_pip_slot
                start_tip_well = left_pip_tip
            else:
                start_slot = right_pip_slot
                start_tip_well = right_pip_tip
            allowable_slots = [rack.parent for rack in pip.tip_racks]
            if start_slot not in allowable_slots:
                raise Exception(f'Start Slot for {mount} pipette must be in \
    {allowable_slots}.')
            starting_tip = ctx.loaded_labwares[
                int(start_slot)].wells_by_name()[start_tip_well]
            if pip.type == 'single':
                tip_log[pip] = {
                    'tips': [
                        tip for rack in pip.tip_racks for tip in rack.wells()],
                    'max': len(pip.tip_racks*96)}
            else:
                tip_log[pip] = {
                    'tips': [
                        tip
                        for rack in pip.tip_racks for tip in rack.rows()[0]],
                    'max': len(pip.tip_racks*96)}
            tip_log[pip]['count'] = tip_log[pip]['tips'].index(starting_tip)

    def pick_up(pip):
        if tip_log[pip]['count'] == tip_log[pip]['max']:
            ctx.pause('Please refill {}µl tipracks before \
resuming.'.format(pip.max_volume))
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
        tip_log[pip]['count'] += 1

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    ctx.comment('Transferring diluent to wells based on Dilutant CSV...')
    last_dil = None
    for line in transfer_info_d:
        [_, s_slot, s_well, asp_h, _, d_slot, d_well, disp_h, vol,
         pip] = line[:10]
        pipette = pipettes[pip.lower()]['instrument']
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)]
        if pipette.has_tip and source != last_dil:
            pipette.drop_tip()
        if diluent_scheme == 'always' or not pipette.has_tip:
            pick_up(pipette)
        last_dil = source
        dest = ctx.loaded_labwares[
            int(d_slot)].wells_by_name()[parse_well(d_well)]
        if not pipette.has_tip:
            pick_up(pipette)
        num_trans = math.ceil(
            float(vol)/pipette.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = float(vol)/num_trans
        for _ in range(num_trans):
            pipette.transfer(vol_per_trans, source.bottom(float(asp_h)),
                             dest.bottom(float(disp_h)), new_tip='never')
            pipette.blow_out(dest.bottom(float(disp_h)))
        if diluent_scheme == 'always':
            pipette.drop_tip()
    for mount in pipettes.keys():
        if 'instrument' in pipettes[mount]:
            pip = pipettes[mount]['instrument']
            if pip.has_tip:
                pip.drop_tip()

    ctx.comment('Transferring DNA to wells based on Sample CSV...')
    for line in transfer_info_s:
        [_, s_slot, s_well, asp_h, _, d_slot, d_well, disp_h, vol,
         pip] = line[:10]
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)]
        dest = ctx.loaded_labwares[
            int(d_slot)].wells_by_name()[parse_well(d_well)]

        pipette = pipettes[pip.lower()]['instrument']
        pick_up(pipette)
        num_trans = math.ceil(
            float(vol)/pipette.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = float(vol)/num_trans
        for _ in range(num_trans):
            pipette.transfer(vol_per_trans, source.bottom(float(asp_h)),
                             dest.bottom(float(disp_h)), new_tip='never')
            pipette.blow_out(dest.bottom(float(disp_h)))
        if mix:
            max = pipette.tip_racks[0].wells()[0].max_volume
            if float(vol) < max:
                mix_vol = float(vol)
            else:
                mix_vol = max
            pipette.mix(3, mix_vol, dest.bottom(float(disp_h)))
        pipette.blow_out()
        pipette.drop_tip()

    ctx.comment('Protocol is complete.')
