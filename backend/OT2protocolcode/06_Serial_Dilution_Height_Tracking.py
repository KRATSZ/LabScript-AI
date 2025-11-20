"""OPENTRONS."""
import math

metadata = {
    'protocolName': 'Plasma Spike w/Optional Serial Dilution',
    'author': 'John C. Lynch <john.lynch@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx):
    """PROTOCOL."""
    [
     serial_boolean,
     starting_diluent_vol,
     starting_plasma_vol,
     p20_mount
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "serial_boolean",
        "starting_diluent_vol",
        "starting_plasma_vol",
        "p20_mount")

    # define all custom variables above here with descriptions:

    # number of samples
    if p20_mount == 'left':
        p300_side = 'right'
    else:
        p300_side = 'left'

    # load labware
    tube_dual = ctx.load_labware('opentrons_10_tuberack_falcon_4x50ml_'
                                 '6x15ml_conical', '3')
    tube_24 = ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_'
                               'safelock_snapcap', '4')

    # load tipracks
    tip300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
              for slot in ['1']]
    tips20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
              for slot in ['2']]

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2', p300_side, tip_racks=tip300)
    p20 = ctx.load_instrument('p20_single_gen2', p20_mount, tip_racks=tips20)

    # reagents
    diluent = tube_dual.wells()[0]  # 15 mL conical tube
    plasma = tube_dual.wells()[1]  # 15 mL conical tube
    radius_15 = tube_dual.wells()[0].diameter/2
    print(radius_15)
    dilution_targets = tube_24.rows()[0][1:]+tube_24.rows()[1][:]
    dilution_sources = tube_24.rows()[0][:]+tube_24.rows()[1][:]
    plasma_targets = tube_24.rows()[2][:]+tube_24.rows()[3][:]

    h_plasma = (starting_plasma_vol*1000/(math.pi*(radius_15**2)))-3
    h_diluent = (starting_diluent_vol*1000/(math.pi*(radius_15**2)))-3
    print(h_plasma)
    print(h_diluent)

    def adjust_height_plasma(vol, radius):
        nonlocal h_plasma
        dh = vol/(math.pi*radius**2)
        h_plasma -= dh
        if h_plasma < 6:
            h_plasma = 1

    def adjust_height_dil(vol, radius):
        nonlocal h_diluent
        dh = vol/(math.pi*radius**2)
        h_diluent -= dh
        if h_diluent < 6:
            h_diluent = 1

    def bead_mixing(well, pip, mvol, reps=10):
        """bead_mixing."""
        """
        'bead_mixing' will mix liquid that contains beads. This will be done by
        aspirating from the middle of the well & dispensing from the bottom to
        mix the beads with the other liquids as much as possible. Aspiration &
        dispensing will also be reversed to ensure proper mixing.
        param well: The current well that the mixing will occur in.
        param pip: The pipet that is currently attached/ being used.
        param mvol: The volume that is transferred before the mixing steps.
        param reps: The number of mix repetitions that should occur. Note~
        During each mix rep, there are 2 cycles of aspirating from bottom,
        dispensing at the top and 2 cycles of aspirating from middle,
        dispensing at the bottom
        """
        vol = mvol * .9

        pip.move_to(well.center())
        for _ in range(reps):
            pip.aspirate(vol, well.bottom(1), rate=2)
            pip.dispense(vol, well.bottom(5), rate=2)
    # protocol
    # add diluent to tubes 2-12 on 24 rack
    p300.pick_up_tip()
    for dest in dilution_targets:
        p300.aspirate(200, diluent)
        p300.move_to(diluent.top())
        p300.aspirate(20, diluent.top())
        p300.move_to(dest.top())
        p300.dispense(20, dest.top())
        p300.dispense(200, dest)
        adjust_height_plasma(200, radius_15)
        print(h_plasma)
    vol_add_list = [250, 250, 250, 240]

    # add 980uL diluent to tube 1 on 24 rack
    for vol in vol_add_list:
        p300.aspirate(vol, diluent)
        p300.move_to(diluent.top())
        p300.aspirate(20, diluent.top())
        p300.move_to(tube_24.wells()[0].top())
        p300.dispense(20, tube_24.wells()[0].top())
        p300.dispense(vol, tube_24.wells()[0])
    p300.drop_tip()

    #  add 20uL stock solution to tube 1 on the 24 rack
    # p20.pick_up_tip()
    # p20.aspirate(20, stock)
    # p20.dispense(20, tube_24.wells()[0])
    # p20.drop_tip()
    ctx.pause("PLEASE ADD 20 uL OF STOCK SOLUTION TO TUBE A1, ROBOT WILL MIX")

    # mix with p300
    p300.pick_up_tip()
    bead_mixing(tube_24.wells()[0], p300, 300, reps=10)

    # first serial dilution
    p300.aspirate(200, tube_24.wells()[0])
    p300.dispense(200, dilution_targets[0])
    p300.drop_tip()

    # serial dilution
    for src, dest in zip(dilution_targets, dilution_targets[1:]):
        p300.pick_up_tip()
        p300.aspirate(200, src)
        p300.move_to(src.top())
        p300.aspirate(20, src.top())
        p300.move_to(dest.top())
        p300.dispense(20, dest.top())
        p300.dispense(200, dest)
        bead_mixing(dest, p300, 300, reps=10)
        p300.drop_tip()

    # add 100 uL plasma to 13-24 in tube rack
    for dest in plasma_targets:
        p300.pick_up_tip()
        p300.aspirate(100, plasma)
        p300.move_to(plasma.top())
        p300.aspirate(20, plasma.top())
        p300.move_to(dest.top())
        p300.dispense(20, dest.top())
        p300.dispense(100, dest)
        # need tip touch here?
        p300.drop_tip()

    # move 10 uL dilutions to plasma tubes
    for src, dest in zip(dilution_sources, plasma_targets):
        p20.pick_up_tip()
        p20.aspirate(10, src)
        p20.dispense(10, dest)
        # need tip touch here?
        p20.drop_tip()
