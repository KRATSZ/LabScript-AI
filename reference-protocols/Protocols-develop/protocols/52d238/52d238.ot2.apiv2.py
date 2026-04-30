import math

metadata = {
    'protocolName': 'NEB Ultra II FS DNA Library Prep (Part 2)',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'PCR, Bead Clean up, and Elution',
    'apiLevel': '2.8'
}


def run(ctx):

    [sample_number, m300_mount, m20_mount, pcr,
     bead_clean_up, elution] = get_values(  # noqa: F821
     "sample_number", "m300_mount", "m20_mount",
     "pcr", "bead_clean_up", "elution")

    sample_number = int(sample_number)
    if not sample_number > 1 or sample_number > 48:
        raise Exception("Enter a sample number between 1-48")
    columns = math.ceil(sample_number/8)

    # Load Labware
    tiprack20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul',
                                   1, 'Tip Box 1')
    tiprack200ul = [ctx.load_labware('opentrons_96_filtertiprack_200ul',
                                     slot, f'Tip Box {slot}') for
                    slot in ['2', '3']]
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 6, 'Reservoir')
    index_primers = ctx.load_labware('4titude_framestar_pcr_plate_200ul',
                                     5, 'Index Primers')

    # Load Modules and Plates
    tc_mod = ctx.load_module('thermocycler module')
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    temp_mod = ctx.load_module('temperature module gen2', 4)
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_generic_pcr_strip_200ul')

    mag_mod = ctx.load_module('magnetic module gen2', 9)
    mag_plate = mag_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    # Load Pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                              tip_racks=[tiprack20ul])
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack200ul)

    # Reagents and Samples
    ethanol = reservoir['A1']
    eb_tween = temp_plate['A1']
    trash = ctx.fixed_trash['A1']
    tc_plate_samples = tc_plate.rows()[0][:columns]
    mag_plate_samples = mag_plate.rows()[0][:columns]
    index_primers_samples = index_primers.rows()[0][:columns]

    if pcr:

        m20.transfer(10, index_primers_samples, tc_plate_samples,
                     mix_after=(5, 15), new_tip='always')

        tc_mod.close_lid()
        tc_mod.set_lid_temperature(105)
        tc_mod.set_block_temperature(98, hold_time_seconds=30)

        profile = [
            {'temperature': 98, 'hold_time_minutes': 10},
            {'temperature': 65, 'hold_time_minutes': 1,
             'hold_time_seconds': 15}
        ]

        tc_mod.execute_profile(steps=profile, repetitions=12)
        tc_mod.set_block_temperature(65, hold_time_minutes=5)
        tc_mod.set_block_temperature(4)
        tc_mod.open_lid()

    if bead_clean_up:

        m20.transfer(20, tc_plate_samples, mag_plate_samples,
                     mix_after=(5, 15), new_tip='always')

        ctx.delay(minutes=5, msg='Pausing for 5 minutes...')
        mag_mod.engage()
        ctx.delay(minutes=2, msg='Pausing for 2 minutes...')

        for mag_col in mag_plate_samples:
            m300.pick_up_tip()
            for _ in range(2):
                m300.transfer(25, mag_col, trash, new_tip='never')
            m300.drop_tip()

        for _ in range(2):
            for mag_col in mag_plate_samples:
                m300.pick_up_tip()
                m300.transfer(100, ethanol, mag_col, new_tip='never')
                m300.transfer(110, mag_col, trash, new_tip='never')
                m300.drop_tip()

        ctx.delay(minutes=2, msg="Delaying for 2 minutes to dry...")
        mag_mod.disengage()

    if elution:

        m300.transfer(22, eb_tween, mag_plate_samples, new_tip='always')
