import math
from opentrons.types import Point

metadata = {
    'protocolName': 'Mass Spec Sample Prep',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, tip_start_samples, well_start_samples, vol_sample,
     height_sample, vol_meoh, vol_mq, col_meoh, col_mq, vol_sample_redissolved,
     mount_p300, mount_m300
     ] = get_values(  # noqa: F821
        'num_samples', 'tip_start_samples', 'well_start_samples', 'vol_sample',
        'height_sample', 'vol_meoh', 'vol_mq', 'col_meoh', 'col_mq',
        'vol_sample_redissolved', 'mount_p300', 'mount_m300')

    num_racks = math.ceil(num_samples/24)
    num_cols = math.ceil(num_samples/8)
    vol_air_gap = 20.0

    # labware
    source_racks = [
        ctx.load_labware(
            'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot,
            f'source plate {i+1}')
        for i, slot in enumerate(['1', '2', '3', '4'][:num_racks])]
    tipracks300s = [ctx.load_labware('opentrons_96_tiprack_300ul', '6')]
    stacked_plate = ctx.load_labware(
        'spestackedoncollection_96_wellplate_1600ul', '5',
        'SPE stacked on collection plate')
    tipracks300m = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['9', '11']]
    collection_plate = ctx.load_labware('greiner_96_wellplate_2000ul',
                                        '7', 'collection plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '8', 'reservoir')
    final_plate = ctx.load_labware('axygen_96_plate_200ul_pcr', '10')

    # pipettes
    p300 = ctx.load_instrument(
        'p300_single_gen2',
        mount_p300,
        tip_racks=tipracks300s)
    p300.starting_tip = tipracks300s[0].wells_by_name()[tip_start_samples]
    m300 = ctx.load_instrument(
        'p300_multi_gen2',
        mount_m300,
        tip_racks=tipracks300m)

    def wick(well, pip, side=1):
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))

    def slow_withdraw(well, pip):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # reagents
    samples_source = [
        well for rack in source_racks for well in rack.wells()][:num_samples]
    stacked_starting_index = stacked_plate.wells().index(
        stacked_plate.wells_by_name()[well_start_samples])
    samples_stacked_s = stacked_plate.wells()[
        stacked_starting_index:stacked_starting_index+num_samples]
    samples_stacked_m = []
    samples_collection_m = []
    samples_final_m = []
    for well in samples_stacked_s:
        col_reference_index = stacked_plate.wells().index(well)//8
        if stacked_plate.columns()[
                col_reference_index][0] not in samples_stacked_m:
            samples_stacked_m.append(
                stacked_plate.columns()[col_reference_index][0])
        if collection_plate.columns()[
                col_reference_index][0] not in samples_collection_m:
            samples_collection_m.append(
                collection_plate.columns()[col_reference_index][0])
        if final_plate.columns()[
                col_reference_index][0] not in samples_final_m:
            samples_final_m.append(
                final_plate.columns()[col_reference_index][0])

    meoh = [
        reservoir.rows()[0][int(col)-1]
        for col in col_meoh.split(',')]
    mq = [
        reservoir.rows()[0][int(col)-1]
        for col in col_mq.split(',')]

    # transfer sample
    num_trans = math.ceil(
        vol_sample/(p300.tip_racks[0].wells()[0].max_volume-vol_air_gap))
    vol_per_trans = round(vol_sample/num_trans, 2)
    for s, d in zip(samples_source, samples_stacked_s):
        p300.pick_up_tip()
        for _ in range(num_trans):
            p300.aspirate(vol_per_trans, s.bottom(height_sample))
            slow_withdraw(s, p300)
            p300.aspirate(vol_air_gap, s.top())  # air gap
            p300.dispense(vol_air_gap, d.top())  # dispense air gap
            p300.dispense(vol_per_trans, d.bottom(2))
            slow_withdraw(d, p300)
        p300.drop_tip()

    ctx.pause('RESUME WHEN READY')

    meoh_index = 0
    meoh_vol_count = 0
    meoh_vol_max = 12000
    num_trans = math.ceil(
        vol_meoh/(m300.tip_racks[0].wells()[0].max_volume-vol_air_gap))
    vol_per_trans = round(vol_meoh/num_trans, 2)
    for _ in range(2):
        m300.pick_up_tip()
        for d in samples_stacked_m:
            for _ in range(num_trans):
                if meoh_vol_count + vol_per_trans*m300.channels > meoh_vol_max:
                    meoh_index += 1
                    meoh_vol_count = 0
                if meoh_index == len(meoh):
                    ctx.pause('Refill MeOH')
                    meoh_index = 0
                    meoh_vol_count = 0
                meoh_source = meoh[meoh_index]
                meoh_vol_count += vol_per_trans*m300.channels

                m300.aspirate(vol_air_gap, meoh_source.top())  # pre air gap
                m300.aspirate(vol_per_trans, meoh_source)
                slow_withdraw(meoh_source, m300)
                m300.aspirate(vol_air_gap, meoh_source.top())
                m300.dispense(m300.current_volume, d.top(-1))
        m300.drop_tip()

        ctx.pause('RESUME WHEN READY')

    mq_index = 0
    mq_vol_count = 0
    mq_vol_max = 12000
    num_trans = math.ceil(vol_mq/(m300.tip_racks[0].wells()[0].max_volume))
    vol_per_trans = round(vol_mq/num_trans, 2)
    m300.pick_up_tip()
    for d in samples_collection_m:
        for _ in range(num_trans):
            if mq_vol_count + vol_per_trans*m300.channels > mq_vol_max:
                mq_index += 1
                mq_vol_count = 0
            if mq_index == len(mq):
                ctx.pause('Refill MQ')
                mq_index = 0
                mq_vol_count = 0
            mq_source = mq[mq_index]
            mq_vol_count += vol_per_trans*m300.channels
            m300.aspirate(vol_per_trans, mq_source)
            slow_withdraw(mq_source, m300)
            m300.dispense(m300.current_volume, d.top(-1))
    m300.drop_tip()

    ctx.pause('RESUME WHEN READY')

    for tip, s, d in zip(
            m300.tip_racks[1].rows()[0][:num_cols],
            samples_collection_m,
            samples_final_m):
        m300.pick_up_tip(tip)
        m300.aspirate(vol_sample_redissolved, s)
        slow_withdraw(s, m300)
        m300.aspirate(vol_air_gap, s.top())  # air gap
        m300.dispense(vol_air_gap, d.top())  # dispense air gap
        m300.dispense(vol_sample, d)
        slow_withdraw(d, m300)
        m300.drop_tip()
