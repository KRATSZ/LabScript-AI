metadata = {
    'protocolName': 'Quant-iT dsDNA Broad-Range Assay Kit',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [p300mnt, p10mnt] = get_values(  # noqa: F821
        'p300mnt', 'p10mnt')

    # load labware and pipettes
    res = protocol.load_labware('nest_12_reservoir_15ml', '1')
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '4')]
    tips10 = [protocol.load_labware('opentrons_96_tiprack_10ul', '5')]
    aplate = protocol.load_labware('axygen_96_wellplate', '2')
    tube_plate = protocol.load_labware('micronics_96_tubes', '3')

    p300 = protocol.load_instrument('p300_multi', p300mnt, tip_racks=tips300)
    p10 = protocol.load_instrument('p10_multi', p10mnt, tip_racks=tips10)

    # Step 1
    wells11 = ['A'+str(i) for i in range(1, 12)]

    p300.pick_up_tip()

    for well in wells11:
        p300.transfer(99, res['A1'], aplate[well].top(), new_tip='never')

    p300.drop_tip()

    # Step 2
    p300.transfer(95, res['A1'], aplate['A12'])

    # Step 3
    for well in wells11:
        p10.pick_up_tip()
        p10.transfer(1, tube_plate[well], aplate[well], new_tip='never')
        p10.blow_out(aplate[well].top())
        p10.drop_tip()
