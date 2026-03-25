metadata = {
    'protocolName': 'Thermocycler Example Protocol',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.13'
    }


def run(protocol):
    [type_tc, well_vol, lid_temp, init_temp, init_time,
        type_tc, d_temp, d_time, a_temp, a_time,
        e_temp, e_time, no_cycles,
        fe_temp, fe_time, final_temp] = get_values(  # noqa: F821
        'type_tc', 'well_vol', 'lid_temp', 'init_temp', 'init_time',
        'type_tc', 'd_temp', 'd_time', 'a_temp', 'a_time',
        'e_temp', 'e_time', 'no_cycles',
        'fe_temp', 'fe_time', 'final_temp')

    tc_mod = protocol.load_module(type_tc)

    """
    Add liquid transfers here, if interested (make sure TC lid is open)
    Example (Transfer 50ul of Sample from plate to Thermocycler):

    tips = [protocol.load_labware('opentrons_96_tiprack_300ul', '2')]
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=tips)
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    sample_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '1')

    tc_wells = tc_plate.wells()
    sample_wells = sample_plate.wells()

    if tc_mod.lid_position != 'open':
        tc_mod.open_lid()

    for t, s in zip(tc_wells, sample_wells):
        pipette.transfer(50, s, t)
    """

    # Close lid
    if tc_mod.lid_position != 'closed':
        tc_mod.close_lid()

    # lid temperature set
    tc_mod.set_lid_temperature(lid_temp)

    # initialization
    tc_mod.set_block_temperature(init_temp, hold_time_seconds=init_time,
                                 block_max_volume=well_vol)

    # run profile
    profile = [
        {'temperature': d_temp, 'hold_time_seconds': d_time},
        {'temperature': a_temp, 'hold_time_seconds': a_time},
        {'temperature': e_temp, 'hold_time_seconds': e_time}
    ]

    tc_mod.execute_profile(steps=profile, repetitions=no_cycles,
                           block_max_volume=well_vol)

    # final elongation

    tc_mod.set_block_temperature(fe_temp, hold_time_seconds=fe_time,
                                 block_max_volume=well_vol)

    # final hold
    tc_mod.deactivate_lid()
    tc_mod.set_block_temperature(final_temp)
