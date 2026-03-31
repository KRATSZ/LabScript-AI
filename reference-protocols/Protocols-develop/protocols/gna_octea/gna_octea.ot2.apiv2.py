from opentrons import types

metadata = {
    'protocolName': 'Automated Sample Prep for GNA Octea',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mntMulti, mntSingle, numSamps] = get_values(  # noqa: F821
     'mntMulti', 'mntSingle', 'numSamps')

    # load labware
    tips = [
        protocol.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    m300 = protocol.load_instrument(
        'p300_multi_gen2', mntMulti, tip_racks=tips)
    p300 = protocol.load_instrument(
        'p300_single_gen2', mntSingle, tip_racks=tips)

    magDeck = protocol.load_module('magnetic module gen2', '4')
    tempDeck = protocol.load_module('temperature module gen2', '6')
    magPlate = magDeck.load_labware('biorad_96_wellplate_200ul_pcr')
    tempPlate = tempDeck.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul')

    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '7')

    deepPlate = protocol.load_labware('nest_96_wellplate_2ml_deep', '8')

    octeaPlate = protocol.load_labware('octea_16_wellplate_40ul', '2')

    # Declare reagents/wells
    wb1 = rsvr['A1']
    hb1 = rsvr['A3']
    waste = rsvr['A12'].top(-2)

    sampsUTM = deepPlate.wells()[:numSamps]
    sampsHB1 = deepPlate.wells()[8:8+numSamps]
    tempSamps = tempPlate.rows()[0][:5]
    magSamps = magPlate.rows()[0][:5]
    rb1 = deepPlate['A12']
    mblyo = deepPlate['D11']
    mmlyo = deepPlate['D12']

    if numSamps != 8:
        raise Exception('Number of Samples is currently being tested and \
        should be set to 8')

    # protocol
    # set temperature module and magdeck
    tempDeck.start_set_temperature(90)
    magDeck.engage()

    # Transfer 360 HB1 to MB LYO, mix and transfer to deep plate
    p300.pick_up_tip()
    p300.transfer(360, hb1, mblyo.top(-2), new_tip='never')
    p300.mix(5, 180, mblyo)
    pip_vol = 0
    for well in sampsHB1:
        if pip_vol < 40:
            p300.dispense(pip_vol, mblyo)
            p300.aspirate(180, mblyo)
            pip_vol = 180
        p300.dispense(40, well)
        pip_vol -= 40
    p300.dispense(pip_vol, mblyo)
    p300.drop_tip()

    # Transfer HB1 with multi channel to deep plate and to samples
    m300.pick_up_tip()
    m300.transfer(360, hb1, sampsHB1[0].top(-2), new_tip='never')
    m300.mix(5, 180, sampsHB1[0])
    m300.drop_tip()

    m300.pick_up_tip()
    m300.transfer(300, hb1, sampsUTM[0].top(-2), new_tip='never')

    def deep_well_mix(reps, vol, loc):
        vol -= 20
        loc1 = loc.bottom().move(types.Point(x=1, y=0, z=1))
        loc2 = loc.bottom().move(types.Point(x=1, y=0, z=4))
        loc3 = loc.bottom().move(types.Point(x=-1, y=0, z=1))
        loc4 = loc.bottom().move(types.Point(x=-1, y=0, z=4))
        m300.aspirate(20, loc1)
        for _ in range(reps-1):
            m300.aspirate(vol, loc1)
            m300.dispense(vol, loc4)
            m300.aspirate(vol, loc3)
            m300.dispense(vol, loc2)
        m300.dispense(20, loc2)
    # m300.mix(5, 180, sampsUTM[0])
    deep_well_mix(4, 180, sampsUTM[0])

    for vol in [150, 150, 100]:
        m300.transfer(
            vol, sampsHB1[0], sampsUTM[0], new_tip='never', air_gap=20)

    # m300.mix(5, 180, sampsUTM[0])
    deep_well_mix(4, 180, sampsUTM[0])
    m300.drop_tip()

    # Transfer 800ul (160 at a time) to temperature module
    tempDeck.await_temperature(90)
    m300.pick_up_tip()
    m300.transfer(160, sampsUTM[0], tempSamps, new_tip='never', air_gap=20)

    def set_default_rate(rate=92.86):
        m300.flow_rate.aspirate = rate
        m300.flow_rate.dispense = rate
        m300.flow_rate.blow_out = rate

    def temp_well_mix(rep, vol, loc, mix_rate=300):
        m300.flow_rate.aspirate = mix_rate
        m300.flow_rate.dispense = mix_rate
        for _ in range(rep):
            m300.aspirate(vol, loc.bottom(1))
            m300.dispense(vol, loc.bottom(0.5))
        set_default_rate()

    for well in tempSamps:
        # m300.mix(5, 90, well)
        temp_well_mix(5, 90, well)
    m300.move_to(tempSamps[-1].top())

    # change temperature and incubate

    tempDeck.set_temperature(80)
    protocol.delay(minutes=2)
    tempDeck.set_temperature(56)

    for well in tempSamps:
        # m300.mix(5, 90, well)
        temp_well_mix(5, 90, well)
    m300.move_to(tempSamps[-1].top())

    protocol.delay(minutes=3)

    tempDeck.deactivate()

    # Mix and transfer samples from temperature module to magdeck
    for well in tempSamps:
        # m300.mix(5, 90, well)
        temp_well_mix(5, 90, well)

    for src, dest in zip(tempSamps, magSamps):
        m300.transfer(160, src, dest, new_tip='never', air_gap=20)

    m300.drop_tip()

    # Incubate on magdeck and transfer supernatant
    protocol.delay(minutes=3)

    m300.pick_up_tip()
    m300.flow_rate.aspirate = 20

    for src in magSamps:
        m300.transfer(160, src, waste, new_tip='never', air_gap=20)

    magDeck.disengage()

    m300.drop_tip()

    # Transfer wb1 to samples on the magdeck and re-combine
    m300.pick_up_tip()
    m300.flow_rate.aspirate = 92.86

    pip_vol = 0
    for well in magSamps:
        if pip_vol < 40:
            m300.dispense(pip_vol, wb1)
            m300.aspirate(180, wb1)
            pip_vol = 180
        m300.dispense(40, well.top(-2))
        pip_vol -= 40
    m300.dispense(pip_vol, wb1)
    magLast = magSamps[-1]

    for well in magSamps[:-1]:
        m300.transfer(
            40, well, magLast, mix_before=(5, 30), new_tip='never', air_gap=20)

    m300.mix(5, 160, magLast)
    m300.move_to(magLast.top())
    # Engage magdeck and remove supernatant
    magDeck.engage()
    protocol.delay(minutes=3)

    m300.flow_rate.aspirate = 20
    for _ in range(2):
        m300.transfer(100, magLast, waste, new_tip='never', air_gap=20)

    magDeck.disengage()
    m300.drop_tip()
    m300.flow_rate.aspirate = 92.86

    # transfer RB1 to MMLYO and distribute
    magSamps2 = magPlate.wells()[32:32+numSamps]
    p300.pick_up_tip()

    for _ in range(2):
        p300.transfer(175, rb1, mmlyo.top(-2), new_tip='never')

    p300.mix(5, 175, mmlyo)

    p300.transfer(40, mmlyo, [w.top() for w in magSamps2], new_tip='never')
    pip_vol = 0
    for well in magSamps2:
        if pip_vol < 40:
            p300.dispense(pip_vol, mmlyo)
            p300.aspirate(180, mmlyo)
            pip_vol = 180
        p300.dispense(40, well.top(-2))
        pip_vol -= 40
    p300.dispense(pip_vol, mmlyo)
    p300.drop_tip()

    m300.pick_up_tip()
    m300.mix(7, 30, magLast)
    m300.drop_tip()

    # transfer samples to octea plate

    for src, dest in zip(magSamps2, octeaPlate.rows()[0][:numSamps]):
        p300.pick_up_tip()
        p300.aspirate(40, src)
        p300.dispense(20, well.bottom().move(types.Point(x=-1, y=1, z=1)))
        p300.dispense(20, well.bottom().move(types.Point(x=1, y=-1, z=1)))
        p300.drop_tip()

    # p300.transfer(40, mmlyo, octeaPlate.wells()[numSamps:])
