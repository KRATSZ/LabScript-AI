metadata = {
    'protocolName': 'Thermocycler Example Protocol',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.0'
    }


def run(protocol):
    [well_vol, lid_temp, input_csv, final_temp, open_lid,
        deactivate_mod] = get_values(  # noqa: F821
            'well_vol', 'lid_temp', 'input_csv', 'final_temp', 'open_lid',
            'deactivate_mod')

    # ex_prof = """cycle,repetitions,"steps (temperature, time in minutes)",,
    # 1,1,"96, 30",,
    # 2,30,"96, 15","60, 30","74, 30"
    # 3,1,"74, 30",,"""
    #
    # [well_vol, lid_temp, input_csv, final_temp, open_lid, deactivate_mod] = [
    #     20, 105, ex_prof, 4, True, True]

    # load thermocycler
    tc_mod = protocol.load_module('thermocycler')

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

    # parse profile input
    profiles_parsed = [
        line.split(',')
        for line in input_csv.splitlines()[1:] if line
        and line.split(',')[0].strip()
    ]

    profiles = [
        {'cycles': int(prof[1]), 'temps': [set for set in prof[2:] if set]}
        for prof in profiles_parsed if len(prof) > 1
    ]
    for p in profiles:
        print(p)

    # Close lid
    if tc_mod.lid_position != 'closed':
        tc_mod.close_lid()

    # lid temperature set
    tc_mod.set_lid_temperature(lid_temp)

    # run profile
    for profile in profiles:
        set = [
            {
                'temperature': float(temp.split(';')[0]),
                'hold_time_minutes': float(temp.split(';')[1])
            }
            for temp in profile['temps']
        ]
        tc_mod.execute_profile(
            steps=set, repetitions=profile['cycles'],
            block_max_volume=well_vol)

    # reach final temperature
    tc_mod.deactivate_lid()
    tc_mod.set_block_temperature(final_temp)

    if open_lid:
        tc_mod.open_lid()

    if deactivate_mod:
        tc_mod.deactivate_block()
