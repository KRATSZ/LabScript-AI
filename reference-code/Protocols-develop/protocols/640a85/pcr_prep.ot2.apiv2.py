import math

# metadata
metadata = {
    'protocolName': 'PCR Prepation',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    [number_of_samples, pcr_type, p300_multi_mount,
        p20_single_mount] = get_values(  # noqa: F821
            'number_of_samples', 'pcr_type', 'p300_multi_mount',
            'p20_single_mount')

    # checks
    if p300_multi_mount == p20_single_mount:
        raise Exception('Pipette mounts cannot match.')
    if number_of_samples < 1 or number_of_samples > 96:
        raise Exception('Invalid number of DNA samples (must be 1-96).')

    # load labware
    tc = ctx.load_module('thermocycler')
    tc.open_lid()
    tc_plate = tc.load_labware(pcr_type)
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', '1', '300ul tips')]
    tips20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', '2', '20ul tips')]
    start_plate = ctx.load_labware(pcr_type, '4', 'input DNA sample plate')
    mm = ctx.load_labware(
        'nest_12_reservoir_15ml', '6', 'reservoir for mastermix').wells()[0]

    # pipettes
    m300 = ctx.load_instrument(
        'p300_multi', p300_multi_mount, tip_racks=tips300)
    p20 = ctx.load_instrument(
        'p20_single_gen2', p20_single_mount, tip_racks=tips20)

    # sample setup
    dna_sources = start_plate.wells()[:number_of_samples]
    mm_dests = tc_plate.rows()[0][:math.ceil(number_of_samples/8)]
    tc_dests = tc_plate.wells()[:number_of_samples]

    # distribute mastermix
    m300.pick_up_tip()
    for d in mm_dests:
        m300.transfer(73, mm, d.bottom(3), air_gap=10, new_tip='never')
        m300.blow_out(d.top(-2))
    m300.drop_tip()

    # transfer samples
    for s, d_set in zip(dna_sources, tc_dests):
        p20.pick_up_tip()
        p20.aspirate(3, s.bottom(2))
        p20.air_gap(2)
        p20.touch_tip(s, v_offset=-3)
        p20.dispense(2, d.top(-2))
        p20.aspirate(7, d.bottom(2))
        p20.dispense(10, d.bottom(2))
        p20.blow_out(d.top(-2))
        p20.touch_tip(d, v_offset=-3)
        p20.drop_tip()

    # setup and execute thermocycler profile
    tc.close_lid()
    tc.set_lid_temperature(105)
    profile1 = [{'temperature': 95, 'hold_time_minutes': 15}]
    profiles2 = [
        [
            {'temperature': 94, 'hold_time_seconds': 30},
            {'temperature': temp, 'hold_time_seconds': 30},
            {'temperature': 72, 'hold_time_seconds': 90}
        ] for temp in [69-i*1.5 for i in range(13)]
    ]
    profile3 = [
        {'temperature': 94, 'hold_time_seconds': 30},
        {'temperature': 50, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 45}
    ]
    profile4 = [
        {'temperature': 72, 'hold_time_minutes': 10},
        {'temperature': 4, 'hold_time_seconds': 10}
    ]
    tc.execute_profile(steps=profile1, repetitions=1, block_max_volume=25)
    for prof in profiles2:
        tc.execute_profile(
            steps=prof, repetitions=1, block_max_volume=25)
    tc.execute_profile(steps=profile3, repetitions=25, block_max_volume=25)
    tc.execute_profile(steps=profile4, repetitions=1, block_max_volume=25)
