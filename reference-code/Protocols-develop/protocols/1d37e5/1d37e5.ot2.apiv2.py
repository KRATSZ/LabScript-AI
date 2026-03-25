metadata = {
    'protocolName': 'PB Trial (Plate Filling)',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [num_plates] = get_values(  # noqa: F821
     'num_plates')

    # load labware and pipette
    tips = protocol.load_labware('opentrons_96_tiprack_20ul', '10')
    m20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips])

    deepwell = protocol.load_labware('nest_96_wellplate_2ml_deep', '11')
    pb256 = deepwell['A1']
    pb128 = deepwell['A2']
    gmg = deepwell['A3']

    destplates = [
        protocol.load_labware(
            'himic_96_wellplate_400ul', s) for s in range(1, num_plates+1)
        ]

    # Transfer Polymixin B 256
    protocol.comment('Transferring 10uL of Polymixin B 256 to columns 1-6\n')
    m20.pick_up_tip()
    for plate in destplates:
        for dest in plate.rows()[0][:6]:
            m20.transfer(10, pb256, dest, new_tip='never')
    m20.drop_tip()

    # Transfer Polymixin B 128
    protocol.comment('Transferring 10uL of Polymixin B 128 to columns 6-12\n')
    m20.pick_up_tip()
    for plate in destplates:
        for dest in plate.rows()[0][6:]:
            m20.transfer(10, pb128, dest, new_tip='never')
    m20.drop_tip()

    # Transfer Growth Media Gamma
    protocol.comment('Transferring 10uL of Growth Media Gamma to all wells\n')
    m20.pick_up_tip()
    for plate in destplates:
        for dest in plate.rows()[0]:
            m20.transfer(10, gmg, dest, new_tip='never')
    m20.drop_tip()

    protocol.comment('Protocol complete!')
