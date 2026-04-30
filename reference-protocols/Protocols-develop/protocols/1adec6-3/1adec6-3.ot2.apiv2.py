metadata = {
    'protocolName': 'Transfer Small Molecules [3/7]',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [mnt20, numPlates, tVol, mixP300] = get_values(  # noqa: F821
     'mnt20', 'numPlates', 'tVol', 'mixP300')

    # load labware
    tips = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', s) for s in [4, 7, 10]
            ]

    m20 = protocol.load_instrument('p20_multi_gen2', mnt20, tip_racks=tips)

    srcPlate = protocol.load_labware('thermofast_96_wellplate_200ul', '6')
    finalPlates = [
        protocol.load_labware(
            'spl_96_wellplate_200ul_flat', s) for s in [1, 2, 3]
        ][:numPlates]

    if mixP300:
        tips300 = [
            protocol.load_labware(
                'opentrons_96_tiprack_300ul', s) for s in [5, 8, 11]
                ]
        mnt300 = 'left' if mnt20 == 'right' else 'right'
        m300 = protocol.load_instrument(
            'p300_multi_gen2', mnt300, tip_racks=tips300)

    for plate in finalPlates:
        for src, dest in zip(srcPlate.rows()[0][:10], plate.rows()[0][:10]):
            m20.transfer(tVol, src, dest, mix_before=(5, 10))
        if mixP300:
            for dest in plate.rows()[0][:10]:
                m300.pick_up_tip()
                m300.mix(3, 200, dest)
                m300.drop_tip()
        protocol.pause('Please empty waste bin with used tips.')
