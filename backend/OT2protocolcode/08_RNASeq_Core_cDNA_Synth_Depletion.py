import math
import json

metadata = {
    'protocolName': 'Zymo-Seq RiboFree™ Total RNA Library Prep First-Strand \
cDNA Synthesis and RiboFreeTM Universal Depletion (robot 1)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_samples, starting_vol, rna_input, p20_mount,
     m20_mount] = get_values(  # noqa: F821
     'number_of_samples', 'starting_vol', 'rna_input', 'p20_mount',
     'm20_mount')
    # [number_of_samples, starting_vol, rna_input, p20_mount, p50_mount] = [
    #     96, 5, '> 1µg', 'right', 'left']

    # load modules and labware
    tc = ctx.load_module('thermocycler')
    tc.set_lid_temperature(100)
    tc.set_block_temperature(4)
    tc_plate = tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    racks20s = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['1', '2', '3']
    ]
    tempdeck = ctx.load_module('temperature module gen2', '4')
    tempdeck.set_temperature(4)
    tempblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_screwcap')
    reagent_res = ctx.load_labware(
        'nest_12_reservoir_15ml', '5', 'reagent reservoir')
    racks20m = [ctx.load_labware('opentrons_96_tiprack_20ul', '6')]

    # pipettes
    if p20_mount == m20_mount:
        raise Exception('Pipette mounts cannot match.')
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=racks20s)
    p20.flow_rate.aspirate = 10
    p20.flow_rate.dispense = 20
    p20.flow_rate.blow_out = 30
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=racks20m)

    # reagents and sample setup
    if number_of_samples > 96 or number_of_samples < 1:
        raise Exception('Invalid number of samples (must be 1-96).')
    samples = tc_plate.wells()[:number_of_samples]
    samples_multi = tc_plate.rows()[0][:math.ceil(number_of_samples/8)]
    r1, r2, h2o = tempblock.rows()[0][:3]
    d1, d2, d3 = tempblock.rows()[1][:3]
    etoh = reagent_res.wells()[0]

    tip20s_count = 0
    all_tips20s = [tip for rack in racks20s for tip in rack.wells()]
    all_tips20m = [tip for rack in racks20m for tip in rack.rows()[0]]
    tip20m_count = 0
    tip20m_max = len(racks20m*12)
    tip20s_max = len(racks20s*96)

    def pick_up(pip):
        nonlocal tip20s_count
        nonlocal tip20m_count
        if pip == p20:
            if tip20s_count == tip20s_max:
                ctx.pause('Replace tipracks before resuming.')
                tip20s_count = 0
                [rack.reset() for rack in racks20s]
            pip.pick_up_tip(all_tips20s[tip20s_count])
            tip20s_count += 1
        else:
            if tip20m_count == tip20m_max:
                ctx.pause('Replace tipracks before resuming.')
                tip20m_count = 0
                [rack.reset() for rack in racks20m]
            pip.pick_up_tip(all_tips20m[tip20m_count])
            tip20m_count += 1

    """ Section 1.1: First-Strand cDNA Synthesis (Yellow Caps) """
    if tc.lid_position == 'closed':
        tc.open_lid()

    # bring samples up to 8µl with H2O if necessary
    vol_h2o = 9 - starting_vol if rna_input != '< 100ng' else 8 - starting_vol
    for s in samples:
        pick_up(p20)
        p20.transfer(vol_h2o, h2o, s, new_tip='never')
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    # transfer R1
    vol_r1 = 1 if rna_input != '< 100ng' else 2
    for s in samples:
        pick_up(p20)
        p20.transfer(vol_r1, r1, s, mix_after=(3, 5), new_tip='never')
        p20.blow_out(s.top(-2))
        p20.drop_tip()
    ctx.pause('Briefly spin down plate before resuming.')

    # execute primer annealing
    profile_1_1 = [
        {'temperature': 98, 'hold_time_minutes': 3},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_1_1, repetitions=1, block_max_volume=10)
    tc.open_lid()

    # transfer R2
    for s in samples:
        pick_up(p20)
        p20.transfer(10, r2, s, mix_after=(3, 15), new_tip='never')
        p20.blow_out(s.top(-2))
        p20.drop_tip()

    # execute reverse transcription
    profile_1_2 = [
        {'temperature': 25, 'hold_time_minutes': 5},
        {'temperature': 48, 'hold_time_minutes': 15},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_1_2, repetitions=1, block_max_volume=20)
    tc.open_lid()

    """ Section 1.2: RiboFreeTM Universal Depletion (Red Caps) """

    # distribute D reagents to predispesing plate
    if number_of_samples > 24:
        predispense_plate = ctx.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt', '9',
            'plate to predispense D reagent')
        vol_per_well = 11*math.ceil(number_of_samples/8)
        for d_reagent, col in zip(
                [d1, d2, d3], predispense_plate.columns()[:3]):
            pick_up(p20)
            for well in col:
                p20.transfer(
                    vol_per_well, d_reagent, well, air_gap=1, new_tip='never')
                p20.blow_out(well.top(-5))
                p20.touch_tip(well)
            p20.drop_tip()
        d1, d2, d3 = predispense_plate.rows()[0][:3]
        d_pip = m20
        d_samples = samples_multi
    else:
        d_pip = p20
        d_samples = samples

    # transfer D1
    for s in d_samples:
        pick_up(d_pip)
        d_pip.transfer(10, d1, s, mix_after=(3, 15), new_tip='never')
        d_pip.blow_out(s.top(-2))
        d_pip.drop_tip()
    ctx.pause('Briefly spin down plate before resuming.')

    # execute pre-depletion incubation
    profile_1_3 = [
        {'temperature': 98, 'hold_time_minutes': 3},
        {'temperature': 68, 'hold_time_minutes': 5}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_1_3, repetitions=1, block_max_volume=30)
    tc.open_lid()

    # transfer D2
    for s in d_samples:
        pick_up(d_pip)
        d_pip.transfer(10, d2, s, mix_after=(3, 15), new_tip='never')
        d_pip.blow_out(s.top(-2))
        d_pip.drop_tip()

    # exeute depletion reaction
    if rna_input == '> 1µg':
        inc_time = 30
    elif rna_input == '250ng-1µg':
        inc_time = 60
    else:
        inc_time = 120
    profile_1_4 = [
        {'temperature': 68, 'hold_time_minutes': inc_time}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_1_4, repetitions=1, block_max_volume=40)
    tc.open_lid()

    # transfer D3
    for s in d_samples:
        pick_up(d_pip)
        d_pip.transfer(10, d3, s, mix_after=(3, 15), new_tip='never')
        d_pip.blow_out(s.top(-2))
        d_pip.drop_tip()

    # execute stop depletion
    profile_1_5 = [
        {'temperature': 98, 'hold_time_minutes': 2},
        {'temperature': 25, 'hold_time_seconds': 10}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_1_5, repetitions=1, block_max_volume=50)
    tc.open_lid()

    # transfer EtOH
    for m in samples_multi:
        pick_up(m20)
        m20.transfer(
            25, etoh, m.top(-2), air_gap=2, new_tip='never')
        m20.mix(5, 20, m),
        m20.blow_out(m.top(-2))
        m20.air_gap(2)
        m20.drop_tip()

    ctx.comment('Carefully remove sample plate from thermocycler and proceed \
with cleanup.')

    # track final used tip
    if not ctx.is_simulating():
        file_path = '/data/csv/tip_track.json'
        # file_path = '/protocols/tip_track.json'
        data = {
            'tips20s': tip20s_count,
            'tips20m': tip20m_count
        }
        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)
