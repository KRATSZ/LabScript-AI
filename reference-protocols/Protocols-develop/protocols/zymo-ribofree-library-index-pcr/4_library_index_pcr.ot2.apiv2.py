import math
import json
import os

metadata = {
    'protocolName': 'Zymo-Seq RiboFree™ Total RNA Library Prep Library Index \
PCR (robot 1)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_samples, rna_input, p20_mount,
        m20_mount] = get_values(  # noqa: F821
            'number_of_samples', 'rna_input', 'p20_mount', 'm20_mount')
    # [number_of_samples, rna_input, p20_mount, m20_mount] = [
    #     96, '> 1µg', 'right', 'left']

    # load modules and labware
    tc = ctx.load_module('thermocycler')
    tc.set_lid_temperature(100)
    tc.set_block_temperature(4)
    tc_plate = tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    racks20s = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['1', '2']
    ]
    tempdeck = ctx.load_module('temperature module gen2', '4')
    tempdeck.set_temperature(4)
    tempblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_screwcap')
    reagent_res = ctx.load_labware(
        'nest_12_reservoir_15ml', '5', 'reagent reservoir')
    index_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul',
        '9', 'UDI primer plate')
    racks20m = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['3', '6']
    ]

    # pipettes
    if p20_mount == m20_mount:
        raise Exception('Pipette mounts cannot match.')
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=racks20s)
    p20.flow_rate.aspirate = 10
    p20.flow_rate.dispense = 20
    p20.flow_rate.blow_out = 30
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=racks20m)

    # file_path = 'protocols/tip_track.json'
    if not ctx.is_simulating():
        file_path = '/data/csv/tip_track.json'
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                data = json.load(json_file)
                if 'tips20s' in data:
                    tip20s_count = data['tips20s'] % 96
                else:
                    tip20s_count = 0
                if 'tips20m' in data:
                    tip20m_count = data['tips20m'] % 12
                else:
                    tip20m_count = 0
    else:
        tip20s_count = 0
        tip20m_count = 0

    all_tips20s = [tip for rack in racks20s for tip in rack.wells()]
    all_tips20m = [tip for rack in racks20m for tip in rack.rows()[0]]
    tip20s_max = len(all_tips20s)
    tip20m_max = len(all_tips20m)

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

    # reagents and sample setup
    if number_of_samples > 96 or number_of_samples < 1:
        raise Exception('Invalid number of samples (must be 1-96).')
    samples = tc_plate.wells()[:number_of_samples]
    udi_primers = index_plate.rows()[0][:math.ceil(number_of_samples/8)]
    samples_multi = tc_plate.rows()[0][:math.ceil(number_of_samples/8)]
    taq_premix = tempblock.rows()[3][0]
    dna_eb = reagent_res.wells()[1]

    """ Section 2.3: Library Index PCR (Green Caps) """
    if tc.lid_position == 'closed':
        tc.open_lid()

    # transfer UDI primers
    for m in samples_multi:
        pick_up(m20)
        m20.transfer(
            5, udi_primers, m, mix_after=(3, 15), air_gap=1, new_tip='never')
        m20.blow_out(m.top(-2))
        m20.drop_tip()

    # transfer taq premix
    for s in samples:
        for i, vol in enumerate([15, 10]):
            pick_up(p20)
            p20.transfer(vol, taq_premix, s.bottom(1), new_tip='never')
            if i == 0:
                p20.drop_tip()
        p20.mix(3, 15, s)
        p20.blow_out(s.top(-2))
        p20.drop_tip()
    ctx.pause('Briefly spin down sample plate and replace on thermoycler.')

    # run first part of profile 1
    tc.close_lid()
    if rna_input == '> 1µg':
        cycles = 10
    elif rna_input == '250ng-1µg':
        cycles = 11
    elif rna_input == '100ng-250ng':
        cycles = 12
    elif rna_input == '< 100ng':
        cycles = 13
    profile_2_4 = [{'temperature': 95, 'hold_time_minutes': 10}]
    profile_2_5 = [
        {'temperature': 95, 'hold_time_seconds': 30},
        {'temperature': 60, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_minutes': 1}
    ]
    profile_2_6 = [
        {'temperature': 72, 'hold_time_minutes': 7},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.execute_profile(steps=profile_2_4, repetitions=1, block_max_volume=50)
    tc.execute_profile(
        steps=profile_2_5, repetitions=cycles, block_max_volume=50)
    tc.execute_profile(steps=profile_2_6, repetitions=1, block_max_volume=50)
    tc.open_lid()

    # transfer elution buffer
    for m in samples_multi:
        pick_up(m20)
        m20.transfer(50, dna_eb, m.top(-2), new_tip='never')
        m20.mix(5, 15, m)
        m20.blow_out(m.top(-2))
        m20.drop_tip()

    ctx.comment('Carefully remove sample plate from thermocycler and proceed \
with cleanup.')
