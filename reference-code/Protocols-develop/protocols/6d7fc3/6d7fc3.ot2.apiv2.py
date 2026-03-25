from opentrons import protocol_api

metadata = {
    'protocolName': '''GeneRead QIAact Lung DNA UMI Panel Kit: Fragmentation,
    End-repair and A-addition''',
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

    # if samples_labware == 'tube':
    #     sample_plate = ctx.load_labware(
    #                     'opentrons_24_tuberack_nest_2ml_snapcap', 2)
    # elif samples_labware == 'plate':
    #     sample_plate = ctx.load_labware(
    #                     'nest_96_wellplate_100ul_pcr_full_skirt', 2)

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
    # sample_wells = sample_plate.wells()[:samples]
    tc_plate_wells = tc_plate.wells()[:samples]
    mm = temp_plate['A1']
    frag_enzyme_mix = temp_plate['B1']
    frag_buff = temp_plate['A2']
    fera = temp_plate['B2']

    # Protocol Steps

    # Pre-Cool Thermocycler and Temperature Module to 4C
    ctx.comment('Pre-Cooling Thermocycler to 4°C')
    ctx.comment('Pre-Cooling Temperature Module to 4°C')
    temp_mod.start_set_temperature(4)
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    temp_mod.await_temperature(4)
    ctx.pause('''Temperature Module has been cooled to 4°C.
              Please place your reagents on the
              temperature module.''')

    # Prepre Master Mix
    frag_buff_vol = 2.5*samples+1.2
    fera_vol = 0.75*samples+0.4

    pip = p300 if frag_buff_vol > 20 else p20
    pick_up(pip)
    pip.aspirate(frag_buff_vol, frag_buff)
    pip.dispense(frag_buff_vol, mm)
    pip.blow_out()
    pip.drop_tip()

    pip = p300 if fera_vol > 20 else p20
    pick_up(pip)
    pip.aspirate(fera_vol, fera)
    pip.dispense(fera_vol, mm)
    pip.blow_out()
    pip.drop_tip()

    # Mix Master Mix
    pip = p300 if frag_buff_vol + fera_vol > 20 else p20
    pick_up(pip)
    pip.mix(10, frag_buff_vol+fera_vol, mm)
    pip.blow_out(mm.top())
    pip.drop_tip()

    # Transfer 3.25 uL of Master Mix to Thermocycler Reaction Plate
    for dest in tc_plate_wells:
        pick_up(p20)
        p20.aspirate(3.25, mm)
        p20.dispense(3.25, dest)
        p20.mix(10, 10)
        p20.blow_out()
        p20.drop_tip()

    # Transfer 5 uL of Fragmentation Enzyme Mix to Thermocycler Reaction Plate
    for dest in tc_plate_wells:
        pick_up(p20)
        p20.aspirate(5, frag_enzyme_mix)
        p20.dispense(5, dest)
        p20.mix(10, 15)
        p20.blow_out()
        p20.drop_tip()

    # Thermocycler Steps
    profile = [
        {'temperature': 4, 'hold_time_minutes': 1},
        {'temperature': 32, 'hold_time_minutes': 24},
        {'temperature': 72, 'hold_time_minutes': 30}
    ]

    tc_mod.set_lid_temperature(103)
    tc_mod.close_lid()
    tc_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=25)
    tc_mod.deactivate_lid()
    tc_mod.set_block_temperature(4)
    tc_mod.open_lid()
    ctx.comment('Protocol Completed! Prepare for Adapter Ligation.')
