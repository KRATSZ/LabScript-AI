from itertools import zip_longest
import math

# metadata
metadata = {
    'protocolName': 'Saliva 3:1|2:1 pooling protocol',
    'author': 'Steve Plonk <protocols@opentrons.com>',
    'description': 'Pool 96 -15mL patients into 32 -15mL pools',
    'apiLevel': '2.9'
}


def run(ctx):
    # bring in constant values used throughout the protocol
    [sample_rows, sample_columns, sample_number, pool_size, pool_rows,
     pool_columns, sample_slots, pool_slots] = get_values(  # noqa: F821
            'sample_rows', 'sample_columns', 'sample_number', 'pool_size',
            'pool_rows', 'pool_columns', 'sample_slots', 'pool_slots')

    # pipette and tip box setup
    tips_1000 = ctx.load_labware(
        'opentrons_96_filtertiprack_1000ul', '11')
    right_pipette = ctx.load_instrument(
        'p1000_single_gen2', 'right', tip_racks=[tips_1000])
    left_pipette = ctx.load_instrument(
        'p1000_single_gen2', 'left', tip_racks=[tips_1000])

    # calculate the number of sample_racks needed
    sample_racks = math.ceil(sample_number / (sample_rows*sample_columns))

    # construct sample rack names (example 'Patients 1-15') and load labware
    first_sample = [
        i*sample_rows*sample_columns + 1 for i in range(sample_racks)]
    last_sample = [
        value + 14 if value + 14 <=
        sample_number else sample_number for value in first_sample]
    [*patient_samples] = [ctx.load_labware(
        'opentrons_15_tuberack_falcon_15ml_conical',
        str(slot), plate_name) for slot, plate_name in zip(
        sample_slots.split(","),
        ['Patients ' + str(first_sample[i]) + '-' +
            str(last_sample[i]) for i in range(sample_racks)])]

    # determine number of pools and pool racks
    pool_number = math.ceil(sample_number / int(pool_size))
    if pool_size == "2":
        pool_rack_capacity = pool_rows*pool_columns
        if pool_number <= 3*pool_rack_capacity:
            pool_racks = math.ceil(pool_number / pool_rack_capacity)
        else:
            pool_racks = math.floor(pool_number / pool_rack_capacity)
    elif pool_size == "3":
        pool_rack_capacity = 2*pool_columns
        if pool_number <= pool_rack_capacity:
            pool_racks = 1
        elif pool_number <= 2*pool_rack_capacity:
            pool_racks = 2
        else:
            pool_racks = 3

    # construct names (example 'Pools 1-10', 'Pools 1-15') and load pool racks
    first_pool = [i*pool_rack_capacity + 1 for i in range(pool_racks)]

    if pool_size == "2":
        last_pool = [value + (pool_rack_capacity - 1) if not (
            value + (pool_rack_capacity - 1) >
            pool_number) else pool_number for value in first_pool]
    elif pool_size == "3":
        last_pool = [value + (pool_rack_capacity - 1) if not (
            pool_number - (value + (pool_rack_capacity - 1)) <
            pool_rack_capacity or value + (pool_rack_capacity - 1) >
            pool_number) else pool_number for value in first_pool]

    [*pools] = [ctx.load_labware(
        'opentrons_15_tuberack_falcon_15ml_conical',
        str(slot), plate_name) for slot, plate_name in zip(
        pool_slots.split(","),
        ['Pools ' + str(first_pool[i]) + '-' + str(
            last_pool[i]) for i in range(pool_racks)])]

    # construct references to pool locations in pool fill order
    pool_rows = []
    if pool_size == "2":
        for pool in pools:
            for row in pool.rows():
                pool_rows.append(row)
        if pool_number > 3*pool_rack_capacity:
            pool_rows.append(patient_samples[6].columns()[4])
    elif pool_size == "3":
        for j, pool in enumerate(pools, start=1):
            for k, row in enumerate(pool.rows(), start=1):
                if not k == 2:
                    new_row = row
                    pool_rows.append(new_row)
            for k, row in enumerate(pool.rows(), start=1):
                if (k == 2 and j == 3):
                    new_row = row
                    pool_rows.append(new_row)

    pool_wells = [location for pool_row in pool_rows for location in pool_row]

    if pool_size == "2":
        pool_dispenses = [
            pool_well for pool_well in pool_wells for i in range(
             int(pool_size))]

    # list wells for transfer steps (L asp, R asp, L disp, R disp)
    transfer_count = 0
    for index, rack in enumerate(patient_samples):
        if pool_size == "2":
            dispense_locations = [
                pool_dispense for pool_dispense in pool_dispenses[
                    index*pool_rack_capacity:(index + 1)*pool_rack_capacity]]
        elif pool_size == "3":
            dispense_locations = [
                pool_well for pool_well in pool_wells[
                    index*pool_columns:(index+1)*pool_columns
                    ] for i in range(3)]
        stop_index = (
         lambda transfer_count: len(
          rack.wells()) if sample_number - transfer_count >= len(
          rack.wells()) else sample_number - transfer_count)(transfer_count)
        transfers = zip_longest(
            [rack.wells()[i] for i in range(0, stop_index, 2)],
            [rack.wells()[i] for i in range(1, stop_index, 2)],
            [dispense_locations[
                i] for i in range(0, stop_index, 2)],
            [dispense_locations[
                i] for i in range(1, stop_index, 2)])

        # transfer steps
        for asp_l, asp_r, disp_l, disp_r in list(transfers):
            left_pipette.pick_up_tip()
            if asp_r and transfer_count < sample_number - 1:
                right_pipette.pick_up_tip()
            left_pipette.aspirate(500, asp_l)
            if asp_r and transfer_count < sample_number - 1:
                right_pipette.aspirate(500, asp_r)
            left_pipette.dispense(500, disp_l)
            transfer_count += 1
            if disp_r and transfer_count < sample_number:
                right_pipette.move_to(disp_r.top(10))
                right_pipette.dispense(500, disp_r)
                transfer_count += 1
            if asp_r:
                left_pipette.drop_tip()
                right_pipette.drop_tip()
            else:
                left_pipette.drop_tip()
