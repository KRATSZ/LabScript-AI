metadata = {
    'protocolName': 'plexWell LP384 Part 4',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
    }


def run(protocol):
    [mnt, num_tubes] = get_values(  # noqa: F821
        'mnt', 'num_tubes')

    # check for number of tubes
    if num_tubes > 12 or num_tubes < 1:
        raise Exception('Number of Tubes should be between 1  and 24.')

    # create pipette and labware
    tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', '1')]
    pip300 = protocol.load_instrument('p300_single_gen2', mnt, tip_racks=tips)
    tube_rack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '6',
        'Tube Rack')
    src_plates = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '3', 'Plate')

    tubes = tube_rack.wells()[:num_tubes]
    rows = src_plates.columns()[:num_tubes]

    for src, dest in zip(rows, tubes):
        pip300.pick_up_tip()
        for well in src:
            pip300.transfer(110, well, dest, new_tip='never')
            pip300.mix(2, 100, dest)
            pip300.blow_out(dest.top())
        pip300.drop_tip()

    protocol.comment('Protocol complete. Check tubes for bubbles and centrifuge\
     if necessary.')
