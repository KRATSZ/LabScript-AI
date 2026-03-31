metadata = {
    'protocolName': '''GeneRead QIAact Lung RNA Fusion UMI Panel Kit:
                    First strand cDNA synthesis''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples, samples_labware,
        p20_mount] = get_values(  # noqa: F821
        "samples", "samples_labware", "p20_mount")

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

    if samples_labware == 'tube':
        sample_plate = ctx.load_labware(
                        'opentrons_24_tuberack_nest_1.5ml_screwcap', 2)
    elif samples_labware == 'plate':
        sample_plate = ctx.load_labware(
                        'nest_96_wellplate_100ul_pcr_full_skirt', 2)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])

    # Wells
    sample_wells = sample_plate.wells()[:samples]
    temp_plate_wells = temp_plate.wells()[:samples]
    rp_primer = reagents['A1']

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Heating Thermocycler to 65°C')
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_block_temperature(65)
    tc_mod.set_lid_temperature(103)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)
    ctx.pause('''Temperature Module has been cooled to 4°C.
              Please place your samples and reagents on the
              temperature module.''')
    ctx.comment('Protocol assumes the samples are 20 ng/uL.')

    # Transfer Samples to Plate on Temp Mod
    for src, dest in zip(sample_wells, temp_plate_wells):
        p20.pick_up_tip()
        p20.aspirate(5, src)
        p20.dispense(5, dest)
        p20.drop_tip()
        p20.pick_up_tip()
        p20.aspirate(1, rp_primer)
        p20.dispense(1, dest)
        p20.mix(7, 4)
        p20.drop_tip()

    ctx.pause('''Please centrifuge the PCR plate with samples and then place it
                onto the thermocycler module.''')

    tc_mod.close_lid()
    tc_mod.set_block_temperature(65, hold_time_minutes=5)
    tc_mod.open_lid()
    ctx.pause('''Place the plate on either the temperature module or on ice for
                at least 2 minutes. Then centrifuge and begin the next part of
                the protocol.''')
