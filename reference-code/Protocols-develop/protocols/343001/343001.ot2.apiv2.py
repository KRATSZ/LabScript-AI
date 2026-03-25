metadata = {
    'protocolName': 'Zymo Extraction Protocol',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


def run(protocol):
    [samp_num, p50mnt, p1kmnt, mag_time, water_vol] = get_values(  # noqa: F821
        'samp_num', 'p50mnt', 'p1kmnt', 'mag_time', 'water_vol')

    # load labware and pipettes
    tips1k = [protocol.load_labware(
                'opentrons_96_tiprack_1000ul', str(s)) for s in range(5, 9)]

    tips1kw = [well.wells() for well in tips1k]
    tips1kwells = [well for plate in tips1kw for well in plate]

    tips50 = [protocol.load_labware(
                'opentrons_96_tiprack_300ul', str(s)) for s in range(9, 11)]
    tips50kw = [well.wells() for well in tips50]
    tips50wells = [well for plate in tips50kw for well in plate]

    magdeck = protocol.load_module('magdeck', '4')
    magplate = magdeck.load_labware('zymo_96_wellblock')
    magheight = 13.5
    magsamps = magplate.wells()[:samp_num]

    elution_plate = protocol.load_labware('zymo_elution_plate', '1')
    elutes = elution_plate.wells()
    """elution_plate2 = protocol.load_labware('zymo_elution_plate', '2')
    elutes2 = elution_plate2.wells()[:samp_num]"""

    waste_res = protocol.load_labware('nest_1_reservoir_195ml', '11')
    liq_waste = waste_res['A1'].top()

    tuberack2ml = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '2')
    pk = tuberack2ml['A1']
    magbeads = tuberack2ml['A2']
    water1 = tuberack2ml['B1']
    water2 = tuberack2ml['B2']

    tuberack50ml = protocol.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '3')
    pathbuff = [tuberack50ml['A1'], 75]
    wb1 = [tuberack50ml['A2'], 75]
    wb2 = [tuberack50ml['B2'], 75]
    etoh1 = [tuberack50ml['A3'], 75]
    etoh2 = [tuberack50ml['B3'], 75]

    p50 = protocol.load_instrument('p50_single', p50mnt, tip_racks=tips50)
    p1k = protocol.load_instrument('p1000_single', p1kmnt, tip_racks=tips1k)

    p50.pick_up_tip(tips50wells[0])
    p50tipvol = 0

    # distribute 2ul of pk to each well at the top of the plate
    for well in magsamps:
        if p50tipvol == 0:
            p50.aspirate(16, pk.bottom(4))
            p50tipvol = 16
        p50.dispense(2, well.top())
        p50tipvol -= 2

    if p50tipvol > 0:
        p50.dispense(p50tipvol, pk.top())

    p50.drop_tip()

    def height_adj(vol, ht):
        delta_ht = 1.1*((13.905**2*3.14)/vol)
        ht -= delta_ht
        if ht < 4:
            ht == 0

    # distribute 400ul of PathBuff to each well AND replace tips for mixing
    for idx, well in enumerate(magsamps):
        p1k.pick_up_tip(tips1kwells[idx])
        p1k.transfer(
            400, pathbuff[0].bottom(pathbuff[1]),
            well.top(-10), new_tip='never')
        height_adj(400, pathbuff[1])
        p1k.blow_out(well.top())
        p1k.return_tip()

    # distribute magbeads after mixing
    p50.pick_up_tip(tips50wells[1])
    p50.aspirate(50, magbeads)
    p50.dispense(49, magbeads)
    for _ in range(8):
        p50.aspirate(49, magbeads)
        p50.dispense(49, magbeads)
    p50.dispense(1, magbeads.top())
    p50.blow_out(magbeads.top())

    for well in magsamps:
        p50.transfer(20, magbeads, well.top(-10), new_tip='never')
        p50.blow_out(well.top())

    p50.drop_tip()

    # mix using recycled tip
    for idx, well in enumerate(magsamps):
        p1k.pick_up_tip(tips1kwells[idx])
        p1k.aspirate(300, well.bottom(20))
        p1k.aspirate(320, well)
        p1k.dispense(300, well)
        p1k.dispense(300, well.bottom(20))
        for _ in range(14):
            p1k.aspirate(300, well.bottom(20))
            p1k.aspirate(300, well)
            p1k.dispense(300, well)
            p1k.dispense(300, well.bottom(20))
        p1k.dispense(20, well.top(-5))
        p1k.blow_out(well.top())
        p1k.drop_tip()

    magdeck.engage(height=magheight)
    protocol.delay(minutes=mag_time)
    protocol.comment('Incubating on MagDeck for '+str(mag_time)+' minutes.')

    # remove supernatant
    tip1kcount = samp_num

    for well in magsamps:
        p1k.pick_up_tip(tips1kwells[tip1kcount])
        tip1kcount += 1
        p1k.transfer(622, well, liq_waste, new_tip='never')
        p1k.drop_tip()

    magdeck.disengage()

    def wash_step(src):
        nonlocal tip1kcount
        washcount = tip1kcount

        # add wash
        for well in magsamps:
            p1k.pick_up_tip(tips1kwells[washcount])
            washcount += 1
            p1k.transfer(500, src[0], well, new_tip='never')
            height_adj(500, src[1])
            p1k.aspirate(490, well)
            for _ in range(5):
                p1k.dispense(480, well)
                p1k.aspirate(480, well)
            p1k.dispense(10, well)
            p1k.return_tip()

        # engage magdeck
        magdeck.engage(height=magheight)
        protocol.delay(minutes=mag_time)
        protocol.comment('Incubating on MagDeck for '+str(mag_time)+' mins')

        # discard supernatant with previous tips
        for well in magsamps:
            p1k.pick_up_tip(tips1kwells[tip1kcount])
            tip1kcount += 1
            p1k.transfer(500, well, liq_waste, new_tip='never')
            p1k.drop_tip()

        magdeck.disengage()

    # wash with WB1
    wash_step(wb1)

    wash_step(wb2)

    wash_step(etoh1)

    wash_step(etoh2)

    protocol.comment('Drying beads for 10mins at room temp.')
    protocol.delay(minutes=10)

    tip50count = 2

    tipc = tip50count

    ms1 = magsamps[:24]
    ms2 = magsamps[24:]

    for src, dest in zip([water1, water2], [ms1, ms2]):
        for well in dest:
            p50.pick_up_tip(tips50wells[tipc])
            tipc += 1
            p50.transfer(water_vol, src, well, new_tip='never')
            p50.aspirate(30, well)
            for _ in range(8):
                p50.dispense(25, well)
                p50.aspirate(25, well)
            p50.dispense(5, well)
            p50.blow_out(well.top())
            p50.return_tip()

    protocol.comment('Incubating for 2 mins at room temp.')
    magdeck.engage(height=magheight)
    protocol.delay(minutes=mag_time)
    protocol.comment('Incubating on MagDeck for '+str(mag_time)+' mins')

    trans_vol = water_vol/2.0

    """for s, d1, d2 in zip(magsamps, elutes, elutes2):
        p50.pick_up_tip(tips50wells[tip50count])
        tip50count += 1
        p50.aspirate(water_vol, s)
        p50.dispense(trans_vol, d1)
        p50.dispense(trans_vol, d2)
        p50.drop_tip()"""

    for idx, well in enumerate(magsamps[:48]):
        p50.pick_up_tip(tips50wells[tip50count])
        tip50count += 1
        p50.aspirate(water_vol, well)
        p50.dispense(trans_vol, elutes[idx])
        p50.dispense(trans_vol, elutes[idx+48])
        p50.drop_tip()

    if samp_num > 48:
        protocol.pause('Please remove elution plate and replace.')
        for i, well in zip(range(48, 96), magsamps[48:]):
            p50.pick_up_tip(tips50wells[tip50count])
            p50.aspirate(water_vol, well)
            p50.dispense(trans_vol, elutes[i])
            p50.dispense(trans_vol, elutes[i+48])
            p50.drop_tip()

    magdeck.disengage()
    protocol.comment('Congratulations - the protocol is now complete.')
