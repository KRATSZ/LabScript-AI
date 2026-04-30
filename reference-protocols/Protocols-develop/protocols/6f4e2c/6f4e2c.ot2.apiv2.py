metadata = {
    'protocolName': 'DNA Isolation from Whole Blood',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [mount, tiptype, samps, lwaste] = get_values(  # noqa: F821
        'mount', 'tiptype', 'samps', 'lwaste')

    # load labware and pipettes
    magdeck = protocol.load_module('magdeck', '1')
    magplate = magdeck.load_labware('eppendorf_96_wellplate_1000ul')
    maght = 14

    res = protocol.load_labware('nest_12_reservoir_15ml', '2')
    start_buff = res['A1']
    ly1 = res['A2']
    ly2 = res['A3']
    ebuff = res['A11']

    tempdeck = protocol.load_module('tempdeck', '4')
    tempplate = tempdeck.load_labware('eppendorf_96_wellplate_1000ul')

    pcrplate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '5')

    tips = [protocol.load_labware(
        tiptype, s) for s in ['3', '6', '9', '10', '11']]

    p300 = protocol.load_instrument('p300_multi', mount, tip_racks=tips)

    """For implementing liquid waste in a reservoir"""
    waste_res = protocol.load_labware('nest_1_reservoir_195ml', '8')
    liquid_waste = waste_res['A1'].top()
    trash = p300.trash_container.wells()[0].top()  # trash container

    magsamp = []
    tempsamp = []
    platesamp = []

    mod_samps = [magsamp, tempsamp, platesamp]
    plates = [magplate, tempplate, pcrplate]

    # protocol
    mod_num = 3 if samps == '24' else 6

    for sam, plate in zip(mod_samps, plates):
        for well in plate.columns()[:mod_num]:
            sam.append(well[0])

    # step 1
    p300.pick_up_tip()

    for col in magsamp:
        p300.transfer(130, start_buff, col.top(), new_tip='never')
        p300.blow_out(col.top())

    p300.drop_tip()

    # step 2
    for col in magsamp[:3]:
        p300.pick_up_tip()
        p300.mix(5, 200, ly1)
        p300.transfer(300, ly1, col.top(), new_tip='never')
        p300.transfer(110, ly1, col, new_tip='never')
        p300.mix(3, 200, col)
        p300.blow_out(col.top())
        p300.drop_tip()

    for col in magsamp[3:]:
        p300.pick_up_tip()
        p300.mix(5, 200, ly2)
        p300.transfer(300, ly2, col.top(), new_tip='never')
        p300.transfer(110, ly2, col, new_tip='never')
        p300.mix(3, 200, col)
        p300.blow_out(col.top())
        p300.drop_tip()

    protocol.comment('Beginning incubation... 5 minute incubation without \
    magnet; 2 minutes with magnet.')
    protocol.delay(minutes=5)
    magdeck.engage(height=maght)
    protocol.delay(minutes=2)

    # step 3
    for col in magsamp:
        p300.pick_up_tip()
        if lwaste == 'no':
            p300.transfer(640, col, trash, new_tip='never')
        else:
            p300.transfer(640, col, liquid_waste, new_tip='never')
        p300.drop_tip()

    magdeck.disengage()

    def wash(startwell):
        swell2 = startwell + 1

        for col in magsamp[:3]:
            p300.pick_up_tip()
            for _ in range(3):
                p300.transfer(
                    200, res.wells()[startwell], col.top(), new_tip='never')
            p300.mix(3, 200, col)
            p300.drop_tip()

        for col in magsamp[3:]:
            p300.pick_up_tip()
            for _ in range(3):
                p300.transfer(
                    200, res.wells()[swell2], col.top(), new_tip='never')
            p300.mix(3, 200, col)
            p300.drop_tip()

        magdeck.engage(height=maght)
        protocol.delay(minutes=3)

    def clean_up():
        dest = trash if lwaste == 'no' else liquid_waste
        for col in magsamp:
            p300.pick_up_tip()
            p300.transfer(600, col, dest, new_tip='never')
            p300.drop_tip()

    for k in range(3, 8, 2):
        wash(k)
        clean_up()
        magdeck.disengage()

    # step 7
    protocol.pause("Please move deep well plate from mag deck to temp deck. \
    When ready to continue, click RESUME.")

    tempdeck.set_temperature(60)
    protocol.comment('Incubating for 10 minutes')
    protocol.delay(minutes=10)

    # step 8
    p300.pick_up_tip()

    for col in tempsamp:
        p300.transfer(50, ebuff, col.top(), new_tip='never')
        p300.blow_out(col.top())

    p300.drop_tip()

    protocol.comment('Incubating for 10 minutes')
    protocol.delay(minutes=10)

    protocol.pause("Please move deep well palte from temp deck to mag deck. \
    When ready to continue, click RESUME.")

    magdeck.engage(height=maght)
    protocol.delay(minutes=5)

    # step 9
    for src, dest in zip(magsamp, platesamp):
        p300.pick_up_tip()
        p300.transfer(50, src, dest, new_tip='never')
        p300.blow_out(dest)
        p300.drop_tip()
