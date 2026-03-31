metadata = {
    'protocolName': 'Plate Filling with Custom 384-Well Plate',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):

    # labware
    plate384 = protocol.load_labware('flipped_384_plate', '3')
    srcplate = protocol.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '5')
    tips = protocol.load_labware('opentrons_96_tiprack_20ul', '1')

    pip = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips])

    mm_loc = {
        'A1': ['B'+str(i) for i in range(1, 5)],
        'A2': ['A'+str(i) for i in range(1, 5)],
        'A3': ['B'+str(i) for i in range(5, 9)],
        'A4': ['A'+str(i) for i in range(5, 9)],
        'A5': ['A'+str(i) for i in range(9, 13)],
        'A6': ['B'+str(i) for i in range(9, 13)],
        'A7': ['A'+str(i) for i in range(13, 17)],
        'A8': ['B'+str(i) for i in range(13, 17)]
        }

    for i in range(1, 9):
        pip.pick_up_tip()
        tip_vol = 0
        for well in mm_loc['A'+str(i)]:
            if tip_vol == 0:
                pip.aspirate(20, srcplate['A'+str(i)])
                tip_vol = 20
            pip.dispense(10, plate384[well])
            tip_vol -= 10
        pip.drop_tip()

    tip_vol = 0
    pip.pick_up_tip()
    for well in plate384.rows()[10]:
        if tip_vol == 0:
            pip.aspirate(20, srcplate['A11'])
            tip_vol = 20
        pip.dispense(10, well)
        tip_vol -= 10

    for well in plate384.rows()[11]:
        if tip_vol == 0:
            pip.aspirate(20, srcplate['A12'])
            tip_vol = 20
        pip.dispense(10, well)
        tip_vol -= 10

    pip.drop_tip()
