from opentrons import types

metadata = {
    'protocolName': 'Zymo Quick-DNA/RNA Viral Kit',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.5'
}


def run(protocol):
    [num_samples, p300m, s_pip, mag_gen] = get_values(  # noqa: F821
     'num_samples', 'p300m', 's_pip', 'mag_gen')

    # load labware and pipettes
    samps = int(num_samples)  # this num represents columns and should be 1-6
    tips200 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in [
                '1', '6', '9', '7', '10'
                ]
            ]
    all_tips = [tr['A'+str(i)] for tr in tips200 for i in range(1, 13)]
    [tips1, tips2, tips3, tips4, tips5,
     tips6, tips7, tips8, tips9, tips10] = [
        all_tips[i:i+samps] for i in range(0, samps*10, samps)
        ]

    s_tips = protocol.load_labware('opentrons_96_filtertiprack_20ul', '5')
    small_pip = protocol.load_instrument(s_pip, 'right', tip_racks=[s_tips])
    p300 = protocol.load_instrument(p300m, 'left')

    magdeck = protocol.load_module(mag_gen, '4')
    magheight = 13.7 if mag_gen == 'magdeck' else 6.85
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    flatplate = protocol.load_labware(
                'nest_96_wellplate_100ul_pcr_full_skirt', '3')
    liqwaste = protocol.load_labware(
                'nest_1_reservoir_195ml', '11', 'Liquid Waste')
    waste = liqwaste['A1'].top()
    tuberack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
        '8', 'Opentrons 24 TubeRack')
    pk = tuberack['D1']
    trough = protocol.load_labware(
                    'nest_12_reservoir_15ml', '2', 'Trough with Reagents')

    buffer = [trough[x] for x in ['A1', 'A2', 'A3'] for _ in range(2)][:samps]
    wb1 = [trough[x] for x in ['A4', 'A5'] for _ in range(3)][:samps]
    wb2 = [trough[x] for x in ['A6', 'A7'] for _ in range(3)][:samps]
    ethanol1 = [trough[x] for x in ['A8', 'A9'] for _ in range(3)][:samps]
    ethanol2 = [trough[x] for x in ['A10', 'A11'] for _ in range(3)][:samps]
    water = trough['A12']

    magsamps = [magplate['A'+str(i)] for i in range(1, 12, 2)][:samps]
    magwells = [well for pl in magplate.columns()[:samps*2:2] for well in pl]
    elutes = [flatplate['A'+str(i)] for i in range(1, 7)][:samps]

    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 150
    p300.flow_rate.blow_out = 300

    def well_mix(reps, loc, vol):
        loc1 = loc.bottom().move(types.Point(x=1, y=0, z=0.6))
        loc2 = loc.bottom().move(types.Point(x=1, y=0, z=5.5))
        p300.aspirate(20, loc1)
        mvol = vol-20
        for _ in range(reps-1):
            p300.aspirate(mvol, loc1)
            p300.dispense(mvol, loc2)
        p300.dispense(20, loc2)

    def init_well_mix(reps, loc, vol):
        loc1 = loc.bottom().move(types.Point(x=1, y=0, z=0.6))
        loc2 = loc.bottom().move(types.Point(x=1, y=0, z=5.5))
        loc3 = loc.bottom().move(types.Point(x=-1, y=0, z=0.6))
        loc4 = loc.bottom().move(types.Point(x=-1, y=0, z=5.5))
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

    # Add proteinase k
    protocol.comment('Adding Proteinase K to each well:')
    for well in magwells:
        small_pip.pick_up_tip()
        small_pip.aspirate(4, pk.bottom(0.5))
        small_pip.dispense(4, well)
        small_pip.blow_out()
        small_pip.drop_tip()

    # transfer 800ul of buffer
    protocol.comment('Adding viral buffer + beads to samples:')
    for well, reagent, tip in zip(magsamps, buffer, tips1):
        p300.pick_up_tip(tip)
        for _ in range(4):
            p300.aspirate(160, reagent)
            p300.dispense(160, well.top(-5))
            p300.aspirate(10, well.top(-5))
        p300.aspirate(160, reagent)
        p300.dispense(200, well.top(-10))
        init_well_mix(2, well, 160)
        p300.blow_out()
        init_well_mix(2, well, 160)
        p300.aspirate(20, well.top(-5))
        p300.drop_tip()

    # mix magbeads for 10 minutes
    protocol.comment('Mixing samples+buffer+beads:')
    for well, tip, tret in zip(magsamps, tips2, tips1):
        p300.pick_up_tip(tip)
        init_well_mix(8, well, 130)
        init_well_mix(8, well, 130)
        p300.blow_out()
        p300.drop_tip(tret)

    magdeck.engage(height=magheight)
    protocol.comment('Incubating on magdeck for 5 minutes')
    protocol.delay(minutes=5)

    # Step 5 - Remove supernatant
    def supernatant_removal(vol, src, dest):
        p300.flow_rate.aspirate = 20
        tvol = vol
        asp_ctr = 0
        while tvol > 180:
            p300.aspirate(
                180, src.bottom().move(types.Point(x=-1, y=0, z=0.5)))
            p300.dispense(180, dest)
            p300.aspirate(10, dest)
            tvol -= 180
            asp_ctr += 1
        p300.aspirate(
            tvol, src.bottom().move(types.Point(x=-1, y=0, z=0.5)))
        dvol = 10*asp_ctr + tvol
        p300.dispense(dvol, dest)
        p300.flow_rate.aspirate = 50

    protocol.comment('Removing supernatant:')

    for well, tip in zip(magsamps, tips1):
        p300.pick_up_tip(tip)
        supernatant_removal(520, well, waste)
        p300.drop_tip()

    for well, tip in zip(magsamps, tips3):
        p300.pick_up_tip(tip)
        supernatant_removal(700, well, waste)
        p300.drop_tip()

    magdeck.disengage()
    # protocol.pause('Check the wells for volume.')
    ttips = True if samps < 3 else False

    def wash_step(src, vol, mtimes, tips, usedtips, msg, trash_tips=ttips):
        protocol.comment(f'Wash Step {msg} - Adding to samples:')
        for well, tip, tret, s in zip(magsamps, tips, usedtips, src):
            p300.pick_up_tip(tip)
            for _ in range(2):
                p300.aspirate(165, s)
                p300.dispense(165, well.top(-3))
                p300.aspirate(10, well.top(-3))
            p300.aspirate(165, s)
            p300.dispense(185, well.bottom(5))
            well_mix(mtimes, well, 180)
            p300.blow_out()
            p300.drop_tip(tret)

        magdeck.engage(height=magheight)
        protocol.comment('Incubating on MagDeck for 3 minutes.')
        protocol.delay(minutes=3)

        protocol.comment(f'Removing supernatant from Wash {msg}:')
        for well, tip in zip(magsamps, usedtips):
            p300.pick_up_tip(tip)
            supernatant_removal(520, well, waste)
            p300.aspirate(20, waste)
            if trash_tips:
                p300.drop_tip()
            else:
                p300.return_tip()
        magdeck.disengage()

    wash_step(wb1, 500, 20, tips4, tips2, '1 Wash Buffer 1')

    wash_step(wb2, 500, 10, tips5, tips3, '2 Wash Buffer 2')

    wash_step(ethanol1, 500, 10, tips6, tips4, '3 Ethanol 1')

    wash_step(ethanol2, 500, 10, tips7, tips5, '4 Ethanol 2')

    protocol.comment('Allowing beads to air dry for 2 minutes.')
    protocol.delay(minutes=2)

    p300.flow_rate.aspirate = 20
    protocol.comment('Removing any excess ethanol from wells:')
    for well, tip, tret in zip(magsamps, tips8, tips6):
        p300.pick_up_tip(tip)
        p300.transfer(
            180, well.bottom().move(types.Point(x=-0.5, y=0, z=0.4)),
            waste, new_tip='never')
        if samps < 3:
            p300.drop_tip()
        else:
            p300.drop_tip(tret)
    p300.flow_rate.aspirate = 50

    protocol.comment('Allowing beads to air dry for 10 minutes.')
    protocol.delay(minutes=10)

    magdeck.disengage()

    protocol.comment('Adding NF-Water to wells for elution:')
    for well, tip, tret in zip(magsamps, tips9, tips7):
        p300.pick_up_tip(tip)
        p300.aspirate(20, water.top())
        p300.aspirate(60, water)
        for _ in range(15):
            p300.dispense(
                50, well.bottom().move(types.Point(x=1, y=0, z=2)))
            p300.aspirate(
                50, well.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300.dispense(80, well)
        p300.blow_out()
        if samps < 3:
            p300.drop_tip()
        else:
            p300.drop_tip(tret)

    protocol.comment('Incubating at room temp for 10 minutes.')
    protocol.delay(minutes=10)

    # Step 21 - Transfer elutes to clean plate
    magdeck.engage(height=magheight)
    protocol.comment('Incubating on MagDeck for 2 minutes.')
    protocol.delay(minutes=2)

    protocol.comment('Transferring elution to final plate:')
    p300.flow_rate.aspirate = 10
    for src, dest, tip, tret in zip(magsamps, elutes, tips10, tips8):
        p300.pick_up_tip(tip)
        p300.aspirate(60, src.bottom().move(types.Point(x=-1, y=0, z=0.6)))
        p300.dispense(60, dest)
        if samps < 3:
            p300.drop_tip()
        else:
            p300.drop_tip(tret)

    magdeck.disengage()

    protocol.comment('Congratulations!')
