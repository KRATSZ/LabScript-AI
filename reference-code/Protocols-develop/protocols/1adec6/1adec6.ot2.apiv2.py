metadata = {
    'protocolName': 'Small Molecule Library Prep (Updated)',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt20, numPlates, pbsVol, dmsoVol,
     dilVol, destDilVol, libVol] = get_values(  # noqa: F821
     'mnt20', 'numPlates', 'pbsVol', 'dmsoVol',
     'dilVol', 'destDilVol', 'libVol')

    # load labware
    tips = [
        protocol.load_labware('opentrons_96_tiprack_20ul', s) for s in [7, 10]]

    m20 = protocol.load_instrument('p20_multi_gen2', mnt20, tip_racks=tips)

    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '6')

    srcPlate = protocol.load_labware('thermofast_96_wellplate_200ul', '4')
    destPlate = protocol.load_labware('thermofast_96_wellplate_200ul', '5')
    finalPlates = [
        protocol.load_labware(
            'thermofast_96_wellplate_200ul', s) for s in [1, 2, 3]
        ][:numPlates]

    # Create variables
    dmso = rsvr['A1']
    pbs = rsvr['A2']

    # Add pbsVol of PBS to columns 1-4 + A5-E5
    m20.pick_up_tip()

    for dest in destPlate.rows()[0][:4]:
        m20.transfer(pbsVol, pbs, dest, new_tip='never')

    m20.drop_tip()

    m20.pick_up_tip(tips[0]['D7'])
    m20.transfer(pbsVol, pbs, destPlate['A5'], new_tip='never')
    m20.drop_tip()

    # Add dmsoVol of DMSO to columns 6-10 (neglecting F-H in 10)

    m20.pick_up_tip()

    for dest in destPlate.rows()[0][5:9]:
        m20.transfer(dmsoVol, dmso, dest, new_tip='never')

    m20.drop_tip()

    m20.pick_up_tip(tips[0]['D8'])
    m20.transfer(dmsoVol, dmso, destPlate['A10'], new_tip='never')
    m20.drop_tip()

    # Transfer dilution volume from source to destination
    for src, dest, i in zip(
            srcPlate.rows()[0][:4], destPlate.rows()[0][:4], range(1, 5)):
        m20.pick_up_tip()
        m20.transfer(dilVol, src, dest, mix_after=(4, 20), new_tip='never')
        m20.drop_tip(tips[0]['A'+str(i)])

    m20.pick_up_tip(tips[0]['D9'])
    m20.transfer(dilVol, srcPlate['A5'], destPlate['A5'],
                 mix_after=(4, 20), new_tip='never')
    m20.drop_tip(tips[0]['A5'])

    m20.reset_tipracks()

    for src, dest in zip(destPlate.rows()[0][:5], destPlate.rows()[0][5:10]):
        m20.transfer(destDilVol, src, dest, mix_after=(4, 20))

    m20.starting_tip = tips[0]['A10']

    for _ in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)

    if numPlates != 0:
        protocol.pause(
            'Please manually add reagents. When ready, click RESUME.')

        # Transfer aliquots to destination plate
        for i in range(10):
            m20.pick_up_tip()
            for plate in finalPlates:
                m20.aspirate(libVol, destPlate.rows()[0][i])
                m20.dispense(libVol, plate.rows()[0][i])
            m20.drop_tip()

    protocol.comment('\nProtocol complete!')
