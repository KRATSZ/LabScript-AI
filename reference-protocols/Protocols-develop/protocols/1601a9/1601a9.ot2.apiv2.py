metadata = {
    'protocolName': 'Illumina Beadchip Amplification',
    'author': 'Chaz <chaz@opentrons.com',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}


def run(protocol):
    [p10mnt] = get_values(  # noqa: F821
        'p10mnt')

    # load labware and pipettes
    res = protocol.load_labware('nest_12_reservoir_15ml', '1')
    tips10 = [
        protocol.load_labware(
            'opentrons_96_tiprack_10ul', s) for s in ['4', '5']]
    aplate = protocol.load_labware('axygen_96_wellplate', '3')
    deep_plate = protocol.load_labware('abgene_96_wellplate_800ul', '2')

    p10 = protocol.load_instrument('p10_multi', p10mnt, tip_racks=tips10)

    # Step 1
    wells11 = ['A'+str(i) for i in range(1, 12)]
    wells12 = ['A'+str(i) for i in range(1, 13)]

    ma1 = res['A5']
    naoh = res['A9']

    p10.pick_up_tip()
    for well in wells12:
        p10.transfer(20, ma1, deep_plate[well], new_tip='never')
        p10.blow_out(deep_plate[well].top())
    p10.drop_tip()

    # Step 2

    for well in wells11:
        p10.pick_up_tip()
        p10.transfer(4, aplate[well], deep_plate[well], new_tip='never')
        p10.blow_out(deep_plate[well].top())
        p10.drop_tip()

    # Step 3

    for well in wells12:
        p10.pick_up_tip()
        p10.transfer(4, naoh, deep_plate[well], new_tip='never')
        p10.blow_out(deep_plate[well].top())
        p10.drop_tip()
