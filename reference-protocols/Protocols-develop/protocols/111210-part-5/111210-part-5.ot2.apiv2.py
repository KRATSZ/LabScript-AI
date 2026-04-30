metadata = {
    'protocolName': '''GeneRead QIAact Lung RNA Fusion UMI Panel Kit:
                    Adaptor ligation''',
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
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_96_aluminumblock_nest_wellplate_100ul')
    samples_plate = ctx.load_labware(
                        'nest_96_wellplate_100ul_pcr_full_skirt', 2)
    pcr_plate_deck = ctx.load_labware(
                        'nest_96_wellplate_100ul_pcr_full_skirt', 5)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipracks_200ul])

    # Wells
    ligation_mix = temp_plate['A6']
    adaptors = temp_plate.wells()[:samples]
    samples_plate_wells = samples_plate.wells()[:samples]
    pcr_plate_deck_wells = pcr_plate_deck.wells()[:samples]

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.pause('''Place End repair / dA tailing sample plate in Slot 2
                and a new PCR plate in Slot 5''')
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    ctx.comment('Pre-Cooling Thermocycler Block to 20°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_block_temperature(20)
    tc_mod.open_lid()
    tc_mod.deactivate_lid()
    temp_mod.await_temperature(4)

    ctx.pause('''Place adaptors and ligation master mix tubes
                on the temperature module.''')

    # Transfer Adapters
    for src, dest in zip(adaptors, pcr_plate_deck_wells):
        p20.pick_up_tip()
        p20.aspirate(5, src)
        p20.dispense(5, dest)
        p20.drop_tip()

    # Transfer 50 uL End repair / dA tailing samples
    for src, dest in zip(samples_plate_wells, pcr_plate_deck_wells):
        p300.pick_up_tip()
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.drop_tip()

    # Transfer 45 uL Ligation Mix
    for well in pcr_plate_deck_wells:
        p300.pick_up_tip()
        p300.aspirate(45, ligation_mix)
        p300.dispense(45, well)
        p300.mix(7, 25)
        p300.drop_tip()

    ctx.pause('''Please centrifuge the PCR plate in slot 2 and keep on ice
                or the temperature module while thermocycler reaches 20C.''')

    ctx.pause('Please place plate in thermocycler to begin incubation.')

    tc_mod.close_lid()
    tc_mod.set_block_temperature(20, hold_time_minutes=15,
                                 block_max_volume=100)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.pause('''Protocol complete. Proceed to adapter ligation cleanup.''')
