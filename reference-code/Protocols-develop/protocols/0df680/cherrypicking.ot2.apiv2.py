import csv
from datetime import datetime
from opentrons import protocol_api

metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.14'
}


def run(ctx):

    now = datetime.now()  # current date and time
    today = now.strftime('%Y%m%d')

    [input_csv] = get_values(  # noqa: F821
        'input_csv')

    p20 = ctx.load_instrument('p20_single_gen2', 'left')

    vol_pre_airgap = 2.0

    data = [
        [val.strip() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line.split(',')[0].strip()]

    def parse_well(well_str):
        return f'{well_str[0].upper()}{int(well_str[1:])}'

    def slow_withdraw(pip, well, delay_seconds=2.0):
        pip.default_speed /= 16
        if delay_seconds >= 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 16

    def pickup(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause('Replace the tips')
            pip.reset_tipracks()
            pip.pick_up_tip()

    lw_map_sources = {}
    lw_map_dests = {}
    output_data = []

    source_liq = ctx.define_liquid(
        'source', '', '#50D5FF')
    dest_liq = ctx.define_liquid(
        'destination', '', '#B925FF')

    # tipracks
    used_slots = []
    for line in data:
        slots = [int(line[4]), int(line[8])]
        for s in slots:
            if s not in used_slots:
                used_slots.append(s)

    tipracks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in [s for s in range(1, 12)]
        if slot not in used_slots]

    p20.tip_racks = tipracks20

    # transfers
    used_tempdeck = False
    for line in data:
        clone_id = line[1].upper()
        source_plate_id = line[2].upper()
        source_lw = line[3]
        source_slot = line[4]
        source_well = parse_well(line[5])
        source_h = float(line[6])
        dest_lw = line[7]
        dest_slot = line[8]
        dest_plate_id = line[9]
        dest_well = parse_well(line[10])
        vol = float(line[11])

        # load labware if needed
        if int(source_slot) not in ctx.loaded_labwares:
            s_plate = ctx.load_labware(
                source_lw, source_slot,
                f'source {source_plate_id}')
            [well.load_liquid(source_liq, volume=200)
             for well in s_plate.wells()]
        if int(dest_slot) not in ctx.loaded_labwares:
            if not used_tempdeck:
                tempdeck = ctx.load_module('temperature module gen2',
                                           dest_slot)
                d_plate = tempdeck.load_labware(
                    dest_lw, f'destination {dest_plate_id}')
                tempdeck.set_temperature(4)
                used_tempdeck = True
            else:
                d_plate = ctx.load_labware(
                    dest_lw, dest_slot, f'destination {dest_plate_id}')
            [well.load_liquid(dest_liq, volume=200)
             for well in d_plate.wells()]

        # check whether a deck refill is needed:
        # reset map if anything doesn't match
        if source_slot in lw_map_sources and lw_map_sources[
                source_slot] != source_plate_id:
            ctx.pause('Replace deck with next set of source plates before \
resuming.')
            lw_map_sources = {}
        if dest_slot in lw_map_dests and lw_map_dests[
                dest_slot] != dest_plate_id:
            ctx.pause('Replace deck with next set of dest plates before \
resuming.')
            lw_map_dests = {}

        # update map with new labware
        lw_map_sources[source_slot] = source_plate_id
        lw_map_dests[dest_slot] = dest_plate_id

        # perform transfer
        source = ctx.loaded_labwares[int(source_slot)].wells_by_name(
            )[source_well]
        dest = ctx.loaded_labwares[int(dest_slot)].wells_by_name(
            )[dest_well]
        pickup(p20)
        if vol_pre_airgap > 0:
            p20.aspirate(vol_pre_airgap, source.top())
        p20.aspirate(vol, source.bottom(source_h))
        slow_withdraw(p20, source)
        p20.dispense(p20.current_volume, dest)
        slow_withdraw(p20, dest)
        p20.drop_tip()

        # log data
        transfer_data = {
            'clone-id': clone_id,
            'source-plate-id': source_plate_id,
            'source-plate-well': source_well,
            'dest-plate-id': dest_plate_id,
            'dest-plate-well': dest_well,
        }
        output_data.append(transfer_data)

    # file writing
    if not ctx.is_simulating:
        output_path = f'/var/lib/jupyter/notebooks/{today}.csv'
        with open(output_path, 'w') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(
                ['cloneID', 'source plate ID', 'source plate well',
                 'destination plate ID', 'destination plate well'])
            for t_data in output_data:
                writer.writerow([t_data['clone-id'],
                                t_data['source-plate-id'],
                                t_data['source-plate-well'],
                                t_data['dest-plate-id']],
                                t_data['dest-plate-well'])
