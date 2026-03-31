import math

metadata = {
    'protocolName': 'Custom Chip PCR Preparation',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    num_samples, p10_mount, p50_mount = get_values(  # noqa: F821
        'num_samples', 'p10_mount', 'p50_mount')

    # check for too many samples
    if num_samples > 24:
        raise Exception("24 sample membranes maximum on chip.")
    if p10_mount == p50_mount:
        raise Exception('Pipette mounts cannot be the same.')

    # load labware and modules
    tc = ctx.load_module('thermocycler')
    tc_plate = tc.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'thermocycler plate')
    if tc.lid_position != 'open':
        tc.open_lid()
    tc.set_lid_temperature(105)
    tempdeck = ctx.load_module('tempdeck', '6')
    tubes = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_snapcap',
        '2ml Eppendorf snapcap reagent tubes')
    chip = ctx.load_labware(
        'custom_24_shakerslide', '1', 'custom chip on shaker')
    strips = ctx.load_labware(
        'tempassure_96_strips_200ul_pcr', '2', 'PCR strips')
    tips10 = [
        ctx.load_labware('opentrons_96_tiprack_10ul', '3', '10ul tiprack')]
    tips50 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', '5', '300ul tiprack')]

    # pipettes
    m10 = ctx.load_instrument(
        instrument_name='p10_multi',
        mount=p10_mount,
        tip_racks=tips10
    )
    p50 = ctx.load_instrument(
        instrument_name='p50_single',
        mount=p50_mount,
        tip_racks=tips50
    )

    if num_samples > 16:
        num_samples_for_mm = num_samples + 4
    else:
        num_samples = 20

    # reagents
    h2o = tubes.wells()[0]
    rxn_buffer = tubes.wells()[1]
    primer = tubes.wells()[2]
    dna_pol = tubes.wells()[3]
    mix_tube = tubes.wells()[4]

    # create master mix, enough for 4 extra samples
    def mm_create(vol, source):
        num_asp = math.ceil(vol/45)
        vol_per_asp = vol/num_asp
        p50.pick_up_tip()
        for _ in range(num_asp):
            p50.move_to(source.top(5))
            p50.air_gap(50-vol_per_asp)
            p50.aspirate(vol_per_asp, source)
            p50.dispense(50, mix_tube.top())
            # p50.blow_out(mix_tube.top())
        p50.drop_tip()

    mm_create(15*num_samples_for_mm, h2o)
    mm_create(5*num_samples_for_mm, rxn_buffer)
    if num_samples_for_mm > 10:
        mm_create(1*num_samples_for_mm, primer)

    p50.pick_up_tip()
    p50.transfer(
        0.25*num_samples_for_mm,
        dna_pol.bottom(2),
        mix_tube,
        air_gap=5,
        new_tip='never')
    p50.mix(10, 20, mix_tube)
    # p50.blow_out(mix_tube.top())
    p50.drop_tip()

    # set up spots
    num_cols = math.ceil(num_samples/8)
    spots = [well for well in chip.rows()[0][:num_cols]]

    # slow flow rate and transfer sample to strips and immediately transfer
    # water to membrane
    m10.flow_rate.aspirate = 2
    m10.flow_rate.dispense = 2
    sample_strips = strips.rows()[0][:num_cols]
    h2o_strip = strips.rows()[0][-1]
    for spot, dest in zip(spots, sample_strips):
        m10.pick_up_tip()
        m10.transfer(8, spot.top(), dest, new_tip='never', trash=False)
        m10.transfer(10, h2o_strip.bottom(1), spot.top(1), new_tip='never')
        m10.drop_tip()

    # transfer master mix to new strip tubes
    mix_wells = strips.wells()[24:24+num_samples]
    p50.pick_up_tip()
    for m in mix_wells:
        p50.transfer(21.75, mix_tube, m, new_tip='never')
        # p50.blow_out(m.top(-3))
    p50.drop_tip()

    # reset flow rate to default and transfer sample to corresponding strip
    # tube already containing master mix
    m10.flow_rate.aspirate = 5
    m10.flow_rate.dispense = 10
    mix_strips = strips.rows()[0][3:3+num_cols]
    for s, d in zip(sample_strips, mix_strips):
        m10.pick_up_tip()
        m10.transfer(3, s, d, new_tip='never')
        m10.mix(10, 9, d)
        # m10.blow_out(d.top(-2))
        m10.drop_tip()

    # transfer to thermocycler and perform thermocycling profile
    tc_dests = tc_plate.rows()[0][:num_cols]
    for s, d in zip(mix_strips, tc_dests):
        m10.pick_up_tip()
        m10.transfer(25, s.bottom(0.5), d, new_tip='never')
        # m10.blow_out(d.top(-2))
        m10.drop_tip()

    tc.close_lid()
    tc.set_block_temperature(95, hold_time_minutes=5)
    profile = [
        {'temperature': 95, 'hold_time_minutes': 1},
        {'temperature': 58, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 30}
    ]
    tc.execute_profile(steps=profile, repetitions=40, block_max_volume=25)
    tc.set_block_temperature(temperature=72, hold_time_minutes=5)
    tc.set_block_temperature(12)
    tc.open_lid()
    tc.deactivate_lid()

    ctx.comment('Thermocycler holding block temperature at 12˚C. Manually \
deactivate in the Opentrons App when ready.')
