from opentrons import protocol_api

metadata = {
    'protocolName': '''GeneRead QIAact Lung RNA Fusion UMI Panel Kit:
                       Target Enrichment PCR''',
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
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
                    'opentrons_24_aluminumblock_nest_1.5ml_screwcap')
    pcr_tubes = ctx.load_labware(
                    'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                    2)

    # Load Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount,
                              tip_racks=[tipracks_20ul])

    # Helper Functions
    def pick_up(pip, loc=None):
        try:
            if loc:
                pip.pick_up_tip(loc)
            else:
                pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            pip.pause("Please replace the empty tip racks!")
            pip.reset_tipracks()
            pip.pick_up_tip()

    # Wells
    tc_plate_wells_forward = tc_plate.wells()[:samples]
    tc_plate_wells_reverse = tc_plate.wells()[80:80+samples]
    forward_mm = temp_plate['A1']
    reverse_mm = temp_plate['B1']
    forward_pcr_wells = pcr_tubes.wells()[:samples]
    reverse_pcr_wells = pcr_tubes.wells()[80:80+samples]

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    temp_mod.set_temperature(4)
    ctx.pause('''Temperature Module has been cooled to 4°C.
              Please place your samples and reagents on the
              temperature module.''')

    # Add Master Mix to PCR Tubes with DNA Library
    for well in forward_pcr_wells:
        pick_up(p20)
        p20.aspirate(10.6, forward_mm)
        p20.dispense(10.6, well)
        p20.mix(7, 10)
        p20.drop_tip()

    for well in reverse_pcr_wells:
        pick_up(p20)
        p20.aspirate(10.6, reverse_mm)
        p20.dispense(10.6, well)
        p20.mix(7, 10)
        p20.drop_tip()

    ctx.pause('''Centrifuge tubes as needed and return them to the
                 aluminum block.''')

    # Transfer Reactions to PCR Plate in thermal cycler
    tc_mod.open_lid()
    for src, dest in zip(forward_pcr_wells, tc_plate_wells_forward):
        pick_up(p20)
        p20.aspirate(20, src)
        p20.dispense(20, dest)
        p20.drop_tip()

    for src, dest in zip(reverse_pcr_wells, tc_plate_wells_reverse):
        pick_up(p20)
        p20.aspirate(20, src)
        p20.dispense(20, dest)
        p20.drop_tip()

    tc_mod.set_lid_temperature(103)

    profile = [
        {'temperature': 95, 'hold_time_seconds': 15},
        {'temperature': 68, 'hold_time_minutes': 10}
    ]

    tc_mod.set_block_temperature(95, hold_time_minutes=15, block_max_volume=20)
    tc_mod.execute_profile(steps=profile, repetitions=8, block_max_volume=20)
    tc_mod.set_block_temperature(72, hold_time_minutes=5, block_max_volume=20)
    tc_mod.set_block_temperature(4, hold_time_minutes=5, block_max_volume=20)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    tc_mod.deactivate_lid()

    ctx.comment('Protocol Complete!')
