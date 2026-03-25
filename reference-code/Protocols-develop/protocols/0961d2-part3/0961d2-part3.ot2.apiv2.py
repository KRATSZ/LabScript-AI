metadata = {
    'protocolName': 'plexWell LP384 Part 3',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
    }


def run(protocol):
    [p10_mnt, num_pl] = get_values(  # noqa: F821
        'p10_mnt', 'num_pl')

    # check for correct number of plates
    if num_pl > 4 or num_pl < 1:
        raise Exception('The number of plates must be between 1 and 4.')

    # create pipettes and tips
    tips10 = [protocol.load_labware('opentrons_96_filtertiprack_10ul', str(s))
              for s in range(1, (3*num_pl-1), 3)]
    pip10 = protocol.load_instrument('p10_multi', p10_mnt, tip_racks=tips10)
    src_plates = [
        protocol.load_labware('biorad_96_wellplate_200ul_pcr', str(s), t)
        for s, t in zip(
            range(2, 3*num_pl, 3),
            ['Plate 1', 'Plate 2', 'Plate 3', 'Plate 4'])]

    dest_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '3', 'Destination Plate')

    pip10.flow_rate.aspirate = 3
    pip10.flow_rate.dispense = 6
    i = 0

    for plate in src_plates:
        for row in plate.rows()[0]:
            dest = dest_plate.rows()[0][i//6]
            pip10.pick_up_tip()
            for _ in range(2):
                pip10.transfer(9, row, dest, new_tip='never')
                pip10.mix(2, 8, dest)
                pip10.blow_out(dest.top())
            pip10.drop_tip()
            i += 1

    protocol.comment('If bubbles are present, please centrifuge to remove \
    bubbles before proceeding to Part 4.')
