import math

# metadata
metadata = {
    'protocolName': 'NGS Library Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):
    m20_mount, num_samples = get_values(  # noqa: F821
        'm20_mount', 'num_samples')

    # load labware
    tc = ctx.load_module('thermocycler')
    tc_plate = tc.load_labware('abgene_96_wellplate_200ul')
    tc.open_lid()
    tc.set_lid_temperature(80)
    tc.set_block_temperature(4)
    plate1 = ctx.load_labware(
        'abgene_96_wellplate_200ul_isofreeze_block', '4',
        'Tn5 + 5x TD Buffer (col 1, PCR plate on ISOFREEZE block)')
    plate2 = ctx.load_labware(
        'abgene_96_wellplate_200ul', '5', '0.2% SDS (col 1, PCR plate)')
    tipracks = [
        ctx.load_labware('usascientific_96_tiprack_200ul', slot)
        for slot in ['1', '2', '3', '6']
    ]
    pcr_mm = ctx.load_labware(
        'nunc_96_wellplate_1700ul', '9',
        'PCR mastermix (col 1, deepwell plate').wells()[0]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    # sample and reagent setup
    num_cols = math.ceil(num_samples/8)
    tc_samples = tc_plate.rows()[0][:num_cols]
    tn5_5x_td_buffer = plate1.wells()[0]
    sds = plate2.wells()[0]
    amp_samples = plate1.rows()[0][:num_cols]
    i7_primers = plate2.rows()[0][:num_cols]

    # transfer tn5_5x_td_buffer
    for s in tc_samples:
        m20.pick_up_tip()
        m20.transfer(6, tn5_5x_td_buffer, s, air_gap=2, mix_after=(3, 10),
                     new_tip='never')
        m20.blow_out(s.top(-2))
        m20.air_gap(2)
        m20.drop_tip()

    # thermocycler profile 1
    tc.close_lid()
    tc.set_block_temperature(55, hold_time_minutes=21, block_max_volume=20)
    tc.set_block_temperature(4)
    tc.open_lid()

    # transfer sds
    for s in tc_samples:
        m20.pick_up_tip()
        m20.transfer(2.5, sds, s, air_gap=2, mix_after=(3, 10),
                     new_tip='never')
        m20.blow_out(s.top(-2))
        m20.air_gap(2)
        m20.drop_tip()

    # thermocycler profile 2
    tc.close_lid()
    tc.set_block_temperature(55, hold_time_minutes=21, block_max_volume=20)
    tc.set_block_temperature(4)
    tc.open_lid()

    m20.home()
    ctx.pause('Replace Tn5 + 5x TD Buffer plate (slot 1) with new \
amplification plate on ISOFREEZE block. Replace SDS plate (slot 2) with I7 \
primer plate before resuming.')

    # transfer PCR mastermix
    m20.pick_up_tip()
    for s in amp_samples:
        if m20.current_volume > 0:
            m20.dispense(m20.current_volume, pcr_mm.top())
        m20.transfer(16, pcr_mm, s.top(), air_gap=2, new_tip='never')
        m20.blow_out(s.top())
        m20.air_gap(2)
    m20.dispense(m20.current_volume, pcr_mm.top())

    # transfer tagmented DNA from DNA plate to Amplification plate
    for s, d in zip(tc_samples, amp_samples):
        if not m20.hw_pipette['has_tip']:
            m20.pick_up_tip()
        m20.transfer(2, s, d, air_gap=2, new_tip='never')
        m20.blow_out(d.top(-2))
        m20.air_gap(2)
        m20.drop_tip()

    # transfer i7 primers to corresponding wells
    for s, d in zip(i7_primers, amp_samples):
        if not m20.hw_pipette['has_tip']:
            m20.pick_up_tip()
        m20.transfer(2, s, d, air_gap=2, new_tip='never')
        m20.blow_out(d.top(-2))
        m20.air_gap(2)
        m20.drop_tip()

    m20.home()
    ctx.pause('Replace DNA plate on thermocycler with amplification plate \
before resuming.')

    tc.set_lid_temperature(105)
    tc.close_lid()
    profile1 = [
        {'temperature': 72, 'hold_time_minutes': 3},
        {'temperature': 94, 'hold_time_seconds': 30},
    ]
    profile2 = [
        {'temperature': 94, 'hold_time_seconds': 10},
        {'temperature': 62, 'hold_time_seconds': 15},
        {'temperature': 68, 'hold_time_seconds': 30}
    ]
    tc.execute_profile(steps=profile1, repetitions=1, block_max_volume=20)
    tc.execute_profile(steps=profile2, repetitions=11, block_max_volume=20)
    tc.set_block_temperature(68, hold_time_minutes=5, block_max_volume=20)
    tc.set_block_temperature(4)
    tc.open_lid()

    ctx.comment('Protocol completed')
