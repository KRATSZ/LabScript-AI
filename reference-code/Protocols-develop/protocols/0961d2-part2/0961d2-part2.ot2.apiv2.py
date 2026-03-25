metadata = {
    'protocolName': 'plexWell LP384 Part 2',
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
    dest_plates = [
        protocol.load_labware('biorad_96_wellplate_200ul_pcr', str(s), t)
        for s, t in zip(
            range(2, 3*num_pl, 3),
            ['Plate 1', 'Plate 2', 'Plate 3', 'Plate 4'])]

    res = protocol.load_labware('nest_12_reservoir_15ml', '9')
    buff = res.wells()[1]

    pip10.flow_rate.aspirate = 3
    pip10.flow_rate.dispense = 6

    for plate in dest_plates:
        for row in plate.rows()[0]:
            pip10.pick_up_tip()
            pip10.transfer(7.5, buff, row, new_tip='never')
            pip10.mix(5, 8, row)
            pip10.blow_out(row.top())
            pip10.drop_tip()

    protocol.comment('Part 2 now complete. Seal plates in all slots, \
    pulse-spin, and run on thermal cycler.')
