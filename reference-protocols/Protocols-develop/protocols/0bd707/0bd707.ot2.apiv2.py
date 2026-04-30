metadata = {
    'protocolName': 'Media Aliquotting',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(protocol):
    [num_plates, transfer_vol, p1000_mount] = get_values(  # noqa: F821
        'num_plates', 'transfer_vol', 'p1000_mount')

    # labware
    source = [protocol.load_labware(
                'nest_1_reservoir_195ml', s,
                'liquid reservoir').wells()[0] for s in ['11', '10']]

    tuberacks = [protocol.load_labware(
                    'custom_24_tuberack_2000ul',
                    slot, 'custom tuberack') for slot in [
                        2, 3, 5, 6, 7, 8, 9]][:num_plates]
    tiprack = [
        protocol.load_labware(
            'opentrons_96_tiprack_1000ul',
            slot, '1000µl tiprack') for slot in [1, 4]]

    # pipette
    p1000 = protocol.load_instrument(
        'p1000_single_gen2', p1000_mount, tip_racks=tiprack)

    if transfer_vol > 1000 or transfer_vol < 100:
        raise Exception(
            'The Transfer Volume must be within P1000 range (100-1000).')

    if num_plates < 1 or num_plates > 7:
        raise Exception('The Number of Plates must be between 1 and 7.')

    # perform transfers from source 1
    for tubes in tuberacks[:3]:
        for t in tubes.wells():
            p1000.pick_up_tip()
            for _ in range(2):
                p1000.transfer(
                    transfer_vol, source[0], t, air_gap=50, new_tip='never')
            p1000.air_gap(50)
            p1000.drop_tip()

    # perform transfers from source 2
    for tubes in tuberacks[3:]:
        for t in tubes.wells():
            p1000.pick_up_tip()
            for _ in range(2):
                p1000.transfer(
                    transfer_vol, source[1], t, air_gap=50, new_tip='never')
            p1000.air_gap(50)
            p1000.drop_tip()
