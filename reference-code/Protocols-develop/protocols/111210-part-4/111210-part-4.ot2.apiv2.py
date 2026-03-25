metadata = {
    'protocolName': '''GeneRead QIAact Lung RNA Fusion UMI Panel Kit:
                    End repair / dA tailing''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "samples", "p20_mount", "p300_mount")

    if not 1 <= samples <= 12:
        raise Exception('''Invalid number of samples.
                        Sample number must be between 1-12.''')

    # Load Labware
    tipracks_200ul = ctx.load_labware('opentrons_96_filtertiprack_200ul', 9)
    tipracks_20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 6)
    tc_mod = ctx.load_module('thermocycler module')
    pcr_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_nest_wellplate_100ul')
    reagents = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_screwcap', 5)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipracks_200ul])

    # Wells
    temp_plate_wells = temp_plate.wells()[:samples]
    pcr_plate_wells = pcr_plate.wells()[:samples]
    nfw = reagents['A1']
    era_buff = reagents['B1']
    era_enzyme = reagents['C1']

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    ctx.comment('Heating Thermocycler Lid to 70°C')
    ctx.comment('Pre-Cooling Thermocycler Block to 4°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_lid_temperature(103)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)

    # Add 15 ul of NFW
    for well in pcr_plate_wells:
        p20.pick_up_tip()
        p20.aspirate(15, nfw)
        p20.dispense(15, well)
        p20.drop_tip()

    # Add 5 ul ERA Buffer
    for well in pcr_plate_wells:
        p20.pick_up_tip()
        p20.aspirate(5, era_buff)
        p20.dispense(5, well)
        p20.drop_tip()

    # Transfer 20 uL of Mix
    for src, dest in zip(temp_plate_wells, pcr_plate_wells):
        p20.pick_up_tip()
        p20.aspirate(20, src)
        p20.dispense(20, dest)
        p20.drop_tip()

    # Transfer 10 uL of ERA Enzyme
    for well in pcr_plate_wells:
        p20.pick_up_tip()
        p20.aspirate(10, era_enzyme)
        p20.dispense(10, well)
        p20.drop_tip()
        p300.pick_up_tip()
        p300.mix(7, 25, well)
        p300.drop_tip()

    ctx.pause('''Please centrifuge the PCR plate with samples and then return it
                onto the thermocycler module.''')

    profile = [
                {'temperature': 4, 'hold_time_minutes': 1},
                {'temperature': 20, 'hold_time_minutes': 30},
                {'temperature': 65, 'hold_time_minutes': 30}]

    tc_mod.close_lid()
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=50)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.pause('''Centrifuge the PCR plate briefly and then place either on ice
                 or the temperature module. Prepare for the next protocol''')
