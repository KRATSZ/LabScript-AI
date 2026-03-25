metadata = {
    'protocolName': 'Seed Cells [2/7]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt300, numPlates] = get_values(  # noqa: F821
     'mnt300', 'numPlates')

    # load labware
    tips = [
        protocol.load_labware('opentrons_96_tiprack_300ul', '7')
        ]

    m300 = protocol.load_instrument('p300_multi_gen2', mnt300, tip_racks=tips)

    rsvr = protocol.load_labware('nest_12_reservoir_15ml', '4')
    finalPlates = [
        protocol.load_labware(
            'spl_96_wellplate_200ul_round', s) for s in [1, 2, 3]
        ][:numPlates]

    # Create variable
    rsvr1 = rsvr.wells()[2:7:2]
    rsvr2 = rsvr.wells()[3:8:2]

    # Perform transfer of cells from reservoir to
    for plate, cells1, cells2 in zip(finalPlates, rsvr1, rsvr2):
        m300.pick_up_tip()
        m300.mix(4, 200, cells1)

        for well in plate.rows()[0][:6]:
            m300.transfer(250, cells1, well, new_tip='never')

        m300.drop_tip()
        m300.pick_up_tip()
        m300.mix(4, 200, cells2)

        for well in plate.rows()[0][6:]:
            m300.transfer(250, cells2, well, new_tip='never')

        m300.drop_tip()
