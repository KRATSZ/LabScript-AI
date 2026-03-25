metadata = {
    'protocolName': 'DNA Transfer',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [p10mnt] = get_values(  # noqa: F821
        'p10mnt')

    # load labware and pipettes
    tube_plate = protocol.load_labware('micronics_96_tubes', '3')
    plate = protocol.load_labware('axygen_96_wellplate', '2')
    tips10 = [protocol.load_labware('opentrons_96_tiprack_10ul', '5')]

    p10 = protocol.load_instrument('p10_multi', p10mnt, tip_racks=tips10)

    # Step 1
    wells11 = ['A'+str(i) for i in range(1, 12)]

    for well in wells11:
        p10.pick_up_tip()
        p10.transfer(10, tube_plate[well], plate[well], new_tip='never')
        p10.blow_out(plate[well].top())
        p10.drop_tip()
