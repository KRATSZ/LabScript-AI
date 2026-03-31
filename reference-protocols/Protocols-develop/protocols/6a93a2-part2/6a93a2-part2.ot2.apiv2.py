import math

metadata = {
    'protocolName': 'Swift Rapid NGS Part 2 - Adaptase',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, tip_type, overage_percent,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp", "tip_type", "overage_percent",
        "p20_mount", "p300_mount")

    # keep user in range
    num_samp = int(num_samp)
    if not 0.0 <= overage_percent <= 10.0:
        raise Exception("Enter a an overage percent between 5-10%")
    overage_percent = 1+overage_percent/100
    num_cols = math.ceil(int(num_samp/8))

    # load labware
    thermocycler = ctx.load_module('thermocycler')
    samp_plate = thermocycler.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt')
    temperature_mod = ctx.load_module('temperature module gen2', '3')
    alum_tuberack = temperature_mod.load_labware(
                        'opentrons_24_aluminumblock_generic_2ml_screwcap')
    tiprack20 = [ctx.load_labware(tip_type, slot) for slot in ['6', '9']]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['4', '5']]

    # load instruments
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=tiprack300)

    # make Adaptase Mastermix
    temperature_mod.set_temperature(4)
    mastermix = alum_tuberack.rows()[1][0]
    reagents = alum_tuberack.rows()[0][:6]
    vols = [math.ceil(num_samp*rxn_vol*overage_percent)
            for rxn_vol in [2, 2, 1.25, 0.5, 0.5, 4.25]]
    num_cols = math.ceil(int(num_samp/8))
    sample_cols = samp_plate.rows()[0][4:4+num_cols]

    for reagent, vol in zip(reagents, vols):
        p20.pick_up_tip()
        p20.transfer(vol, reagent, mastermix.top(), new_tip='never')
        p20.drop_tip()

    ctx.pause("""Vortex mix Adaptase mix tube (tube B1)
                 After placing mix tube back, thermocycler will warm up.""")

    # operate thermocycler - denature samples
    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    thermocycler.set_lid_temperature(105)
    thermocycler.set_block_temperature(95)
    profile = [{'temperature': 95, 'hold_time_minutes': 2}]
    ctx.pause('''Thermocycler temperature is at 95C.
                Please add the sample plate to the thermocycler.
                Thermocycler will close lid automatically.
                Be ready to take samples and put on ice
                immediately after the 2 minute cycle has completed. ''')

    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile,
                                 repetitions=1,
                                 block_max_volume=10.5)
    thermocycler.open_lid()
    ctx.pause('''Immediately remove samples and put on ice for 2 minutes.
    After, put the plate back on the Thermocycler for the Adaptase Mastermix
    to be added.''')

    # add adaptase and mix thouroughly
    for well in samp_plate.wells()[32:32+num_samp]:
        p20.pick_up_tip()
        p20.aspirate(10.5*overage_percent, mastermix)
        p20.dispense(10.5*overage_percent, well.top())
        p20.drop_tip()

    for col in sample_cols:
        m300.pick_up_tip()
        m300.mix(15, 20, col)
        m300.blow_out()
        m300.drop_tip()

    ctx.pause('''Transfer of Adaptase Mastermix is complete -
    Solutions have been pipette-mixed 15 times.
    Spin samples, seal,  and place back on thermocycler for another
    thermocycler profile.''')

    profile = [
        {'temperature': 37, 'hold_time_minutes': 15},
        {'temperature': 95, 'hold_time_minutes': 2},
    ]
    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile,
                                 repetitions=1,
                                 block_max_volume=20.5)
    thermocycler.set_block_temperature(4, block_max_volume=20.5)
    thermocycler.open_lid()
    ctx.comment('Protocol complete. Samples ready for extension')
