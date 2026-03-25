import json
import os

# metadata
metadata = {
    'protocolName': 'Manual Cleave, ACN + Elution (Off-Deck Vacuum)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [occupied_well_csv1, occupied_well_csv2, occupied_well_csv3, reagent_scan,
     reagent_slot_scan, elution_scan, elution_slot_scan, reagent_transfer_vol,
     elution_transfer_vol, m300_mount, p300_mount,
     tip_track] = get_values(  # noqa: F821
        'occupied_well_csv1', 'occupied_well_csv2', 'occupied_well_csv3',
        'reagent_scan', 'reagent_slot_scan', 'elution_scan',
        'elution_slot_scan', 'reagent_transfer_vol', 'elution_transfer_vol',
        'm300_mount', 'p300_mount', 'tip_track')

    # load labware
    racks = [
        ctx.load_labware('custom_96_tuberack_500ul', f'{slot}', f'plate {i+1}')
        for i, slot in enumerate(['4', '5', '6'])]
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                         '300ul tiprack')
        for slot in ['10', '11']]

    reagent_map = {
        'WAT': {
            'slot': '9',
            'tips': tips300[1].columns()[5:6],
            'flow-rate-asp': 100,
            'flow-rate-disp': 100,
            'flow-rate-blow-out': 100,
            'blow-out': True,
            'dispense-delay': 0,
            'drop-tip': False
        },
        'ACN': {
            'slot': '8',
            'tips': tips300[1].columns()[:1],
            'volume': 200,
            'flow-rate-asp': 100,
            'flow-rate-disp': 100,
            'flow-rate-blow-out': 100,
            'blow-out': True,
            'dispense-delay': 0,
            'drop-tip': False
        }
    }

    # check for barcode scan
    reagent_scan_type = reagent_scan.split('_')[-1].upper().strip()
    reagent_slot_scan_type = reagent_slot_scan.upper().strip()
    elution_scan_type = elution_scan.split('_')[-1].upper().strip()
    elution_slot_scan_type = elution_slot_scan.upper().strip()
    if reagent_scan_type == 'REPLACE WITH SCAN' \
            or reagent_slot_scan_type == 'REPLACE WITH SCAN':
        pass
    elif elution_scan_type == 'REPLACE WITH SCAN' \
            or elution_slot_scan_type == 'REPLACE WITH SCAN':
        pass
    else:
        if not reagent_scan_type:
            raise Exception('Rescan reagent (empty reagent scan)')
        if not reagent_slot_scan_type:
            raise Exception('Rescan reagent slot (empty slot scan)')
        if not reagent_scan_type == reagent_slot_scan_type[:3]:
            raise Exception(f'Reagent mismatch: {reagent_scan_type} in slot \
    {reagent_slot_scan_type}')
        if reagent_slot_scan_type not in reagent_map.keys():
            raise Exception(f'Invalid reagent slot scan: \
{reagent_slot_scan_type}')

        if not elution_scan:
            raise Exception('Rescan elution (empty elution scan)')
        if not elution_slot_scan_type:
            raise Exception('Rescan elution slot (empty elution slot scan)')
        if not elution_scan_type == elution_slot_scan_type[:3]:
            raise Exception(f'Elution mismatch: {elution_scan_type} in slot \
{elution_slot_scan_type}')
        if elution_slot_scan_type not in reagent_map.keys():
            raise Exception(f'Invalid slot scan: {elution_slot_scan_type}')

        reagent_type = reagent_slot_scan_type
        reagent = ctx.load_labware(
            'test_1_reservoir_300000ul', reagent_map[reagent_type]['slot'],
            reagent_type).wells()[0]
        elution_type = elution_slot_scan_type
        elution = ctx.load_labware(
            'test_1_reservoir_300000ul', reagent_map[elution_type]['slot'],
            elution_type).wells()[0]

        def all_tips_full():
            for rack in tips300:
                for well in rack.wells():
                    well.has_tip = True

        folder_path = '/data/manual_cleave'
        tip_file_path = folder_path + '/tip_log.json'
        if tip_track and not ctx.is_simulating():
            if os.path.isfile(tip_file_path):
                with open(tip_file_path) as json_file:
                    tip_data = json.load(json_file)
                    for slot in tip_data.keys():
                        for well, tip_bool in tip_data[slot].items():
                            ctx.loaded_labwares[int(slot)].wells_by_name()[
                                well].has_tip = tip_bool
            else:
                all_tips_full()
        else:
            all_tips_full()

        # load pipette
        m300 = ctx.load_instrument(
            'p300_multi_gen2', m300_mount, tip_racks=tips300)
        p300 = ctx.load_instrument(
            'p300_single_gen2', p300_mount, tip_racks=tips300)

        # samples and reagents
        def slide_window(num_tips, col):
            num_slides = 9 - num_tips
            for slide in range(num_slides):
                window_start_index = 8 + -1*num_tips - slide
                window = col[window_start_index:(window_start_index+num_tips)]
                window_full = True
                for tip in window:
                    if not tip.has_tip:
                        window_full = False
                if window_full:
                    return window[0]
            return False

        def scan_racks(num_tips, reagent_type):
            all_columns = reagent_map[reagent_type]['tips']
            for col in all_columns:
                pick_up_loc = slide_window(num_tips, col)
                if pick_up_loc:
                    return pick_up_loc
            return False

        per_tip_pickup_current = .1

        def pick_up(num_tips, reagent_type):
            if not 1 <= num_tips <= 8:
                raise Exception(f'INVALID NUMBER OF TIPS: {num_tips}.')
            if num_tips > 1:
                pip = m300
                pick_up_current = num_tips*per_tip_pickup_current
                ctx._implementation._hw_manager.hardware._attached_instruments[
                    pip._implementation.get_mount()].update_config_item(
                        'pick_up_current', pick_up_current)
            else:
                pip = p300
            scan_result = scan_racks(num_tips, reagent_type)
            if scan_result:
                pip.pick_up_tip(scan_result)
            else:
                ctx.pause('REFILL TIPRACKS BEFORE RESUMING.')
                [rack.reset() for rack in tips300]
                scan_result = scan_racks(num_tips, reagent_type)
                pip.pick_up_tip(scan_result)
            return scan_result, pip

        def return_tip(pip, tip_loc, chunk_len, reagent_type):
            pip.drop_tip(tip_loc)
            all_tips = [
                well
                for col in reagent_map[reagent_type]['tips'] for well in col]
            tip_ind = all_tips.index(tip_loc)
            for tip in all_tips[tip_ind:tip_ind+chunk_len]:
                tip.has_tip = True

        # parse wells into chunks
        chunk_map = {num: [] for num in range(1, 9)}
        for csv, rack in zip(
                [occupied_well_csv1, occupied_well_csv2, occupied_well_csv3],
                racks):
            occupied_wells = [
                rack.wells_by_name()[line.upper()]
                for line in csv.splitlines() if line]
            for col in rack.columns():
                running = None
                chunk_length = 0
                for well in col[::-1]:
                    if well in occupied_wells:
                        running = well
                        chunk_length += 1
                    else:
                        if running:
                            chunk_map[chunk_length].append(running)
                        running = None
                        chunk_length = 0
                if running:
                    chunk_map[chunk_length].append(running)

        num_chunks = len(
            [key for key, vals in chunk_map.items()
             if len(vals) > 0])
        accessed = 0
        num_centrifugations = 4

        for num_tips, dests in chunk_map.items():
            if len(dests) > 0:
                accessed += 1
                pick_up_loc, pip = pick_up(num_tips, reagent_type)
                for dest in dests:
                    pip.aspirate(reagent_transfer_vol, reagent.bottom(1))
                    pip.dispense(reagent_transfer_vol, dest.top(-1))
                    ctx.delay(seconds=reagent_map[
                        reagent_type]['dispense-delay'])
                    if reagent_map[reagent_type]['blow-out']:
                        pip.blow_out(dest.top(-1))

                if elution == num_centrifugations - 1 and \
                        reagent_map[reagent_type]['drop-tip'] and \
                        accessed == num_chunks:
                    pip.drop_tip()
                else:
                    # return tip and reset has_tip attribute
                    return_tip(pip, pick_up_loc, num_tips, reagent_type)

        ctx.pause('Vacuum ACN before replacing plates and resuming.')

        for elution_ind in range(num_centrifugations):
            for num_tips, dests in chunk_map.items():
                if len(dests) > 0:
                    accessed += 1
                    pick_up_loc, pip = pick_up(num_tips, elution_type)
                    for dest in dests:
                        pip.aspirate(elution_transfer_vol, elution.bottom(1))
                        pip.dispense(elution_transfer_vol, dest.top(-1))
                        ctx.delay(seconds=reagent_map[
                            elution_type]['dispense-delay'])
                        if reagent_map[elution_type]['blow-out']:
                            pip.blow_out(dest.top(-1))

                    if elution_ind == num_centrifugations - 1 and \
                            reagent_map[elution_type]['drop-tip'] and \
                            accessed == num_chunks:
                        pip.drop_tip()
                    else:
                        # return tip and reset has_tip attribute
                        return_tip(pip, pick_up_loc, num_tips, elution_type)
            func = ctx.pause if elution_ind < num_centrifugations - 1 \
                else ctx.comment
            func(msg='Centrifuge all plates. Replace and resume when \
finished.')

        # track final used tip
        # void partially full tip column
        for tiprack in tips300:
            for col in tiprack.columns():
                for well in col:
                    if not well.has_tip:
                        for well in col:
                            well.has_tip = False
                        break
        tip_data = {
            str(rack.parent):
                {well.display_name.split(' ')[0]: well.has_tip
                 for well in rack.wells()}
            for rack in tips300
        }
        if not ctx.is_simulating():
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            with open(tip_file_path, 'w') as outfile:
                json.dump(tip_data, outfile)

        ctx._implementation._hw_manager.hardware._attached_instruments[
            m300._implementation.get_mount()].update_config_item(
                'pick_up_current', 1.0)

    for c in ctx.commands():
        print(c)
