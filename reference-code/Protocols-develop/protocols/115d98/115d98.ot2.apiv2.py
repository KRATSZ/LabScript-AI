metadata = {
    'protocolName': 'Visby Test without Pooling p1000',
    'author': 'Dipro <dipro@basisdx.org>, Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(protocol):
    [mnt1000, sampVol, numSamps] = get_values(  # noqa: F821
     'mnt1000', 'sampVol', 'numSamps')

    # load labware
    tips1000 = protocol.load_labware('opentrons_96_filtertiprack_1000ul', '1')
    p1000 = protocol.load_instrument(
        'p1000_single_gen2', mnt1000, tip_racks=[tips1000])
    p1000.flow_rate.aspirate = 300
    p1000.flow_rate.dispense = 300

    visbys = [
        protocol.load_labware(
            'visby', s) for s in [10, 11, 7, 8, 9][:numSamps]]

    poolRack = protocol.load_labware('basisdx_15_tuberack_12000ul', '5')
    sampRack = protocol.load_labware('basisdx_15_tuberack_12000ul', '2')

    # create variables
    pooledSamps = [
        poolRack[w] for w in ['A1', 'A3', 'A5', 'C1', 'C3'][:numSamps]]
    samps = sampRack.rows()[0][:numSamps]
    gap = 50

    protocol.comment(f'\nTransferring {sampVol}uL to dilution buffer\n')
    for samp, dest in zip(samps, pooledSamps):
        p1000.pick_up_tip()
        p1000.aspirate(100, samp.top())
        p1000.aspirate(sampVol, samp.bottom(10))
        protocol.delay(seconds=1)
        p1000.move_to(samp.top())
        p1000.air_gap(gap)
        p1000.dispense(100+sampVol+gap, dest.top(-30))
        p1000.drop_tip(home_after=False)

    for idx, (visby, pool) in enumerate(zip(visbys, pooledSamps)):
        protocol.comment(f'\nTransferring {sampVol}uL to Visby {idx+1}\n')
        p1000.pick_up_tip()
        p1000.mix(1, sampVol*.9, pool.bottom(38))

        p1000.aspirate(sampVol, pool.bottom(38))
        protocol.delay(seconds=1)
        p1000.move_to(pool.top())
        p1000.air_gap(gap)
        p1000.dispense(sampVol+gap+20, visby['A1'].bottom(10))
        protocol.delay(seconds=1)
        p1000.drop_tip(home_after=False)

    protocol.comment('\nProtocol complete!')
