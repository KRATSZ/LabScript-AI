# metadata
metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(ctx):

    p20_mount, p300_mount = get_values(  # noqa: F821
        'p20_mount', 'p300_mount')
    # p20_mount, p300_mount = ['left', 'right']

    tc = ctx.load_module('thermocycler')
    tc_plate = tc.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'reaction plate')
    if tc.lid_position == 'closed':
        tc.open_lid()
    gel_plate = ctx.load_labware(
        'corning_96_wellplate_360ul_flat', '1', 'gel samples plate')
    tempdeck = ctx.load_module('tempdeck', '4')
    reagents_plate = tempdeck.load_labware(
        'usascientific_96_wellplate_2.4ml_deep', 'reagent plate')
    tempdeck.set_temperature(4)
    racks20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['2', '3', '5']
    ]
    racks300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['6']
    ]
    primers_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul',
        '9', 'primers plate')

    # pipettes
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=racks20)
    m300 = ctx.load_instrument('p300_multi', p300_mount, tip_racks=racks300)

    # reagents
    dntps = reagents_plate.columns()[0][0]
    polymerase = reagents_plate.columns()[0][1]
    pcr_buff = reagents_plate.columns()[1][0]

    # create mastermix
    m300.pick_up_tip()
    m300.transfer(
        45,
        pcr_buff,
        reagents_plate.columns()[4][0],
        air_gap=30,
        new_tip='never'
    )
    m300.blow_out(reagents_plate.columns()[3][0].top(-2))
    m300.drop_tip()

    for reagent in [dntps, polymerase]:
        p20.distribute(
            9, dntps, [d for d in reagents_plate.columns(2)], air_gap=1)

    for s, d in zip(reagents_plate.columns()[2], reagents_plate.columns()[3]):
        p20.pick_up_tip()
        p20.transfer(9, s, d, air_gap=1, new_tip='never')
        p20.blow_out(d.top(-2))
        p20.drop_tip()

    # transfer contents to thermocycler plate
    m300.distribute(
        30, reagents_plate.columns()[3][0], tc_plate.rows()[0], air_gap=30)

    primers = [well for row in primers_plate.rows() for well in row]
    primer_dests = [well for row in tc_plate.rows() for well in row]

    # transfer corresponding primers to reactions
    for s, d in zip(primers, primer_dests):
        p20.pick_up_tip()
        p20.aspirate(5, s.top())
        p20.aspirate(2, s.bottom(0.5))
        p20.aspirate(5, d)
        p20.dispense(12, d)
        p20.blow_out(d.top(-2))
        p20.drop_tip()

    tc.close_lid()
    tc.set_lid_temperature(105)
    tc.set_block_temperature(temperature=95, hold_time_seconds=120)
    profile = [
        {'temperature': 95, 'hold_time_seconds': 30},
        {'temperature': 57, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 60}
    ]
    tc.execute_profile(steps=profile, repetitions=20, block_max_volume=32)
    tc.set_block_temperature(temperature=72, hold_time_minutes=10)
    tc.deactivate_lid()
    tc.open_lid()

    rxn_sources = primer_dests
    gel_dests = [well for row in gel_plate.rows() for well in row]

    # transfer corresponding primers to reactions
    for s, d in zip(rxn_sources, gel_dests):
        p20.pick_up_tip()
        p20.aspirate(5, s.top())
        p20.aspirate(5, s)
        p20.dispense(10, d)
        p20.blow_out(d.top(-2))
        p20.drop_tip()

    ctx.comment('Thermocycler block remaining at 72˚C incubation. Deactivate \
through Opentrons App when ready.')
