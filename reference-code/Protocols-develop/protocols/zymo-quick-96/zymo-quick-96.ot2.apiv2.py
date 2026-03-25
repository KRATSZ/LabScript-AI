from opentrons import types
import math

metadata = {
    'protocolName': 'Zymo Quick-DNA/RNA Viral Kit [Custom]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.10'
}


def run(protocol):
    [numSamps, p300m, pipMnt, mag_gen] = get_values(  # noqa: F821
        'numSamps', 'p300m', 'pipMnt', 'mag_gen')

    # load labware and pipettes
    numCols = math.ceil(numSamps/8)
    tips200 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in [
                '8', '5', '9', '6', '2'
                ]
            ]
    allTips = [t for rack in tips200 for t in rack.rows()[0]]
    mixTips = allTips[:numCols]
    trashTips = allTips[numCols:]
    p300 = protocol.load_instrument(p300m, pipMnt, tip_racks=tips200)

    magdeck = protocol.load_module(mag_gen, '7')
    magheight = 13.7 if mag_gen == 'magdeck' else 6.85
    magplate = magdeck.load_labware('vwr_96_wellplate_1000ul')
    flatplate = protocol.load_labware(
                'nest_96_wellplate_100ul_pcr_full_skirt', '3')
    wasteres = [protocol.load_labware(
                'nest_1_reservoir_195ml', s, 'Liquid Waste') for s in [10, 11]]
    waste1 = wasteres[0]['A1'].top()
    waste2 = wasteres[1]['A1'].top()
    trough2 = protocol.load_labware(
                'nest_12_reservoir_15ml', '1', '12-Reservoir with Reagents')
    trough = protocol.load_labware(
                'nest_12_reservoir_15ml', '4', '12-Reservoir with Reagents')

    buffer = [w for w in trough.wells()[:4] for _ in range(3)][:numCols]
    wb1 = [w for w in trough.wells()[4:8] for _ in range(3)][:numCols]
    wb2 = [w for w in trough.wells()[8:] for _ in range(3)][:numCols]
    ethanol1 = [w for w in trough2.wells()[:4] for _ in range(3)][:numCols]
    ethanol2 = [w for w in trough2.wells()[4:8] for _ in range(3)][:numCols]
    water = trough2['A12']

    magsamps = magplate.rows()[0][:numCols]
    elutes = flatplate.rows()[0][:numCols]
    sides = [1, -1]*6

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 150
    p300.flow_rate.blow_out = 300

    def well_mix(reps, loc, vol, s):
        loc1 = loc.bottom().move(types.Point(x=s, y=0, z=0.6))
        loc2 = loc.bottom().move(types.Point(x=s, y=0, z=5.5))
        p300.aspirate(20, loc1)
        mvol = vol-20
        for _ in range(reps-1):
            p300.aspirate(mvol, loc1)
            p300.dispense(mvol, loc2)
        p300.dispense(20, loc2)

    def init_well_mix(reps, loc, vol, s):
        loc1 = loc.bottom().move(types.Point(x=s, y=0, z=0.6))
        loc2 = loc.bottom().move(types.Point(x=s, y=0, z=5.5))
        loc3 = loc.bottom().move(types.Point(x=-s, y=0, z=0.6))
        loc4 = loc.bottom().move(types.Point(x=-s, y=0, z=5.5))
        p300.aspirate(20, loc1)
        for _ in range(reps-1):
            p300.aspirate(vol, loc1)
            p300.dispense(vol, loc4)
            p300.aspirate(vol, loc3)
            p300.dispense(vol, loc2)
        p300.dispense(20, loc2)

    # def wash mix - dispense on pellet

    def wash_mix(reps, loc, vol):
        loc1 = loc.bottom().move(types.Point(x=1, y=0, z=0.6))
        loc2 = loc.bottom().move(types.Point(x=-1, y=0, z=4))
        p300.aspirate(20, loc2)
        mvol = vol-20
        for _ in range(reps-1):
            p300.aspirate(mvol, loc2)
            p300.dispense(mvol, loc1)
        p300.dispense(20, loc2)

    tipNum = 0

    def _drop_tip():
        nonlocal tipNum
        p300.drop_tip(trashTips[tipNum])
        tipNum += 1

    # transfer 600ul of buffer
    protocol.comment('Adding viral buffer + beads to samples:')
    for well, reagent, side in zip(magsamps, buffer, sides):
        p300.pick_up_tip()
        for _ in range(2):
            p300.aspirate(200, reagent)
            p300.dispense(200, well.top(-5))
            p300.aspirate(10, well.top(-5))
        p300.aspirate(200, reagent)
        p300.dispense(220, well.top(-10))
        init_well_mix(2, well, 160, side)
        p300.blow_out()
        init_well_mix(2, well, 160, side)
        p300.aspirate(20, well.top(-5))
        p300.drop_tip()

    # mix magbeads for 10 minutes
    protocol.comment('Mixing samples+buffer+beads:')
    for well, tip, side in zip(magsamps, mixTips, sides):
        p300.pick_up_tip()
        init_well_mix(8, well, 130, side)
        init_well_mix(8, well, 130, side)
        p300.blow_out()
        p300.drop_tip(tip)

    magdeck.engage(height=magheight)
    protocol.comment('Incubating on magdeck for 5 minutes')
    protocol.delay(minutes=5)

    # Step 5 - Remove supernatant
    def supernatant_removal(vol, src, dest, s, zz=0.5):
        p300.flow_rate.aspirate = 20
        tvol = vol
        asp_ctr = 0
        while tvol > 180:
            p300.aspirate(
                180, src.bottom().move(types.Point(x=-s, y=0, z=zz)))
            p300.dispense(180, dest)
            p300.aspirate(10, dest)
            tvol -= 180
            asp_ctr += 1
            if zz > 10:
                zz -= 10
        p300.aspirate(
            tvol, src.bottom().move(types.Point(x=-s, y=0, z=0.5)))
        dvol = 10*asp_ctr + tvol
        p300.dispense(dvol, dest)
        p300.flow_rate.aspirate = 50

    protocol.comment('Removing supernatant:')

    for well, tip, side in zip(magsamps, mixTips, sides):
        p300.pick_up_tip(tip)
        supernatant_removal(900, well, waste1, side, zz=25)
        p300.return_tip()

    magdeck.disengage()

    def wash_step(src, mtimes, wasteLoc, msg):
        protocol.comment(f'Wash Step {msg} - Adding to samples:')
        p300.pick_up_tip()
        for well, s in zip(magsamps, src):
            for _ in range(2):
                p300.aspirate(165, s)
                p300.dispense(165, well.top(-3))
                p300.aspirate(10, well.top(-3))
            p300.aspirate(165, s)
            p300.dispense(185, well.top(-3))
            protocol.delay(seconds=1)
        _drop_tip()

        for well, tip, s, side in zip(magsamps, mixTips, src, sides):
            p300.pick_up_tip(tip)
            well_mix(mtimes, well, 180, side)
            p300.blow_out()
            p300.return_tip()

        magdeck.engage(height=magheight)
        protocol.comment('Incubating on MagDeck for 3 minutes.')
        protocol.delay(minutes=3)

        protocol.comment(f'Removing supernatant from Wash {msg}:')
        for well, tip, side in zip(magsamps, mixTips, sides):
            p300.pick_up_tip(tip)
            supernatant_removal(520, well, wasteLoc, side)
            p300.return_tip()
        magdeck.disengage()

    wash_step(wb1, 20, waste1, '1 Wash Buffer 1')

    wash_step(wb2, 10, waste1, '2 Wash Buffer 2')

    wash_step(ethanol1, 10, waste2, '3 Ethanol 1')

    wash_step(ethanol2, 10, waste2, '4 Ethanol 2')

    protocol.comment('Allowing beads to air dry for 2 minutes.')
    protocol.delay(minutes=2)

    p300.flow_rate.aspirate = 20
    protocol.comment('Removing any excess ethanol from wells:')
    for well, tip, side in zip(magsamps, mixTips, sides):
        p300.pick_up_tip(tip)
        s = side*-0.5
        p300.transfer(
            180, well.bottom().move(types.Point(x=s, y=0, z=0.4)),
            waste2, new_tip='never')
        p300.return_tip()
    p300.flow_rate.aspirate = 50

    protocol.comment('Allowing beads to air dry for 10 minutes.')
    protocol.delay(minutes=10)

    magdeck.disengage()

    protocol.comment('Adding NF-Water to wells for elution:')
    for well, side in zip(magsamps, sides):
        p300.pick_up_tip()
        p300.aspirate(20, water.top())
        p300.aspirate(50, water)
        for _ in range(15):
            p300.dispense(
                40, well.bottom().move(types.Point(x=side, y=0, z=2)))
            p300.aspirate(
                40, well.bottom().move(types.Point(x=side, y=0, z=0.5)))
        p300.dispense(70, well)
        p300.blow_out()
        _drop_tip()

    protocol.comment('Incubating at room temp for 10 minutes.')
    protocol.delay(minutes=10)

    # Step 21 - Transfer elutes to clean plate
    magdeck.engage(height=magheight)
    protocol.comment('Incubating on MagDeck for 2 minutes.')
    protocol.delay(minutes=2)

    protocol.comment('Transferring elution to final plate:')
    p300.flow_rate.aspirate = 10
    for src, dest, side in zip(magsamps, elutes, sides):
        p300.pick_up_tip()
        p300.aspirate(50, src.bottom().move(types.Point(x=-side, y=0, z=0.6)))
        p300.dispense(50, dest)
        _drop_tip()

    magdeck.disengage()

    protocol.comment('Congratulations!')
