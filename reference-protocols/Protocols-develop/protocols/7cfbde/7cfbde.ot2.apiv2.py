from opentrons import types, protocol_api
import math

metadata = {
    'protocolName': '3D Black Bio RNA Extraction',
    'author': 'Chaz <chaz@opentrons.com>',
    'apiLevel': '2.9'
}


def run(protocol: protocol_api.ProtocolContext):
    [mnt300, num_samples] = get_values(  # noqa: F821
     'mnt300', 'num_samples')

    # load labware
    magdeck = protocol.load_module('magnetic module gen2', '7')
    magPlate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    waste1 = protocol.load_labware(
        'nest_1_reservoir_195ml', '10').wells()[0].top(-2)
    waste2 = protocol.load_labware(
        'nest_1_reservoir_195ml', '11').wells()[0].top(-2)
    res12 = protocol.load_labware('nest_12_reservoir_15ml', '5')
    res1 = protocol.load_labware('nest_1_reservoir_195ml', '2')
    alBlock = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '4')
    sampPlate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '1')

    tips200 = [
        protocol.load_labware(
            'opentrons_96_tiprack_300ul', s) for s in ['8', '9', '6', '3']
        ]
    all_tips = [tr['A'+str(i)] for tr in tips200 for i in range(1, 13)]
    park_tips = all_tips[:12]

    m300 = protocol.load_instrument(
        'p300_multi_gen2', mnt300, tip_racks=tips200[1:])

    # create reagent locations as variables
    num_cols = math.ceil(num_samples/8)
    pk = alBlock['A1']
    magBeads = [alBlock[x] for x in ['A3', 'A4'] for _ in range(6)][:num_cols]
    lysis = [well for well in res12.wells()[:6] for _ in range(2)][:num_cols]
    wash1 = [well for well in res12.wells()[6:] for _ in range(2)][:num_cols]
    wash2 = [res1['A1'] for _ in range(12)]
    eBuff = [w for w in alBlock.rows()[0][6:] for _ in range(2)][:num_cols]

    magSamps = magPlate.rows()[0][:num_cols]
    pSamps = sampPlate.rows()[0][:num_cols]

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    tip_ctr = 12

    def pick_up():
        nonlocal tip_ctr
        """Function that can be used instead of .pick_up_tip() that will pause
        robot when robot runs out of tips, prompting user to replace tips
        before resuming"""
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            m300.home()
            for _ in range(6):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=1)
            protocol.pause("\nReplace the tips in slots 9, 6, and 3. \
            Move empty rack to slot 8")
            m300.reset_tipracks()
            m300.pick_up_tip()
            tip_ctr = 0

    def tip_return():
        nonlocal tip_ctr
        m300.drop_tip(all_tips[tip_ctr])
        tip_ctr += 1

    def well_mix(reps, v, loc, side):
        loc1 = loc.bottom().move(types.Point(x=side, y=0, z=3))
        loc2 = loc.bottom().move(types.Point(x=side*-1, y=0, z=0.6))
        m300.aspirate(20, loc1)
        mvol = v-20
        for _ in range(reps):
            m300.aspirate(mvol, loc1)
            m300.dispense(mvol, loc2)
        m300.dispense(20, loc2)

    def remove_supernatant(vol, src, dest, side):
        m300.flow_rate.aspirate = 20
        m300.aspirate(10, src.top())
        while vol > 200:
            m300.aspirate(
                200, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
            m300.dispense(200, dest)
            m300.aspirate(10, dest)
            vol -= 200
        m300.aspirate(vol, src.bottom().move(types.Point(x=side, y=0, z=0.5)))
        m300.dispense(vol, dest)
        m300.dispense(10, dest)
        m300.flow_rate.aspirate = 50

    def mag_removal(vol, waste):
        magdeck.engage()
        protocol.comment('Incubating for 3 minutes')
        protocol.delay(minutes=3)

        for well, tip, s in zip(magSamps, park_tips, sides):
            m300.pick_up_tip(tip)
            remove_supernatant(vol, well, waste, side)
            m300.drop_tip(tip)

        magdeck.disengage()

    def wash_step(srcs, vol, mix, w):
        """ This is a versatile function that does a lot of the repetive tasks
            src = source wells for reagent
            vol = volume of reagent added (and supernatant removed)*
            mix = the number of times to mix
            w = waste location
            """
        for well, src, side in zip(magSamps, srcs, sides):
            pick_up()
            add_vol = vol
            e_vol = 0
            while add_vol > 200:
                m300.aspirate(200, src)
                m300.dispense(200, well.top(-3))
                m300.aspirate(10, well.top(-3))
                add_vol -= 200
                e_vol += 10
            m300.aspirate(add_vol, src)
            total_vol = add_vol + e_vol
            m300.dispense(total_vol, well)

            well_mix(mix, 200, well, side)

            m300.blow_out()

            tip_return()

        mag_removal(vol, w)

    sides = [-1, 1]*6

    # Step 1: Add 10uL Proteinase K, 804uL Lysis-Binding Mix, 200uL sample
    protocol.comment('Adding 10uL of Proteinase K')
    m300.pick_up_tip(park_tips[0])
    m300.aspirate(12*num_cols, pk)
    for well in magSamps:
        m300.dispense(10, well)
    m300.dispense(2*num_cols, pk)
    m300.blow_out()

    protocol.comment('\nAdding 804uL of Lysis-Binding Mix + 200uL of Sample')
    for well, l, samp, t, s in zip(magSamps, lysis, pSamps, park_tips, sides):
        if not m300.has_tip:
            m300.pick_up_tip(t)
        for _ in range(4):
            m300.transfer(201, l, well.top(-2), new_tip='never')
        m300.blow_out(well.top(-3))
        m300.transfer(200, samp, well, new_tip='never')
        well_mix(20, 200, well, s)
        m300.blow_out()
        m300.drop_tip()

    # Step 2: Add 20uL of Magnetic Beads
    for well, mb, tr, side in zip(magSamps, magBeads, park_tips, sides):
        pick_up()
        m300.transfer(20, mb, well, new_tip='never')
        well_mix(15, 200, well, side)
        m300.blow_out()
        m300.drop_tip(tr)

    mag_removal(1050, waste1)

    # Step 4: Wash 1, 750uL
    protocol.comment('\nPerforming Wash 1...')
    wash_step(wash1, 750, 15, waste1)

    # Step 5: Wash 2-1, 800uL
    protocol.comment('\nPerforming Wash 2-1...')
    wash_step(wash2, 800, 15, waste2)

    # Step 6: Wash 2-2, 800uL
    protocol.comment('\nPerforming Wash 2-2...')
    wash_step(wash2, 800, 15, waste2)

    protocol.comment('\nRemoving any excess ethanol...')
    m300.flow_rate.aspirate = 25
    for well, tip in zip(magSamps, park_tips):
        m300.pick_up_tip(tip)
        m300.aspirate(60, well)
        m300.dispense(60, waste2)
        m300.aspirate(10, waste2)
        m300.drop_tip(tip)

    m300.flow_rate.aspirate = 50
    magdeck.disengage()
    protocol.comment('\nLetting air dry for 10 minutes...')
    protocol.comment('Please replace 96-Well Plate containing Samples \
    with clean plate for elutions')
    protocol.delay(minutes=10)

    protocol.comment('\nAdding 60uL of elution buffer to samples...')
    for well, buffer, side in zip(magSamps, eBuff, sides):
        loc1 = well.bottom().move(types.Point(x=side, y=0, z=2))
        loc2 = well.bottom().move(types.Point(x=side*-1, y=0, z=0.6))
        pick_up()
        m300.aspirate(60, buffer)
        m300.dispense(60, loc2)
        for _ in range(10):
            m300.aspirate(50, loc1)
            m300.dispense(50, loc2)
        m300.blow_out()
        tip_return()

    protocol.comment('\nIncubating at room temp for 10 minutes.')
    protocol.delay(minutes=10)

    magdeck.engage()
    protocol.comment('Incubating on MagDeck for 2 minutes.')
    protocol.delay(minutes=2)

    protocol.comment('\nTransferring elution to final plate...')
    m300.flow_rate.aspirate = 20
    for src, dest, s in zip(magSamps, pSamps, sides):
        pick_up()
        m300.aspirate(60, src.bottom().move(types.Point(x=s, y=0, z=0.6)))
        m300.dispense(60, dest)
        tip_return()

    magdeck.disengage()
    protocol.comment('\nCongratulations! The protocol is complete!')
