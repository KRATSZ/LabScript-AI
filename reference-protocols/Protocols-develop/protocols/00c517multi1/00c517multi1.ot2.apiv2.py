import math

metadata = {
    'protocolName': 'VIB UGENT - Multi-channel Workflow Part 1',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp, test_mode, m300_mount, m20_mount] = get_values(  # noqa: F821
        "num_samp", "test_mode", "m300_mount", "m20_mount")

    # m300_mount = 'left'
    # m20_mount = 'right'
    # num_samp = 96

    # labware
    strip_tube_plate = ctx.load_labware('3dprint_96_tuberack_200ul', 1)
    agilent_1400 = ctx.load_labware('agilent_96_wellplate_1400ul', 2)
    s_trap_plate = ctx.load_labware('protifistrap_96_wellplate_400ul', 3)
    reagent_plate = ctx.load_labware('nest_12_reservoir_15ml', 4)
    # agilent_500 = [ctx.load_labware('agilent_96_wellplate_500ul', slot)
    #                for slot in [7, 8, 9, 11]]
    if not ctx.is_simulating:
        hs_mod = ctx.load_module('heaterShakerModuleV1', 10)
        hs_plate = hs_mod.load_labware('agilent_96_wellplate_1400ul')
        hs_mod.close_labware_latch()
    else:
        hs_plate = ctx.load_labware('agilent_96_wellplate_1400ul', 10)
        hs_plate = hs_plate
    tips20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
              for slot in [5]]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in [6]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips300)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)

    # mapping
    trypsin = reagent_plate.rows()[0][0]

    num_col = math.ceil(num_samp/8)
    sample_cols = agilent_1400.rows()[0][:num_col]

    # protocol
    ctx.pause('''
    Place the following labware on the deck: 3D-print tuberack containing
    a PCR strip with TCEP/CAA on slot 1,
    sample plate (Agilent with square wells, 1400 µl) containing 50 µl sample
    on slot 2, S-trap plate on slot 3, 12-well reservoir on slot 4,
    20 µl tip rack on slot 5 and 300 µl tiprack on slot 6.
    Make sure the heater-shaker is on slot 10.
    ''')
    ctx.comment('\n---------------27 - ADD TCEP+CAA----------------\n\n')
    tcep = strip_tube_plate.wells()[0]
    for col in sample_cols:
        m20.pick_up_tip()
        m20.aspirate(7, tcep)
        m20.dispense(7, col)
        m20.mix(3, 20, col)
        m20.drop_tip()
    # step 30

    if not test_mode:
        if not ctx.is_simulating:
            hs_mod.set_and_wait_for_temperature(95)
    else:
        ctx.comment('skipping temperature to 95 for test mode')

    if not ctx.is_simulating:
        hs_mod.open_labware_latch()

    ctx.pause('''
                 Wrap plate with tin foil and transfer plate to heater-shaker
                 at 95°C. Incubate for 10 min on heater-shaker.
                 TCEP/CAA can be removed from slot 1
    ''')

    try:

        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(750)
    except UnboundLocalError:
        pass

    if not test_mode:
        ctx.delay(minutes=10)
    else:
        ctx.comment('skipping 10 minute delay for test mode')
    try:
        hs_mod.deactivate_heater()
        hs_mod.deactivate_shaker()
    except UnboundLocalError:
        pass

    ctx.pause('''
    Put plate containing reduced and alkylated samples on ice for 1 min.
    After cool-down process manually until protease digest.
    Put S-Trap plate containing sample on slot 3.
    ''')

    ctx.comment('\n---------------40 - ADD TRYPSIN----------------\n\n')
    m300.pick_up_tip()
    for col in s_trap_plate.rows()[0][:num_col]:
        m300.aspirate(125, trypsin)
        m300.dispense(125, col)
    m300.drop_tip()

    ctx.pause('''
    Check that all protease solution is at the bottom of the S-trap columns.
    If not, tap the S-trap plate until all solution is
    covering the S-trap material.
    Incubate S-trap plate with cover
    (do not seal tightly!) in incubator at 37°C overnight.
    Do not shake!
    Store leftover trypsin solution at -20°C. After digestion, perform elution
    with the TECAN Resolvex A200 or centrifuge.
    Dry eluted peptides (in 96-well plate) with a vaccuum concentrator.
    ''')
