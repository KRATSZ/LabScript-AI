from opentrons.types import Point
import os
import math
import json

metadata = {
    'title': 'NGS Library Prep',
    'author': 'Nick Diehl <ndiehl@opentrons.com',
    'apiLevel': '2.11'
}


def run(ctx):

    [sample_csv, perform_normalization, pipette_p20, pipette_p300, mount_p20,
     mount_p300, lw_tiprack300, tip_track] = get_values(  # noqa: F821
        'sample_csv', 'perform_normalization', 'pipette_p20', 'pipette_p300',
        'mount_p20', 'mount_p300', 'lw_tiprack300', 'tip_track')

    sample_info = [
        [int(val) for val in line.split(',')[:2]]
        for line in sample_csv.splitlines()[1:]
        if line and line.split(',')[0].strip()]
    sample_map = {
        line[0]: line[1]
        for line in sample_info
    }
    max_subsamples = max(sample_map.values())
    num_samples = len(sample_info)
    subsample_list = [sample_map[key] for key in sorted(sample_map.keys())]

    if num_samples * max_subsamples * 2 > 96:
        raise Exception(f'Invalid number of samples ({num_samples}) and \
max subsamples ({max_subsamples}). Exceeds plate capacity.')

    # labware
    sample_plate = ctx.load_labware('agilent_96_wellplate_200ul', '1',
                                    'sample plate')
    dilution_plate = ctx.load_labware('agilent_96_wellplate_200ul', '2',
                                      'dilution plate')
    pcr1_plate = ctx.load_labware('agilent_96_wellplate_200ul', '3',
                                  'PCR 1 plate')
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '4')]
    tipracks300 = [ctx.load_labware(lw_tiprack300, '5')]
    normalization_plate = ctx.load_labware('sequalprep_96_wellplate_200ul',
                                           '6', 'normalization plate')
    pcr2_plate = ctx.load_labware('agilent_96_wellplate_200ul', '9',
                                  'PCR 2 plate')
    tuberack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '7',
        'tuberack 1')
    tuberack2 = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '8',
        'tuberack 2')

    # pipettes
    p20 = ctx.load_instrument(pipette_p20, mount_p20, tip_racks=tipracks20)
    p300 = ctx.load_instrument(pipette_p300, mount_p300, tip_racks=tipracks300)

    # reagents
    samples_single = sample_plate.wells()[:num_samples]
    water, mm1, reverse_primer1, reverse_primer2 = tuberack2.columns()[0][:4]

    # read tip data
    tip_log = None
    if not ctx.is_simulating():
        # folder_path = 'protocols/69486f/supplements'
        # tip_file_path = folder_path + '/tip_log.json'
        folder_path = '/data/ngs'
        tip_file_path = folder_path + '/tip_log.json'
        if tip_track and not ctx.is_simulating():
            if os.path.isfile(tip_file_path):
                with open(tip_file_path) as json_file:
                    tip_log = json.load(json_file)

    # flip has_tip booleans based on tip log if it exists
    if tip_log:
        for slot, well_map in tip_log.items():
            tiprack = ctx.loaded_labwares()[int(slot)]
            for well_name, tip_val in well_map.items():
                tiprack.wells_by_name()[well_name].has_tip = tip_val

    def pick_up(pip=p20, channels=p20.channels):
        def look():
            # iterate and look for required number of consecutive tips
            for rack in pip.tip_racks:
                for col in rack.columns():
                    counter = 0
                    for well in col[::-1]:
                        if well.has_tip:
                            counter += 1
                        else:
                            counter = 0
                        if counter == channels:
                            pip.pick_up_tip(well)
                            return True
            return False

        eval_pickup = look()
        if eval_pickup:
            return
        else:
            # refill rack if no tips available
            ctx.pause(f'Refill {pip} tipracks before resuming.')
            pip.reset_tipracks()
            look()

    """ DILUTION """

    rows_per_sample = 2 if max_subsamples > 6 else 1
    if p20.type == 'multi' and rows_per_sample == 1:  # only if samples in col
        sources, num_pickups = [
            sample_plate.rows()[0][0] for _ in range(max_subsamples)], \
            num_samples
        source_sets = [
            [sample_plate.rows()[0][i]] for i in range(max_subsamples)]
        dilution_sets = [
            [dilution_plate.rows()[0][i]] for i in range(max_subsamples)]
    else:
        sources, num_pickups = samples_single, 1
        sets = []
        for i in range(num_samples):
            rows_flat = [
                well for row in dilution_plate.rows()[
                    i*rows_per_sample:(i+1)*rows_per_sample]
                for well in row]
            sets.append(rows_flat)
        dilution_sets = [
            set[:num_subsamples]
            for set, num_subsamples in zip(sets, subsample_list)]
        source_sets = [
            [sample_plate.wells()[dilution_plate.wells().index(well)]
             for well in set]
            for set in dilution_sets]

    # pre-add water
    sets = []
    for i in range(num_samples):
        rows_flat = [
            well for row in dilution_plate.rows()[
                i*rows_per_sample:(i+1)*rows_per_sample]
            for well in row]
        sets.append(rows_flat)
    dests_water_all = [
        well for set, num_subsamples in zip(sets, subsample_list)
        for well in set[:num_subsamples]]

    vol_water = 9
    pick_up(p20, 1)
    for d in dests_water_all:
        p20.aspirate(vol_water, water)
        p20.dispense(vol_water, d.bottom(2))
        # touch at half radius
        p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
    p20.drop_tip()

    # add samples to dilute
    vol_sample = 1
    for source_set, dest_set in zip(source_sets, dilution_sets):
        for s, d in zip(source_set, dest_set):
            pick_up(p20, num_pickups)
            p20.aspirate(vol_sample, s)
            p20.dispense(vol_sample, d.bottom(2))
            p20.mix(5, 8, d.bottom(2), rate=2.0)
            # touch at half radius
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
            p20.drop_tip()

    """ PCR1 PREP """

    # prepare PCR1 mastermixes
    num_samples_mm_creation = num_samples*2+2+1  # accounts for overage
    pcr1_map = [
        {
            'forward-primer-tube': primer_well,
            'creation-tube': creation_well,
            'volume': 0.1*num_samples_mm_creation
        }
        for creation_well, primer_well in zip(
            tuberack.wells()[:max_subsamples],
            # use max 5 primers. loop back around for subsamples 6-8
            [tuberack.wells()[8+(i % 5)] for i in range(max_subsamples)])
    ]

    # add all constant reagents to each mix tube
    vol_pcr_mm = 10*num_samples_mm_creation
    vol_reverse_primer_mm = 0.1*num_samples_mm_creation
    vol_water_mm = 8.8*num_samples_mm_creation
    for reagent, vol in zip(
            [mm1, reverse_primer1, water],
            [vol_pcr_mm, vol_reverse_primer_mm, vol_water_mm]):
        pip = p300 if vol > 20 else p20
        tip_capacity = pip.tip_racks[0].wells()[0].max_volume
        num_transfers = math.ceil(vol/tip_capacity)
        vol_per_transfer = vol/num_transfers
        pick_up(pip, 1)
        for item in pcr1_map:
            mix_dest = item['creation-tube']
            for _ in range(num_transfers):
                pip.aspirate(vol_per_transfer, reagent)
                pip.dispense(vol_per_transfer, mix_dest.bottom(5))
        pip.drop_tip()

    # add unique forward primers to mix and homogenize
    vol_forward_primer_mm = 0.1*num_samples_mm_creation
    pip = p300 if vol_forward_primer_mm > 20 else p20
    tip_capacity = pip.tip_racks[0].wells()[0].max_volume
    num_transfers = math.ceil(vol_forward_primer_mm/tip_capacity)
    vol_per_transfer = vol_forward_primer_mm/num_transfers
    for item in pcr1_map:
        pick_up(pip, 1)
        primer = item['forward-primer-tube']
        mix_dest = item['creation-tube']
        for _ in range(num_transfers):
            pip.aspirate(vol_per_transfer, primer)
            pip.dispense(vol_per_transfer, mix_dest.bottom(5))
        pip.mix(10, 20, mix_dest.bottom(5), rate=2.0)
        pip.drop_tip()

    # pre-transfer mix to wellplate
    vol_mm_total = 19
    pcr1_mix_sources = [item['creation-tube'] for item in pcr1_map]

    sets = []
    for i in range(num_samples):
        rows_flat = [
            well for row in pcr1_plate.rows()[
                i*rows_per_sample:(i+1)*rows_per_sample]
            for well in row]
        sets.append(rows_flat)

    if max_subsamples <= 4:
        locs_ntc = pcr1_plate.columns()[-1][:2*max_subsamples:2]
    else:
        locs_ntc = pcr1_plate.columns()[-1][:2*max_subsamples]

    pcr1_mix_dest_sets = []
    for i in range(max_subsamples):
        temp = []
        for num_subsamples, set in zip(subsample_list, sets):
            if num_subsamples >= i+1:
                wells = set[i*2:(i+1)*2]
                for well in wells:
                    temp.append(well)
        temp.append(locs_ntc[i])
        pcr1_mix_dest_sets.append(temp)

    for source, dest_set in zip(pcr1_mix_sources, pcr1_mix_dest_sets):
        pick_up(p20, 1)
        for d in dest_set:
            p20.aspirate(vol_mm_total, source)
            p20.dispense(vol_mm_total, d.bottom(2))
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
        p20.drop_tip()

    # add DNA template to mix
    pcr1_sample_sets = []
    for set, num_subsamples in zip(sets, subsample_list):
        for i in range(num_subsamples):
            wells = set[i*2:(i+1)*2]
            pcr1_sample_sets.append(wells)
    sources = dests_water_all

    vol_template = 1
    for source, dest_set in zip(sources, pcr1_sample_sets):
        pick_up(p20, num_pickups)
        for d in dest_set:
            p20.aspirate(vol_template, source)
            p20.dispense(vol_template, d.bottom(2))
            p20.mix(1, 10, d.bottom(2), rate=2.0)
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
        p20.drop_tip()

    """ NORMALIZATION """
    pool_dests = dilution_plate.columns()[-1][:num_samples]
    all_pcr1_wells = [well for set in pcr1_sample_sets for well in set]
    all_normalization_wells = [
        normalization_plate.wells()[pcr1_plate.wells().index(well)]
        for well in all_pcr1_wells]
    wells_per_pool_list = [
        num_subsamples*2 for num_subsamples in subsample_list]
    pool_source_sets = [
        all_normalization_wells[
            i*wells_per_pool_list[i]:(i+1)*wells_per_pool_list[i]]
        for i in range(num_samples)]
    vol_sample_per_pool = 15

    if perform_normalization:
        ctx.pause(F'RUN PCR PROFILE 1 ON PLATE IN SLOT {pcr1_plate.parent}. \
CHANGE THE TUBERACK 1 (SLOT 7) ACCORDING TO REAGENT MAP 2.')

        if len(all_normalization_wells) > 28:
            reservoir = ctx.load_labware('agilent_3_reservoir_95ml', '11',
                                         'normalization buffers reservoir')
            binding_buffer = reservoir.rows()[0][0]
            wash_buffer = [reservoir.rows()[0][1] for _ in range(2)]
            elution_buffer = tuberack2.rows()[0][2]
            all_normalization_cols = []
            for well in all_normalization_wells:
                col_ind = normalization_plate.wells().index(well) // 8
                col = normalization_plate.rows()[0][col_ind]
                if col not in all_normalization_cols:
                    all_normalization_cols.append(col)
            normalization_locs = all_normalization_cols
            buffer_channels = 8
        else:
            binding_buffer = tuberack2.columns()[-1][0]
            wash_buffer = tuberack2.columns()[-1][1:3]
            elution_buffer = tuberack2.columns()[-1][3]
            normalization_locs = all_normalization_wells
            buffer_channels = 1
        vol_pcr1_product = 15
        vol_binding_buffer = vol_pcr1_product
        vol_wash_buffer = 50
        vol_elution = 20
        wells_per_wash_tube = math.floor(1450/vol_wash_buffer)

        # transfer binding buffer, mix, incubate
        pick_up(p20, buffer_channels)
        for d in normalization_locs:
            p20.aspirate(vol_binding_buffer, binding_buffer)
            p20.dispense(vol_binding_buffer, d.bottom(2))
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
        p20.drop_tip()

        # transfer PCR1 to normalization plate
        for s, d in zip(all_pcr1_wells, all_normalization_wells):
            pick_up(p20, 1)
            p20.aspirate(vol_pcr1_product, s)
            p20.dispense(vol_pcr1_product, d.bottom(2))
            p20.mix(10, 10, d.bottom(2), rate=2.0)
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
            p20.drop_tip()

        ctx.delay(minutes=60, msg='Incubating 1 hour.')

        # remove liquid
        for d in normalization_locs:
            pick_up(p300, buffer_channels)
            p300.aspirate(vol_pcr1_product+vol_binding_buffer, d.bottom(0.5))
            p300.drop_tip()

        # wash
        for i, d in enumerate(normalization_locs):
            source_tube = wash_buffer[i//wells_per_wash_tube]
            pick_up(p300, buffer_channels)
            p300.aspirate(vol_wash_buffer, source_tube)
            p300.dispense(vol_wash_buffer, d.bottom(2))
            p300.mix(2, 10, d.bottom(2), rate=2.0)
            p300.aspirate(vol_wash_buffer, d.bottom(0.5))
            p300.drop_tip()

        # elute
        for d in normalization_locs:
            pick_up(p20, buffer_channels)
            p20.aspirate(vol_elution, elution_buffer)
            p20.dispense(vol_elution, d.bottom(2))
            p20.mix(5, 10, d.bottom(2), rate=2.0)
            p20.drop_tip()

        ctx.delay(minutes=5, msg='Incubating 5 minutes.')

    else:
        ctx.pause(f'RUN PCR PROFILE 1 ON PLATE IN SLOT {pcr1_plate.parent}. \
NORMALIZE ALL SAMPLES PLACE NORMALIZED PLATE IN SLOT 6 FOR POOLING TO BEGIN. \
CHANGE THE TUBERACK 1 (SLOT 7) ACCORDING TO REAGENT MAP 2')

    for source_set, pool in zip(pool_source_sets, pool_dests):
        pick_up(p20, 1)
        for s in source_set:
            p20.aspirate(vol_sample_per_pool, d.bottom(0.5))
            p20.dispense(vol_sample_per_pool, pool.bottom(3))
        p20.drop_tip()

    if num_samples < 6:
        num_replicates = 4
    elif 6 <= num_samples <= 7:
        num_replicates = 3
    else:
        num_replicates = 2

    num_samples_mm_creation = num_replicates + 2

    pcr2_map = [
        {
            'forward-primer-tube': forward_primer_well,
            'creation-tube': creation_well,
            'volume': 0.1*num_samples_mm_creation
        }
        for creation_well, forward_primer_well in zip(
            tuberack2.wells()[12:12+num_samples],
            tuberack.wells()[8:8+num_samples])
    ]

    # add all constant reagents to each mix tube
    vol_pcr_mm = 10*num_samples_mm_creation
    vol_water_mm = 4.8*num_samples_mm_creation
    vol_primer_mm = 0.1*num_samples_mm_creation
    for reagent, vol in zip(
            [mm1, water, reverse_primer2],
            [vol_pcr_mm, vol_water_mm, vol_reverse_primer_mm]):
        pip = p300 if vol > 20 else p20
        tip_capacity = pip.tip_racks[0].wells()[0].max_volume
        num_transfers = math.ceil(vol/tip_capacity)
        vol_per_transfer = vol/num_transfers
        pick_up(pip, 1)
        for item in pcr2_map:
            mix_dest = item['creation-tube']
            for _ in range(num_transfers):
                pip.aspirate(vol_per_transfer, reagent)
                pip.dispense(vol_per_transfer, mix_dest.bottom(5))
        pip.drop_tip()

    # add unique forward/reverse primers to mix and homogenize
    vol_primer_mm = 0.1*num_samples_mm_creation
    for item in pcr2_map:
        primer = item['forward-primer-tube']
        pip = p300 if vol_primer_mm > 20 else p20
        tip_capacity = pip.tip_racks[0].wells()[0].max_volume
        num_transfers = math.ceil(vol_primer_mm/tip_capacity)
        vol_per_transfer = vol_forward_primer_mm/num_transfers
        pick_up(pip, 1)
        mix_dest = item['creation-tube']
        for _ in range(num_transfers):
            pip.aspirate(vol_per_transfer, primer)
            pip.dispense(vol_per_transfer, mix_dest.bottom(5))
        if i == 1:
            pip.mix(1, 20, mix_dest.bottom(5), rate=2.0)
        pip.drop_tip()

    # plate PCR mixes
    pcr2_mix_sources = [item['creation-tube'] for item in pcr2_map]
    pcr2_mix_dest_sets = [
        row[:num_replicates] + [row[9]]  # include NTC
        for row in pcr2_plate.rows()[:num_samples]]
    vol_pcr2_mix = 15
    for source, dest_set in zip(pcr2_mix_sources, pcr2_mix_dest_sets):
        pick_up(p20, 1)
        for d in dest_set:
            p20.aspirate(vol_pcr2_mix, source)
            p20.dispense(vol_pcr2_mix, d.bottom(2))
            p20.move_to(d.bottom().move(Point(x=d.diameter/4, z=2)))
        p20.drop_tip()

    """ POOLING """
    pool_replicate_sets = [
        row[:num_replicates]
        for row in pcr2_plate.rows()[:num_samples]]
    num_pickups = 1

    # distribute replicates
    for pool, replicate_set in zip(pool_dests, pool_replicate_sets):
        # transfer replicates
        pick_up(p20, 1)
        for i, r in enumerate(replicate_set):
            if i == 0:
                p20.mix(10, 10, pool.bottom(3), rate=2.0)
            p20.aspirate(5, pool)
            p20.dispense(5, r.bottom(2))
            p20.mix(1, 5, r.bottom(2), rate=2.0)
            p20.move_to(r.bottom().move(Point(x=r.diameter/4, z=2)))
        p20.drop_tip()

    # write tip data to dictionary
    tip_log = {}
    for slot, lw in ctx.loaded_labwares.items():
        if lw.is_tiprack:
            tiprack_info = {
                well.display_name.split(' ')[0]: well.has_tip
                for well in lw.wells()
            }
            tip_log[slot] = tiprack_info

    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        with open(tip_file_path, 'w') as outfile:
            json.dump(tip_log, outfile, indent=4)
