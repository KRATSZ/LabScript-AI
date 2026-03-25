metadata = {
    'protocolName': 'Sample Prep with Custom Labware',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [p50_mnt, p1k_mnt] = get_values(  # noqa: F821
        'p50_mnt', 'p1k_mnt')

    # load labware and pipettes
    t50 = protocol.load_labware('generic_96_tiprack_200ul', '1', '200ul Tips')
    t1k = protocol.load_labware(
        'opentrons_96_filtertiprack_1000ul', '2', '1000ul Filter Tips')
    p50 = protocol.load_instrument('p50_single', p50_mnt, tip_racks=[t50])
    p1k = protocol.load_instrument('p1000_single', p1k_mnt, tip_racks=[t1k])

    plate = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', '3', 'Corning Plate')
    water_rack = protocol.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '7',
        'Water Rack')
    water = water_rack['A1']

    nep_rack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '10',
        'RSE & NEP Rack')
    s1_rack = protocol.load_labware(
        'charlesriver_15_tuberack_10000ul', '8', 'Sample 1 Rack')
    hksa_rack = protocol.load_labware(
        'charlesriver_15_tuberack_10000ul', '11', 'RSE & HKSA Rack')

    def fast_mix(t, vol, loc):
        p1k.flow_rate.aspirate = 1000
        p1k.mix(t, vol, loc.bottom(3))
        p1k.flow_rate.aspirate = 500

    def water_transfer(ht, vol, loc):
        p1k.transfer(vol, water.bottom(ht), loc.bottom(10), new_tip='never')
        p1k.blow_out(loc.top())

    # Steps 1 - 6; water transfers
    p1k.pick_up_tip()

    water_transfer(60, 800, hksa_rack['A1'])
    water_transfer(60, 1920, hksa_rack['A2'])
    for w in ['A3', 'A4', 'A5', 'B1', 'B2', 'B3']:
        water_transfer(35, 1000, hksa_rack[w])
    for w in ['C1', 'C2']:
        water_transfer(35, 900, hksa_rack[w])
    water_transfer(20, 4500, s1_rack['A2'])
    for w in ['A3', 'A4']:
        water_transfer(20, 2000, s1_rack[w])

    p1k.drop_tip()

    # Steps 7 - 9; RSE mix and transfer
    p1k.pick_up_tip()
    fast_mix(5, 300, nep_rack['A1'])
    p1k.blow_out(nep_rack['A1'].bottom(3))
    p1k.transfer(
        200, nep_rack['A1'].bottom(3),
        hksa_rack['A1'].bottom(2.5), new_tip='never')
    p1k.mix(5, 800, hksa_rack['A1'].bottom(2.5))
    p1k.drop_tip()
    p50.transfer(80, hksa_rack['A1'].bottom(5), hksa_rack['A2'].bottom())

    # step 10 = 16; RSE mix and dilution
    p1k.pick_up_tip()
    fast_mix(5, 1000, hksa_rack['A2'])
    p1k.drop_tip()

    def dil_transfer(src, dest):
        p1k.pick_up_tip()
        p1k.transfer(1000, hksa_rack[src].bottom(3), hksa_rack[dest].bottom(5),
                     new_tip='never')
        p1k.mix(5, 1000, hksa_rack[dest].bottom(5))
        p1k.drop_tip()

    src_dil = ['A2', 'A3', 'A4', 'A5', 'B1', 'B2']
    dest_dil = src_dil[1:] + ['B3']

    for s, d in zip(src_dil, dest_dil):
        dil_transfer(s, d)

    # step 17 - 21; hksa mix and dilution

    def hksa_dil(src, dest, src_mix_vol):
        p1k.pick_up_tip()
        fast_mix(5, src_mix_vol, src)
        p1k.blow_out(dest)
        p1k.drop_tip()
        p50.pick_up_tip()
        p50.transfer(100, src.bottom(3), dest.bottom(5), new_tip='never')
        p50.drop_tip()

    hksa_dil(nep_rack['A2'], hksa_rack['C1'], 300)
    hksa_dil(hksa_rack['C1'], hksa_rack['C2'], 800)
    p1k.pick_up_tip()
    fast_mix(5, 800, hksa_rack['C2'])
    p1k.drop_tip()

    # step 22 - 27; sample mix and spiking

    def samp_dil(src, dest, vol):
        p1k.pick_up_tip()
        p1k.mix(5, 1000, s1_rack[src].bottom(3))
        p1k.transfer(vol, s1_rack[src].bottom(3),
                     s1_rack[dest].bottom(3), new_tip='never')
        p1k.mix(5, 1000, s1_rack[dest].bottom(3))

    samp_dil('A1', 'A2', 500)
    p1k.transfer(990, s1_rack['A2'].bottom(3), s1_rack['B1'].bottom(3),
                 new_tip='never')
    p1k.transfer(990, s1_rack['A2'].bottom(3), s1_rack['B2'].bottom(3),
                 new_tip='never')
    p1k.drop_tip()
    samp_dil('A2', 'A3', 2000)
    p1k.transfer(990, s1_rack['A3'].bottom(3), s1_rack['B3'].bottom(3),
                 new_tip='never')
    p1k.drop_tip()
    samp_dil('A3', 'A4', 2000)
    p1k.transfer(990, s1_rack['A4'].bottom(3), s1_rack['B4'].bottom(3),
                 new_tip='never')
    p1k.drop_tip()

    # step 28 - 31;
    p1k.pick_up_tip()
    fast_mix(5, 300, nep_rack['A2'])
    p1k.blow_out(nep_rack['A2'])
    p1k.drop_tip()

    p50.transfer(10, nep_rack['A2'].bottom(3), s1_rack['B1'].bottom(5))

    p1k.pick_up_tip()
    fast_mix(5, 800, nep_rack['A1'])
    p1k.drop_tip()

    for w in ['B2', 'B3', 'B4']:
        p50.transfer(10, nep_rack['A1'].bottom(5), s1_rack[w].bottom(5))

    # step 32 -
    for w in ['B1', 'B2', 'B3', 'B4']:
        p1k.pick_up_tip()
        fast_mix(5, 800, s1_rack[w])
        p1k.drop_tip()

    dtx = []
    for ltr in 'ABCDEFGH':
        dtx.append([ltr+'1', ltr+'2', ltr+'3', ltr+'4'])
    for ltr in 'ABCDEFGH':
        dtx.append([ltr+'5', ltr+'6', ltr+'7', ltr+'8'])

    src32 = []
    for w in ['B3', 'B2', 'B1', 'A5', 'A4', 'A3', 'A2']:
        src32.append(hksa_rack[w])
    for w in ['A2', 'B2', 'A3', 'B3', 'A4', 'B4']:
        src32.append(s1_rack[w])
    src32.append(hksa_rack['C2'])
    src32.append(s1_rack['A1'])

    p50.pick_up_tip()
    for well in dtx[0]:
        p50.transfer(50, water, plate[well].bottom(2.5), new_tip='never')
        p50.blow_out(plate[well].top())
    p50.drop_tip()

    for src, dwells in zip(src32, dtx[1:]):
        p1k.pick_up_tip()
        fast_mix(5, 800, src)
        p1k.drop_tip()

        p50.pick_up_tip()
        for w in dwells:
            p50.transfer(50, src.bottom(5), plate[w], new_tip='never')
            p50.blow_out(plate[w].top())
        p50.drop_tip()
