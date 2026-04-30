from opentrons import protocol_api

metadata = {
    'protocolName': '''GeneRead QIAact Lung DNA UMI Panel Kit: Adapter
                       Ligation''',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [samples, p300_mount,
        p20_mount] = get_values(  # noqa: F821
        "samples", "p300_mount", "p20_mount")

    if not 1 <= samples <= 12:
        raise Exception('''Invalid number of samples.
                        Sample number must be between 1-12.''')

    # Load Labware
    tipracks_200ul = ctx.load_labware('opentrons_96_filtertiprack_200ul', 9)
    tipracks_20ul = ctx.load_labware('opentrons_96_filtertiprack_20ul', 6)
    tc_mod = ctx.load_module('thermocycler module')
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    temp_mod = ctx.load_module('temperature module gen2', 3)
    temp_plate = temp_mod.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_snapcap')
    pcr_tubes = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        2)

    # Load Pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=[tipracks_200ul])
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
    tc_plate_wells = tc_plate.wells()[:samples]
    adapter_wells = temp_plate.wells()[:samples]
    ligation_mm = temp_plate['A6']
    pcr_tube_wells = pcr_tubes.wells()[:samples]
    lig_buff = temp_plate['B6']
    dna_lig = temp_plate['C6']
    lig_sol = temp_plate['D6']

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Cooling Thermocycler to 4°C')
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)
    ctx.pause('''Temperature Module has been cooled to 4°C.
              Please place your samples and reagents on the
              temperature module.''')

    # Mix Ligation Master Mix
    lig_buff_vol = 10*samples+5
    dna_lig_vol = 5*samples+2.5
    lig_sol_vol = 7.2*samples+3.6

    pip = p300 if lig_buff_vol > 20 else p20
    pick_up(pip)
    pip.aspirate(lig_buff_vol, lig_buff)
    pip.dispense(lig_buff_vol, ligation_mm)
    pip.blow_out()
    pip.drop_tip()

    pip = p300 if dna_lig_vol > 20 else p20
    pick_up(pip)
    pip.aspirate(dna_lig_vol, dna_lig)
    pip.dispense(dna_lig_vol, ligation_mm)
    pip.blow_out()
    pip.drop_tip()

    pip = p300 if lig_sol_vol > 20 else p20
    pick_up(pip)
    pip.aspirate(lig_sol_vol, lig_sol)
    pip.dispense(lig_sol_vol, ligation_mm)
    pip.blow_out()
    pip.drop_tip()

    # Mix Master Mix
    pip = p300 if lig_buff_vol + dna_lig_vol + lig_sol_vol > 20 else p20
    pick_up(pip)
    pip.mix(10, 50, ligation_mm)
    pip.blow_out(ligation_mm.top())
    pip.drop_tip()

    # Add Adapters to PCR Tubes
    ctx.comment(f'Transferring {samples} Adapters to {samples} PCR Tubes')
    for src, dest in zip(adapter_wells, pcr_tube_wells):
        pick_up(p20)
        p20.aspirate(2.8, src)
        p20.dispense(2.8, dest)
        p20.blow_out()
        p20.drop_tip()

    # Transfer 25 µl of each fragmentation, end-repair and
    # A-addition product to PCR tubes
    for src, dest in zip(tc_plate_wells, pcr_tube_wells):
        pick_up(p300)
        p300.aspirate(25, src)
        p300.dispense(25, dest)
        p300.blow_out()
        p300.drop_tip()

    # Add Ligation Master Mix to PCR Tubes
    for dest in pcr_tube_wells:
        pick_up(p300)
        p300.aspirate(22.2, ligation_mm)
        p300.dispense(22.2, dest)
        p300.mix(7, 25)
        p300.blow_out()
        p300.drop_tip()

    ctx.pause('''Please centrifuge the PCR tubes and rest them on ice. Replace
                 the PCR plate with a new plate in the thermocycler. Click
                 Resume to set the thermocycler to 20°C.''')
    tc_mod.set_block_temperature(20)
    ctx.pause('''Thermocycler is set to 20°C. Please put the PCR tubes into the
                aluminum block in deck slot 2 to begin transferring reaction
                mixture to PCR plate in the thermocycler.''')

    # Transfer Reaction Mixtures to PCR Plate in Thermocycler
    for src, dest in zip(pcr_tube_wells, tc_plate_wells):
        pick_up(p300)
        p300.aspirate(50, src)
        p300.dispense(50, dest)
        p300.blow_out()
        p300.drop_tip()

    # Incubate Reaction for 15 mins at 20C
    tc_mod.close_lid()
    tc_mod.set_block_temperature(20, hold_time_minutes=15, block_max_volume=50)
    tc_mod.open_lid()
    ctx.comment('Protocol Complete!')
