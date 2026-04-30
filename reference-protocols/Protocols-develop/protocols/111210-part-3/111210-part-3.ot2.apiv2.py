metadata = {
    'protocolName': '''GeneRead QIAact Lung RNA Fusion UMI Panel Kit:
                    Second strand synthesis''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples,
        p20_mount] = get_values(  # noqa: F821
        "samples", "p20_mount")

    if not 1 <= samples <= 12:
        raise Exception('''Invalid number of samples.
                        Sample number must be between 1-12.''')

    # Load Labware
    tipracks_20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 6)
    tc_mod = ctx.load_module('thermocycler module')
    tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_nest_wellplate_100ul')
    reagents = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_screwcap', 5)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])

    # Wells
    temp_plate_wells = temp_plate.wells()[:samples]
    nfw = reagents['A1']
    xc_buff = reagents['B1']
    rh_rnase = reagents['C1']
    dntp = reagents['D1']
    bx_enzyme = reagents['A2']

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    ctx.comment('Heating Thermocycler Lid to 103°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_lid_temperature(103)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)

    # Transfer Components
    for well in temp_plate_wells:
        p20.pick_up_tip()
        p20.aspirate(5, nfw)
        p20.dispense(5, well)
        p20.drop_tip()

        p20.pick_up_tip()
        p20.aspirate(2, xc_buff)
        p20.dispense(2, well)
        p20.drop_tip()

        p20.pick_up_tip()
        p20.aspirate(1, rh_rnase)
        p20.dispense(1, well)
        p20.drop_tip()

        p20.pick_up_tip()
        p20.aspirate(1, dntp)
        p20.dispense(1, well)
        p20.drop_tip()

        p20.pick_up_tip()
        p20.aspirate(1, bx_enzyme)
        p20.dispense(1, well)
        p20.mix(7, 10)
        p20.drop_tip()

    ctx.pause('''Please centrifuge the PCR plate with samples and then place it
                onto the thermocycler module.''')

    profile = [
                {'temperature': 37, 'hold_time_minutes': 7},
                {'temperature': 65, 'hold_time_minutes': 10},
                {'temperature': 80, 'hold_time_minutes': 10}]

    tc_mod.close_lid()
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=10)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.pause('''Centrifuge the PCR plate briefly and then place either on ice
                 or the temperature module. Prepare for the next protocol''')
