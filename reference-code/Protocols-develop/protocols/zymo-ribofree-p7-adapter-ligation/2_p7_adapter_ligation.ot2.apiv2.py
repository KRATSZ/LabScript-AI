import json
import os

metadata = {
    'protocolName': 'Zymo-Seq RiboFree™ Total RNA Library Prep P7 Adapter \
Ligation (robot 1)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_samples, p20_mount] = get_values(  # noqa: F821
            'number_of_samples', 'p20_mount')
    # [number_of_samples, p20_mount] = [96, 'right']

    # load modules and labware
    tc = ctx.load_module('thermocycler')
    tc.set_lid_temperature(100)
    tc.set_block_temperature(4)
    tc_plate = tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    racks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['1', '2', '3', '6']
    ]
    tempdeck = ctx.load_module('temperature module gen2', '4')
    tempdeck.set_temperature(4)
    tempblock = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_screwcap')

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=racks20)
    p20.flow_rate.aspirate = 10
    p20.flow_rate.dispense = 20
    p20.flow_rate.blow_out = 30

    # file_path = 'protocols/tip_track.json'
    if not ctx.is_simulating():
        file_path = '/data/csv/tip_track.json'
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                data = json.load(json_file)
                if 'tips20' in data:
                    tip20_count = data['tips20']
                else:
                    tip20_count = 0
    else:
        tip20_count = 0

    all_tips20 = [tip for rack in racks20 for tip in rack.wells()]
    tip20_max = len(all_tips20)

    def pick_up():
        nonlocal tip20_count
        if tip20_count == tip20_max:
            ctx.pause('Replace 20µl tipracks before resuming.')
            tip20_count = 0
            [rack.reset() for rack in racks20]
        p20.pick_up_tip(all_tips20[tip20_count])
        tip20_count += 1

    # reagents and sample setup
    if number_of_samples > 96 or number_of_samples < 1:
        raise Exception('Invalid number of samples (must be 1-96).')
    samples = tc_plate.wells()[:number_of_samples]
    l1, l2 = tempblock.rows()[2][:2]

    """ Section 2.1: P7 Adapter Ligation (Green Caps) """
    if tc.lid_position == 'closed':
        tc.open_lid()

    # transfer L1
    for s in samples:
        p20.pick_up_tip()
        p20.transfer(10, l1, s, mix_after=(3, 15), new_tip='never')
        p20.blow_out(s.top(-2))
        p20.drop_tip()
    ctx.pause('Briefly spin down plate before resuming.')

    # execute P7 ligation reaction
    profile_2_1 = [
        {'temperature': 37, 'hold_time_minutes': 15},
        {'temperature': 98, 'hold_time_minutes': 2},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_2_1, repetitions=1, block_max_volume=20)
    tc.open_lid()

    # transfer L2
    for s in samples:
        p20.pick_up_tip()
        p20.transfer(20, l2, s, mix_after=(3, 15), new_tip='never')
        p20.blow_out(s.top(-2))
        p20.drop_tip()
    ctx.pause('Briefly spin down plate before resuming.')

    # execute second strand synthesis
    profile_2_2 = [
        {'temperature': 95, 'hold_time_minutes': 10},
        {'temperature': 63, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_minutes': 7},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.close_lid()
    tc.execute_profile(steps=profile_2_2, repetitions=1, block_max_volume=40)
    tc.open_lid()

    ctx.comment('Carefully remove sample plate from thermocycler and proceed \
with cleanup.')

    # track final used tip
    # file_path = '/data/csv/tip_track.json'
    if not ctx.is_simulating():
        data = {
            'tips20': tip20_count
        }
        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)
