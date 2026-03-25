from opentrons.types import Point

metadata = {
    'protocolName': 'PCR',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [worklist, do_deactivate_tc, mount_m300,
     mount_p20] = get_values(  # noqa: F821
        'worklist', 'do_deactivate_tc', 'mount_m300', 'mount_p20')

    mix_reps_oligo = 5
    mix_vol_oligo = 5.0
    vol_pcr_reagent = 30.0
    mix_reps_pcr_reagent = 5
    mix_vol_pcr_reagent = 20.0

    # modules and labware
    tc = ctx.load_module('thermocycler')
    tc_plate = tc.load_labware('biorad_96_wellplate_200ul_pcr', 'pcr plate')
    tipracks200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '1')]
    oligo_plates = [
        ctx.load_labware('biorad_96_wellplate_200ul_pcr', slot,
                         f'oligo source plate {i+1}')
        for i, slot in enumerate(['5', '2'])]
    reagent_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '4',
                                     'reagent plate')
    tipracks20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['9', '6']]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', mount_m300,
                               tip_racks=tipracks200)
    p20 = ctx.load_instrument('p20_single_gen2', mount_p20,
                              tip_racks=tipracks20)

    # parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in worklist.splitlines()[1:]
        if line and line.split(',')[0].strip()]

    # reagents
    oligo_volumes = [float(line[3]) for line in data]
    oligo_sources = [
        oligo_plates[0].wells_by_name()[line[1]]
        for line in data]
    oligo_dests = [
        tc_plate.wells_by_name()[line[2]]
        for line in data]

    pcr_reagent = reagent_plate.rows()[0][0]

    def wick(well, pip, side=1):
        pip.move_to(well.bottom().move(Point(x=side*well.diameter/2*0.8, z=3)))

    def slow_withdraw(well, pip):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    # oligo transfer and mixing
    for vol, source, dest in zip(oligo_volumes, oligo_sources, oligo_dests):
        p20.pick_up_tip()
        p20.aspirate(vol, source)
        wick(source, p20)
        slow_withdraw(source, p20)
        p20.dispense(vol, dest)
        p20.mix(mix_reps_oligo, mix_vol_oligo, dest)
        wick(dest, p20)
        slow_withdraw(dest, p20)
        p20.drop_tip()

    # PCR reagent addition
    pcr_reagent_dests = []
    for well in oligo_dests:
        col_reference = tc_plate.columns()[tc_plate.wells().index(well)//8][0]
        if col_reference not in pcr_reagent_dests:
            pcr_reagent_dests.append(col_reference)

    tc.open_lid()
    tc.set_lid_temperature(105)
    for dest in pcr_reagent_dests:
        m300.pick_up_tip()
        m300.aspirate(vol_pcr_reagent, pcr_reagent)
        slow_withdraw(pcr_reagent, m300)
        m300.dispense(vol_pcr_reagent, dest)
        m300.mix(mix_reps_pcr_reagent, mix_vol_pcr_reagent, dest)
        slow_withdraw(dest, m300)
        m300.drop_tip()
    tc.close_lid()

    """ PCR """
    profile_denaturation = [
        {'temperature': 98, 'hold_time_seconds': 20},
        {'temperature': 60, 'hold_time_seconds': 20},
        {'temperature': 72, 'hold_time_seconds': 30}]

    # denaturation
    tc.set_block_temperature(98, hold_time_seconds=30)
    tc.execute_profile(steps=profile_denaturation, repetitions=30)

    # extension
    tc.set_block_temperature(72, hold_time_seconds=120)
    tc.set_block_temperature(4)
    tc.open_lid()

    if do_deactivate_tc:
        tc.deactivate_lid()
        tc.deactivate_block()
