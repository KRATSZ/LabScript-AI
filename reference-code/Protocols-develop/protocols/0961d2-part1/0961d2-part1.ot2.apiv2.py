metadata = {
    'protocolName': 'plexWell LP384 Part 1',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
    }


def run(protocol):
    [p10_mnt] = get_values(  # noqa: F821
        'p10_mnt')

    # create pipettes and labware
    tips10 = [protocol.load_labware('opentrons_96_filtertiprack_10ul', str(s))
              for s in range(1, 11, 3)]
    pip10 = protocol.load_instrument('p10_multi', p10_mnt, tip_racks=tips10)
    [src1, src2, dst1, dst2] = [
        protocol.load_labware('biorad_96_wellplate_200ul_pcr', s, t)
        for s, t in zip(
            ['2', '5', '3', '6'],
            ['Source 1', 'Source 2', 'Destination 1', 'Destination 2'])]

    res = protocol.load_labware('nest_12_reservoir_15ml', '9')
    buff = res.wells()[0]

    src_plates = src1.rows()[0] + src2.rows()[0]
    dest_plates = dst1.rows()[0] + dst2.rows()[0]

    pip10.flow_rate.aspirate = 3
    pip10.flow_rate.dispense = 6

    # part 1 - add DNA to SBP96 plates
    for src, dest in zip(src_plates, dest_plates):
        pip10.pick_up_tip()
        pip10.transfer(6, src, dest, new_tip='never')
        pip10.mix(5, 6, dest)
        pip10.blow_out(dest.top())
        pip10.drop_tip()

    # part 2 - add Coding buffer
    for dest in dest_plates:
        pip10.pick_up_tip()
        pip10.transfer(5, buff, dest, new_tip='never')
        pip10.mix(10, 5, dest)
        pip10.blow_out(dest.top())
        pip10.drop_tip()

    protocol.comment('Part 1 now complete. Seal plates in slots 3 and 6, \
    pulse-spin, and run on thermal cycler.')
