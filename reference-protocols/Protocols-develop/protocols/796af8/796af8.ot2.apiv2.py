import math

metadata = {
    'protocolName': 'NEB Ultra II FS DNA Library Prep',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(ctx):

    [sample_number, m300_mount, m20_mount, end_repair,
        adapter_ligation, bead_clean_up] = get_values(  # noqa: F821
        "sample_number", "m300_mount", "m20_mount",
        "end_repair", "adapter_ligation", "bead_clean_up")

    sample_number = int(sample_number)
    if not sample_number > 1 or sample_number > 48:
        raise Exception("Enter a sample number between 1-48")
    columns = math.ceil(sample_number/8)

    # Load Labware
    tiprack20ul = [ctx.load_labware('opentrons_96_filtertiprack_20ul',
                   slot, f'Tip Box {box}') for slot, box in
                   zip(['1', '2', '5'], ['1', '2', '4'])]
    tiprack200ul = ctx.load_labware('opentrons_96_filtertiprack_200ul',
                                    3, 'Tip Box 3')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 6)

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
                              tip_racks=tiprack20ul)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=[tiprack200ul])

    # Reagents and Samples
    ethanol = reservoir['A1']
    endprep_mm = temp_plate['A1']
    adapter_mm = temp_plate['A2']
    pcr_mm = temp_plate['A3']
    tc_plate_samples = tc_plate.rows()[0][:columns]
    mag_plate_samples = mag_plate.rows()[0][:columns]
    trash = ctx.fixed_trash['A1']

    # Set Temp Mod to 4C
    temp_mod.set_temperature(4)

    # End Repair
    if end_repair:

        # Transfer Master Mix
        m20.transfer(6.25, endprep_mm, tc_plate_samples, mix_after=(5, 8),
                     touch_tip=True, new_tip="always")

        # Begin Theromcycler Process
        tc_mod.close_lid()
        tc_mod.set_lid_temperature(75)
        tc_mod.set_block_temperature(37, hold_time_minutes=10)
        tc_mod.set_block_temperature(65, hold_time_minutes=30)
        tc_mod.set_block_temperature(20)

    # Adaptor Ligation
    if adapter_ligation:

        tc_mod.open_lid()
        m20.transfer(10, adapter_mm, tc_plate_samples, mix_after=(5, 12),
                     new_tip="always")

        # Begin Theromcycler Process
        tc_mod.set_block_temperature(20, hold_time_minutes=15)
        tc_mod.set_block_temperature(4)

    # Bead Clean Up
    if bead_clean_up:

        m20.transfer(20, tc_plate_samples, mag_plate_samples,
                     mix_after=(5, 12), new_tip="always")
        ctx.delay(minutes=5, msg="Pausing for 5 minutes")

        mag_mod.engage()
        ctx.delay(minutes=2, msg="Engaging magnet for 2 minutes...")

        # Steps 22-26
        for mag_col in mag_plate_samples:
            m20.pick_up_tip()
            for _ in range(2):
                m20.transfer(20, mag_col, trash, new_tip='never')
            m20.drop_tip()

        # Steps 27-36
        for _ in range(2):
            for mag_col in mag_plate_samples:
                m300.pick_up_tip()
                m300.transfer(100, ethanol, mag_col, new_tip='never')
                m300.transfer(100, ethanol, trash, new_tip='never')
                m300.drop_tip()

        # Steps 37-41
        ctx.delay(minutes=2, msg="Delaying for 2 minutes to dry...")
        mag_mod.disengage()
        m20.transfer(13, pcr_mm, mag_plate_samples, new_tip='always')
