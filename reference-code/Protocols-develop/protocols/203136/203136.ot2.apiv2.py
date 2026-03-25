metadata = {
    'protocolName': 'Purification of Genomic DNA',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [p300mnt, p50mnt, samp_no] = get_values(  # noqa: F821
        'p300mnt', 'p50mnt', 'samp_no')

    # load labware and pipettes
    tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', s)
            for s in ['2', '3', '5', '6', '8', '9', '10', '11']]
    p300 = protocol.load_instrument('p300_multi', p300mnt, tip_racks=tips)
    p50 = protocol.load_instrument('p50_single', p50mnt, tip_racks=tips)
    magdeck = protocol.load_module('magdeck', '4')
    magplate = magdeck.load_labware(
        'usascientific_96_wellplate_2.4ml_deep', 'Deep Well Plate')
    final_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '1',
                                        'Final Plate')
    res = protocol.load_labware('usascientific_12_reservoir_22ml', '7',
                                'Reservoir')

    # samples
    row_no = samp_no//8
    rows_samp = row_no if samp_no % 8 == 0 else row_no + 1
    b_samps = magplate.rows()[0][:rows_samp]

    # reagents
    lysis = res['A1']
    pk = res['A2']
    pbuff = res['A3']
    magbeads = res['A4']
    wash1 = res['A5']
    wash2 = res['A6']
    ebuff = res['A7']
    waste1 = res['A8']
    waste2 = res['A9']
    waste3 = res['A10']
    wwaste1 = res['A11']
    wwaste2 = res['A12']

    # Step 1 ~ Add 140ul Lysis and 30ul Proteinase K

    p300.pick_up_tip()
    for well in b_samps:
        p300.transfer(140, lysis, well.top(), new_tip='never')
    p300.drop_tip()

    for well in b_samps:
        p300.pick_up_tip()
        p300.transfer(30, pk, well, new_tip='never')
        p300.mix(5, 200, well)
        p300.blow_out(well.top())
        p300.drop_tip()

    # Step 2 ~ 20 minutes of incubation
    protocol.comment('Incubating for 20 minutes.')
    protocol.delay(minutes=20)

    # Step 3 ~ Add 50ul of purification buffer
    p300.pick_up_tip()
    for well in b_samps:
        p300.transfer(50, pbuff, well.top(), new_tip='never')
    p300.drop_tip()

    # Step 4 ~ Add 6ul of magbeads and mix
    """p300.pick_up_tip()
    p300.mix(10, 70, magbeads)
    p300.transfer(6, magbeads, b_samps[0], new_tip='never')
    p300.mix(5, 200, b_samps[0])
    p300.drop_tip()

    for well in b_samps[1:]:
        p300.pick_up_tip()
        p300.transfer(6, magbeads, well, new_tip='never')
        p300.mix(5, 200, well)
        p300.drop_tip()"""

    p50.pick_up_tip()
    p50.mix(10, 50, magbeads)

    for well in magplate.wells()[:samp_no]:
        if not p50.hw_pipette['has_tip']:
            p50.pick_up_tip()
        p50.transfer(6, magbeads, well, new_tip='never')
        p50.mix(5, 50, well)
        p50.blow_out(well.top())
        p50.drop_tip()

    # Step 5 - not needed
    # Step 6 - incubate for 5 minutes with magnet up
    magdeck.engage()
    protocol.comment('Magnetic Module engaging for 5 minutes.')
    protocol.delay(minutes=5)

    if rows_samp > 8:
        b2_samps = [b_samps[:4], b_samps[4:8], b_samps[8:]]
        first_waste = [waste1, waste2, waste3]
    elif rows_samp > 4:
        b2_samps = [b_samps[:4], b_samps[4:]]
        first_waste = [waste1, waste2]
    else:
        b2_samps = [b_samps]
        first_waste = [waste1]

    for wells, dump in zip(b2_samps, first_waste):
        for well in wells:
            p300.pick_up_tip()
            p300.transfer(190, well, dump.top(), new_tip='never')
            p300.transfer(190, well, dump.top(), new_tip='never')
            p300.transfer(46, well, dump.top(), new_tip='never')
            p300.drop_tip()

    # Step 7 ~ Wash with 100ul
    def wash_step(w, t):
        p300.pick_up_tip()

        for well in b_samps:
            p300.transfer(100, w, well.top(), air_gap=10, new_tip='never')

        protocol.comment('Letting wash sit for 1 minute.')
        protocol.delay(minutes=1)

        for well in b_samps:
            if not p300.hw_pipette['has_tip']:
                p300.pick_up_tip()
            p300.transfer(100, well.bottom(2), t, air_gap=10, new_tip='never')
            p300.drop_tip()

    wash_step(wash1, wwaste1)
    wash_step(wash2, wwaste2)

    # Step 8 ~ Incubate for 2 minutes
    protocol.comment('Letting sample dry for 2 minutes.')
    protocol.delay(minutes=2)

    # Step 9 ~ add 15ul of elution buffer and mix
    magdeck.disengage()

    for well in b_samps:
        p300.pick_up_tip()
        p300.transfer(30, ebuff, well, new_tip='never')
        p300.mix(5, 30, well)
        p300.blow_out(well.top())
        p300.drop_tip()

    protocol.comment('Incubating for 2 minutes with the magnet down.')
    protocol.delay(minutes=2)

    # Step 10 ~ Engage magdeck and incubate for 2 minutes

    protocol.comment('Incubation for 2 minutes with the magnet up.')

    magdeck.engage()

    protocol.delay(minutes=2)

    # Step 11 ~ Transfer elution buffer to final plate.
    p300.flow_rate.aspirate = 30

    for src, dest in zip(b_samps, final_plate.rows()[0][:rows_samp]):
        p300.pick_up_tip()
        p300.transfer(30, src, dest, new_tip='never')
        p300.blow_out(dest.top())
        p300.drop_tip()

    protocol.comment('Protocol complete.')
