from opentrons import types

metadata = {
    'protocolName': 'Automated Sample Prep for GNA Octea [v2]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mntMulti, mntSingle, tempBlock, rsAdd] = get_values(  # noqa: F821
     'mntMulti', 'mntSingle', 'tempBlock', 'rsAdd')

    # load labware
    tips = [
        protocol.load_labware('opentrons_96_filtertiprack_200ul', '3')]
    m300 = protocol.load_instrument(
        'p300_multi_gen2', mntMulti, tip_racks=tips)
    p300 = protocol.load_instrument(
        'p300_single_gen2', mntSingle, tip_racks=tips)

    magDeck = protocol.load_module('magnetic module gen2', '7')
    tempDeck = protocol.load_module('temperature module gen2', '4')
    magPlate = magDeck.load_labware('nest_96_wellplate_2ml_deep')
    tempPlate = tempDeck.load_labware(tempBlock)

    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '10')
    tubeRack = protocol.load_labware(
        'opentrons_24_tuberack_nest_1.5ml_snapcap', '6')

    octeaPlate = protocol.load_labware('octea_16_wellplate_40ul', '1')

    # Declare reagents/wells
    rs1 = tubeRack['A6']
    magBeads = tubeRack['A1']
    pca = tubeRack['D6']

    hb1 = rsvr['A12']
    wb1 = rsvr['A10']
    waste = rsvr['A1'].top(-1)

    sampsTemp = tempPlate.wells()[:8]
    magSingle = magPlate.wells()[:8]
    magMulti = magPlate['A1']

    # create function to adjust aspiration/dispense/blowout rates
    custom_rates = {
        'reset': [92.86, 92.86, 92.86],
        'mix': [150, 150, 150]
        }

    def flow_rate(k, pip):
        pip.flow_rate.aspirate = custom_rates[k][0]
        pip.flow_rate.dispense = custom_rates[k][1]
        pip.flow_rate.blow_out = custom_rates[k][2]

    # protocol
    # Reconstitue magbeads and transfer to samples
    protocol.comment('\nTransferring 10ul MagBeads to samples...')

    p300.pick_up_tip()

    if rsAdd:
        p300.transfer(90, rs1, magBeads, new_tip='never')

    p300.mix(8, 80, magBeads)

    for well in sampsTemp:
        if p300.current_volume < 10:
            p300.mix(3, 20, magBeads)
            p300.aspirate(20, magBeads)
        p300.dispense(10, well.top(-2))

    p300.drop_tip()

    # Transfer 680ul hb1 to samples
    protocol.comment('\nTransferring 680uL HB1 to samples...')

    for well in sampsTemp:
        p300.pick_up_tip()
        for _ in range(4):
            p300.aspirate(30, hb1.top())
            p300.aspirate(170, hb1)
            p300.dispense(200, well.top(-2))
        flow_rate('mix', p300)
        p300.mix(10, 180, well)
        flow_rate('reset', p300)
        protocol.delay(seconds=1)
        p300.touch_tip(v_offset=-3, radius=0.8)
        p300.aspirate(20, well.top())
        p300.drop_tip()

    # Incubate @80C for 3 minutes
    protocol.comment('\nSetting Temp Deck to 80 and incubating for 3 minutes')
    tempDeck.set_temperature(80)
    protocol.delay(minutes=3)

    # Incubate @56C for 3 minutes; Mix while tempDeck cools
    protocol.comment('\nSetting Temp Deck to 56 and incubating for 3 minutes \
    - The pipette will mix samples while temperature is reached.')
    tempDeck.start_set_temperature(56)
    num_of_mixes = 0

    def mix_while_cooling(v):
        flow_rate('mix', p300)
        if v > 0:
            p300.starting_tip = tips[0]['A1']
        for idx, well in enumerate(sampsTemp):
            if v > 0:
                p300.pick_up_tip(tips[0].wells()[idx])
            else:
                p300.pick_up_tip()
            p300.mix(5, 180, well)
            protocol.delay(seconds=1)
            p300.drop_tip(tips[0].wells()[idx])
        flow_rate('reset', p300)

    while tempDeck.temperature < 60 and num_of_mixes < 6:
        mix_while_cooling(num_of_mixes)
        num_of_mixes += 1
    if tempDeck.temperature < 58:
        tempDeck.await_temperature(56)
    protocol.delay(minutes=3)

    # Transfer sample+hb1+magbeads to magplate
    protocol.comment('\nTransferring samples to Mag Deck')

    for idx, (src, dest) in enumerate(zip(sampsTemp, magSingle)):
        p300.pick_up_tip(tips[0].wells()[idx])
        p300.mix(3, 180, src)
        for _ in range(4):
            p300.transfer(200, src, dest, new_tip='never')
        p300.drop_tip()

    # Incubate on MagDeck and transfer supernatant
    protocol.comment('\nIncubating on Mag Deck \
    & transferring supernatant to waste')
    magDeck.engage()
    protocol.delay(minutes=2)

    m300.pick_up_tip()
    m300.aspirate(10, magMulti.top())
    m300.flow_rate.aspirate = 30
    for _ in range(5):
        m300.aspirate(160, magMulti.bottom().move(types.Point(x=-1, y=0, z=1)))
        m300.dispense(170, waste)
        m300.aspirate(10, waste)
    m300.drop_tip()
    flow_rate('reset', m300)

    # Transfer 200uL of WB1 and mix well
    protocol.comment('\nAdding 200uL of WB1 to samples')
    magDeck.disengage()

    m300.pick_up_tip()
    m300.aspirate(200, wb1)
    flow_rate('mix', m300)
    m300.dispense(200, magMulti)
    for _ in range(12):
        m300.aspirate(150, magMulti.bottom(2))
        m300.dispense(150, magMulti)
    protocol.delay(seconds=2)
    m300.drop_tip()

    # Incbuate on MagDeck and transfer supernatant; reconstitute pca
    protocol.comment('\nIncubating on Mag Deck \
    & transferring supernatant to waste')
    magDeck.engage()
    protocol.delay(minutes=2)

    m300.pick_up_tip()
    m300.flow_rate.aspirate = 30
    m300.aspirate(200, magMulti.bottom().move(types.Point(x=-1, y=0, z=1)))
    m300.dispense(200, waste)
    m300.aspirate(10, waste)
    m300.drop_tip()

    # Transfer PCA; reconstitute if needed
    protocol.comment('\nTransferring 40ul of PCA to samples... \
    Reconstituting PCA first, if needed')

    magDeck.disengage()
    p300.pick_up_tip()
    if rsAdd:
        for _ in range(2):
            p300.transfer(175, rs1, pca, new_tip='never')

    p300.mix(6, 180, pca)

    for well in magSingle:
        p300.aspirate(20, pca.top())
        p300.aspirate(40, pca)
        p300.dispense(60, well.top(-2))

    p300.drop_tip()

    # Mixing samples and transferring to Octea chip
    protocol.comment('\nMixing samples and transferring to Octea chip')
    for src, dest in zip(magSingle, octeaPlate.rows()[0]):
        p300.pick_up_tip()
        for _ in range(6):
            p300.aspirate(30, src.bottom().move(types.Point(x=1, y=0, z=1)))
            p300.dispense(30, src.bottom().move(types.Point(x=2, y=0, z=2)))
        protocol.delay(seconds=1)
        p300.aspirate(40, src)
        p300.dispense(20, dest.bottom().move(types.Point(x=-1, y=1, z=1)))
        p300.dispense(20, dest.bottom().move(types.Point(x=1, y=-1, z=1)))
        p300.drop_tip()
