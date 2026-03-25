metadata = {
    'protocolName': 'Visby Test with Pooling p1000',
    'author': 'Dipro <dipro@basisdx.org>, Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(protocol):
    [mnt1000, poolVol, numVisbys, numPools] = get_values(  # noqa: F821
     'mnt1000', 'poolVol', 'numVisbys', 'numPools')

    # load labware
    tips1000 = protocol.load_labware('opentrons_96_filtertiprack_1000ul', '1')
    p1000 = protocol.load_instrument(
        'p1000_single_gen2', mnt1000, tip_racks=[tips1000])
    p1000.flow_rate.aspirate = 300
    p1000.flow_rate.dispense = 300

    visbys = [
        protocol.load_labware(
            'visby', s) for s in [10, 11, 7, 8, 9, 4][:numVisbys]]

    poolRack = protocol.load_labware('basisdx_15_tuberack_12000ul', '5')

    # create variables
    pvol = poolVol/numPools
    pooledSamps = [
        poolRack[w] for w in ['A1', 'A3', 'A5', 'C1', 'C3', 'C5'][:numVisbys]]
    iSamps = protocol.load_labware('basisdx_15_tuberack_12000ul', '2').rows()
    if numVisbys > 3:
        iSamps += protocol.load_labware(
            'basisdx_15_tuberack_12000ul', '3').rows()
    gap = 50

    protocol.comment(f'\nPooling Samples: {pvol}uL-->{poolVol}uL\n')
    for samps, pool in zip(iSamps, pooledSamps):
        for samp in samps[:numPools]:
            p1000.pick_up_tip()
            p1000.aspirate(100, samp.top())
            p1000.aspirate(pvol, samp.bottom(10))
            protocol.delay(seconds=1)
            p1000.move_to(samp.top())
            p1000.air_gap(gap)
            p1000.dispense(100+pvol+gap, pool.top(-30))
            p1000.drop_tip(home_after=False)

    for idx, (visby, pool) in enumerate(zip(visbys, pooledSamps)):
        protocol.comment(f'\nTransferring {poolVol}uL to Visby {idx+1}\n')
        p1000.pick_up_tip()
        p1000.mix(1, poolVol*.9, pool.bottom(38))

        p1000.aspirate(poolVol, pool.bottom(38))
        protocol.delay(seconds=1)
        p1000.move_to(pool.top())
        p1000.air_gap(gap)
        p1000.dispense(poolVol+gap+20, visby['A1'].bottom(10))
        protocol.delay(seconds=1)
        p1000.drop_tip(home_after=False)

    protocol.comment('\nProtocol complete!')
