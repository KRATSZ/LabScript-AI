from opentrons import types
import math

metadata = {
    'protocolName': 'MGI Easy Nucleic Acid Extraction Kit',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [numSamps, sampPlate, extrPlate,
     elutePlate, p300mnt, tipType, tipTrash] = get_values(  # noqa: F821
     'numSamps', 'sampPlate', 'extrPlate',
     'elutePlate', 'p300mnt', 'tipType', 'tipTrash')

    # load labware and pipette
    m300 = protocol.load_instrument('p300_multi_gen2', p300mnt)

    magdeck = protocol.load_module('magnetic module gen2', '10')
    magplate = magdeck.load_labware(extrPlate, 'Extraction Plate')
    sampplate = protocol.load_labware(sampPlate, '4', 'Sample Plate (Input)')
    elutionplate = protocol.load_labware(elutePlate, '1', 'Elution Plate')
    res = protocol.load_labware('nest_12_reservoir_15ml', '3')

    maghts = {
        'nest_96_wellplate_2ml_deep': 6.9,
        'alphalabs_96_wellplate_1000ul': 6.9
        }

    num_cols = math.ceil(numSamps/8)

    magsamps = magplate.rows()[0][:num_cols]
    samps = sampplate.rows()[0][:num_cols]
    elutes = elutionplate.rows()[0][:num_cols]

    lysis = [well for well in res.wells()[:3] for _ in range(4)]
    wb1 = [well for well in res.wells()[3:5] for _ in range(6)]
    wb2 = [well for well in res.wells()[5:7] for _ in range(6)]
    wb3 = [well for well in res.wells()[7:9] for _ in range(6)]
    water = res['A12']

    waste = protocol.load_labware(
        'nest_1_reservoir_195ml', '11').wells()[0].top()

    tips = [protocol.load_labware(tipType, s) for s in [7, 8, 9, 5, 6, 2]]
    parkTips = tips[0].rows()[0][:num_cols]
    all_tips = [tr['A'+str(i)] for tr in tips[1:] for i in range(1, 13)]
    tips1, tips2, tips3, tips4, tips5 = [
        all_tips[i*num_cols:(i+1)*num_cols] for i in range(5)]

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    # functions
    tipMax = int(tipType.split('_')[-1][:3]) - 10
    sides = [-1, 1]*6

    def well_mix(reps, loc, v, side):
        loc1 = loc.bottom().move(types.Point(x=side, y=0, z=3))
        loc2 = loc.bottom().move(types.Point(x=side*-1, y=0, z=0.6))
        m300.aspirate(20, loc1)
        mvol = v-20
        for _ in range(reps):
            m300.aspirate(mvol, loc1)
            m300.dispense(mvol, loc2)
        m300.dispense(20, loc2)

    def remove_supernatant(vol, src, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top())
        while vol > tipMax:
            m300.aspirate(
                tipMax, src.bottom().move(types.Point(x=side, y=0, z=0.5)))

            # wait for a moment to allow outer drips to fall above liquid
            m300.move_to(src.top(-6))
            protocol.delay(seconds=1)
            # flick to the side
            m300.move_to(src.top(-6).move(types.Point(x=2, y=0, z=0)))
            m300.move_to(src.top(-6).move(types.Point(x=0, y=0, z=0)))
            m300.dispense(tipMax+10, waste)
            m300.aspirate(10, waste)
            vol -= tipMax
        m300.aspirate(10, src.top())
        m300.aspirate(
            (vol+10),
            src.bottom().move(types.Point(x=side, y=0, z=0.5))
            )
        m300.move_to(src.top(-6))
        protocol.delay(seconds=1)
        m300.dispense((vol+20), waste)
        m300.flow_rate.aspirate = 50

    washctr = 1

    def wash(wb, tips):
        nonlocal washctr
        protocol.comment(f'Beginning wash step for Wash {washctr}...')

        for tip, pt, src, dest, s in zip(tips, parkTips, wb, magsamps, sides):
            m300.pick_up_tip(tip)
            m300.transfer(300, src, dest.top(-2), new_tip='never')
            well_mix(2, dest, 200, s)
            m300.blow_out()
            m300.drop_tip(pt)

        protocol.comment('Engaging MagDeck and incubating for 4 minutes...')
        magdeck.engage(height=maghts[extrPlate])
        protocol.delay(minutes=4)

        protocol.comment(f'Removing supernatant for Wash {washctr}...')
        for pt, src, s, tt in zip(parkTips, magsamps, sides, tips):
            m300.pick_up_tip(pt)
            remove_supernatant(300, src, s)
            m300.blow_out()
            if tipTrash:
                m300.drop_tip(tt)
            else:
                m300.drop_tip()

        magdeck.disengage()

        protocol.comment(f'Wash {washctr} complete...')
        washctr += 1

    # Transfer 460uL lysis well_mix
    protocol.comment('Adding 460uL of Lysis Mix to wells...')

    m300.pick_up_tip(all_tips[0])
    for reagent, well in zip(lysis, magsamps):
        m300.transfer(460, reagent, well, new_tip='never')
        m300.blow_out(well)
    m300.drop_tip(all_tips[0])

    # Transfer 200ul of samples
    protocol.comment('Adding 200uL of sample to wells...')

    for tip, src, dest in zip(parkTips, samps, magsamps):
        m300.pick_up_tip(tip)
        m300.transfer(200, src, dest, new_tip='never')
        m300.mix(8, 200, dest)
        m300.blow_out(dest)
        m300.drop_tip(tip)

    # Incubate for 10 minutes
    protocol.comment('Incubating for 10 minutes...')
    protocol.delay(minutes=10)

    # Engage magdeck, incubate for 5 minutes
    protocol.comment('Engaging MagDeck and incubating for 5 minutes...')
    magdeck.engage(height=maghts[extrPlate])
    protocol.delay(minutes=5)

    # transfer supernatant (660ul)
    protocol.comment('Removing 660uL of supernatant...')

    for tip, well, s in zip(parkTips, magsamps, sides):
        m300.pick_up_tip(tip)
        remove_supernatant(660, well, s)
        m300.blow_out()
        m300.drop_tip()

    magdeck.disengage()

    # wash 1
    wash(wb1, tips1)

    # wash 2
    wash(wb2, tips2)

    # wash 3
    wash(wb3, tips3)

    # Dry for 10 minutes
    protocol.comment('Drying for 10 minutes...')
    protocol.delay(minutes=10)

    # Transfer 75uL of RNAse Free Water
    protocol.comment('Adding 75uL RF Water to wells...')

    for tip, well, s in zip(tips4, magsamps, sides):
        m300.pick_up_tip(tip)
        m300.transfer(75, water, well, new_tip='never')
        well_mix(8, well, 70, s)
        m300.blow_out(well)
        m300.drop_tip(all_tips[0])

    protocol.comment('Engaging MagDeck and incubating for 4 minutes...')
    magdeck.engage(height=maghts[extrPlate])
    protocol.delay(minutes=4)

    protocol.comment('Transferring elutes...')
    m300.flow_rate.aspirate = 25
    for tip, tt, src, s, dest in zip(tips5, tips4, magsamps, sides, elutes):
        m300.pick_up_tip(tip)
        m300.aspirate(
            75, src.bottom().move(types.Point(x=s, y=0, z=0.5)))
        m300.dispense(75, dest)
        m300.blow_out(dest)
        if tipTrash:
            m300.drop_tip(tt)
        else:
            m300.drop_tip()

    protocol.comment('Protocol complete!')
