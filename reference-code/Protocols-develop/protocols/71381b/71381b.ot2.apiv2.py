from opentrons.types import Point

metadata = {
    'protocolName': 'Zymo Quick DNA HMW + Labelling',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt20, mnt300, label, purify] = get_values(  # noqa: F821
     'mnt20', 'mnt300', 'label', 'purify')

    # load labware and pipette
    m20 = protocol.load_instrument('p20_multi_gen2', mnt20)
    tempdeck = protocol.load_module('temperature module gen2', '1')
    tempplate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul')
    samps = tempplate.rows()[0][:4]

    res = protocol.load_labware('nest_12_reservoir_15ml', '5')

    t20 = {}
    t20['tr2'] = protocol.load_labware('opentrons_96_tiprack_20ul', '6')

    if label:
        t20['tr1'] = protocol.load_labware('opentrons_96_tiprack_20ul', '3')
        lplate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '2')

    if purify:
        t300 = [
            protocol.load_labware(
                'opentrons_96_tiprack_300ul', s) for s in ['7', '8', '10']]
        m300 = protocol.load_instrument(
            'p300_multi_gen2', mnt300, tip_racks=t300)
        t20['tr3'] = protocol.load_labware('opentrons_96_tiprack_20ul', '11')
        magdeck = protocol.load_module('magnetic module gen2', '4')
        magplate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr')

    switch = True

    def _drop(pip):
        nonlocal switch
        side = 30 if switch else -18
        drop_loc = protocol.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch

    """ LABELLING """
    if label:
        mQ = res['A1']
        csb = lplate['A3']
        mTaql = lplate['A5']
        mtc22 = lplate['A1']
        pk = lplate['A7']

        stpctr = 1

        def ltransfer(
                lbl, src, vol1, loc1, tips,
                vol2=0, loc2=1, mix=0, rtips=[0]*4):
            nonlocal stpctr
            protocol.comment(f'\nStep {stpctr}: Adding {vol1+vol2}uL {lbl}...')
            for samp, tip, rt in zip(samps, tips, rtips):
                m20.pick_up_tip(tip)
                m20.aspirate(vol1, src)
                m20.dispense(vol1, samp.bottom(loc1))
                if vol2:
                    m20.aspirate(vol2, src)
                    m20.dispense(vol2, samp.bottom(loc2))
                if mix:
                    m20.mix(mix, 20, samp)
                m20.blow_out()
                if rtips:
                    m20.drop_tip(rt)
                else:
                    _drop(m20)
            stpctr += 1

        # Step 1
        ltransfer('mQ', mQ, 10, 10, t20['tr1'].rows()[0][:4], 13, 1)

        # Step 2
        ltransfer('CSB', csb, 4, 1, t20['tr1'].rows()[0][4:8])

        # Step 3
        ltransfer('M.Taql', mTaql, 2, 1, t20['tr1'].rows()[0][8:])

        # Step 4
        ltransfer(
            'MTC22', mtc22, 1, 1, t20['tr2'].rows()[0][:4],
            mix=10, rtips=t20['tr1'].rows()[0][:4]
            )

        # Step 5
        protocol.comment('\nStep 5: Setting temperature to 65C and incubating \
        for 60 minutes...')
        tempdeck.set_temperature(65)
        protocol.delay(minutes=60)
        tempdeck.deactivate()
        stpctr = 6

        # Step 6
        ltransfer(
            'Proteinase K', pk, 2, 1, t20['tr2'].rows()[0][4:8],
            mix=10, rtips=t20['tr1'].rows()[0][4:8]
            )

        # Step 7
        protocol.comment('\nStep 7: Setting temperature to 50C and incubating \
        for 60 minutes...')
        tempdeck.set_temperature(50)
        protocol.delay(minutes=60)

        protocol.comment('Labelling complete!')

    """ PURIFICATION """
    if purify:
        magbeads = res['A2']
        magbuff = res['A3']
        wb1 = res['A4']
        wb2 = res['A5']
        ebuff = res['A6']
        msamps1 = magplate.rows()[0][:4]
        msamps2 = magplate.rows()[0][4:8]
        msamps3 = magplate.rows()[0][8:]
        tsamps2 = tempplate.rows()[0][4:8]
        tsamps3 = tempplate.rows()[0][8:]
        waste1 = res['A7'].top(-2)

        # Step 1
        protocol.comment('\nStep 1: Resuspend Magbeads and add 10uL...')
        for samp, tip in zip(samps, t20['tr2'].rows()[0][8:]):
            m20.pick_up_tip(tip)
            m20.mix(25, 20, magbeads)
            m20.aspirate(10, magbeads)
            m20.dispense(10, samp)
            m20.blow_out()
            _drop(m20)

        def pTransRemoval(
                src, vol, dest, waste,
                rtips=[0]*4, dest2=[0]*4, rvol=0, tvol=75, remove=True):
            for d, rt, d2 in zip(dest, rtips, dest2):
                m300.pick_up_tip()
                m300.aspirate(vol, src)
                m300.dispense(vol, d)
                m300.mix(25, vol, d)
                if d2:
                    for _ in range(2):
                        m300.transfer(tvol, d, d2, new_tip='never')
                protocol.delay(seconds=10)
                m300.blow_out()
                if remove:
                    magdeck.engage()
                    protocol.delay(minutes=1)
                    rvol = vol + 20 if rvol == 0 else rvol
                    if d2:
                        m300.transfer(rvol, d2, waste, new_tip='never')
                    else:
                        m300.transfer(rvol, d, waste, new_tip='never')
                if rtips:
                    m300.drop_tip(rt)
                else:
                    _drop(m300)
                magdeck.disengage()

        def extraRemoval(vol, srcs, waste, tips, rtips=[0]*4):
            magdeck.engage()
            for src, tip, rt in zip(srcs, tips, rtips):
                m20.pick_up_tip(tip)
                m20.aspirate(vol, src)
                m20.dispense(vol, waste)
                if label:
                    m20.drop_tip(rt)
                else:
                    _drop(m20)
            magdeck.disengage()

        # Step 2
        protocol.comment('\nStep 2: Adding 50uL MagBinding Buffer, \
        Transferring to MagDeck, & Removing Supernatant...')
        pTransRemoval(magbuff, 50, samps, waste1, dest2=msamps1, rvol=120)

        # Step 3
        protocol.comment('\nStep 3: Adding 50uL MagBinding Buffer \
        & Removing Supernatant...')
        pTransRemoval(magbuff, 50, msamps1, waste1, rvol=75)

        # Step 4
        protocol.comment('\nStep 4: Removing leftover buffer...')
        extraRemoval(
            5, msamps1, waste1, t20['tr3'].rows()[0][:4],
            t20['tr2'].rows()[0][:4])

        # Step 5
        protocol.comment('\nStep 5: Adding 100uL Wash Buffer 1 \
        & Removing Supernatant...')
        pTransRemoval(wb1, 100, msamps1, waste1)

        # Step 6
        protocol.comment('\nStep 6: Removing leftover buffer...')
        extraRemoval(
            5, msamps1, waste1, t20['tr3'].rows()[0][4:8],
            t20['tr2'].rows()[0][4:8])

        # Step 7
        protocol.comment('\nStep 7: Adding 100uL Wash Buffer 2 \
        & Removing Supernatant...')
        pTransRemoval(wb2, 100, msamps1, waste1, rtips=t300[0].rows()[0][:4])

        # Step 8
        protocol.comment('\nStep 8: Adding 100uL Wash Buffer 2 \
        & Removing Supernatant...')
        pTransRemoval(wb2, 100, msamps1, waste1, rtips=t300[0].rows()[0][4:8])

        # Step 9
        protocol.comment('\nStep 9: Adding 100uL Wash Buffer 2, \
        Transferring Samples, & Removing Supernatant...')
        pTransRemoval(
            wb2, 100, msamps1, waste1, dest2=msamps2,
            rtips=t300[0].rows()[0][8:])

        # Step 10
        protocol.comment('\nStep 10: Removing leftover buffer...')
        extraRemoval(
            5, msamps2, waste1, t20['tr3'].rows()[0][8:],
            t20['tr2'].rows()[0][8:])
        magdeck.engage()

        # Step 11
        protocol.comment('\nStep 11: Drying Magbeads for 30 minutes...')
        tempdeck.set_temperature(65)
        protocol.delay(minutes=25)  # assuming tempdeck takes 5 minutes...

        # Step 12
        protocol.comment('\nStep 12: Adding 50uL Elution Buffer, \
        Transferring Samples, & Removing Supernatant...')
        pTransRemoval(
            ebuff, 50, msamps2, waste1, dest2=tsamps2,
            rtips=t300[1].rows()[0][:4], tvol=30, remove=False)

        # Step 13
        protocol.comment('\nStep 13: Waiting 5 minutes...')
        protocol.delay(minutes=5)

        # Step 14
        protocol.comment('\nStep 14: Mixing samples...')
        utips = t300[2].rows()[0][4:8]
        for samp, tip in zip(tsamps2, utips):
            m300.pick_up_tip()
            m300.mix(25, 50, samp)
            m300.move_to(samp.bottom(4))
            protocol.delay(seconds=10)
            m300.blow_out()
            m300.drop_tip(tip)

        # Step 15
        protocol.comment('\nStep 15: Waiting 5 minutes...')
        protocol.delay(minutes=5)

        # Step 16
        protocol.comment('\nStep 16: Mixing samples & transferring...')
        wtips = t300[1].rows()[0][4:8]
        for s, s2, t, t2 in zip(tsamps2, msamps3, utips, wtips):
            m300.pick_up_tip(t)
            m300.mix(25, 50, s)
            for _ in range(2):
                m300.transfer(30, s, s2, new_tip='never')
            m300.move_to(s2.bottom(4))
            protocol.delay(seconds=10)
            m300.blow_out()
            m300.drop_tip(t2)

        # Step 17
        protocol.comment('\nStep 17: Setting Temperature Module to 22C \
        and waiting 1 minute...')
        tempdeck.set_temperature(22)

        # Step 18
        protocol.comment('\nStep 18: Transfer solution to Temperature Module')
        xtips = t300[2].rows()[0][8:]
        ytips = t300[1].rows()[0][8:]
        magdeck.engage()
        for s, s2, t, t2 in zip(msamps3, tsamps3, xtips, ytips):
            m300.pick_up_tip(t)
            m300.transfer(50, s, s2, new_tip='never')
            m300.drop_tip(t2)

        protocol.comment('\nPurification complete!')
