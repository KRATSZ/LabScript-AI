import math

metadata = {
    'protocolName': 'Nucleic Acid Purification - Workflow 1',
    'author': 'Sakib <sakib.hossain@opentrons.com>',
    'description': 'Custom Protocol Request',
    'apiLevel': '2.8'
}


def run(protocol):

    [total_samples, pool_size, p300s_mount, p300m_mount,
        deepwell_plate_type] = get_values(  # noqa: F821
        "total_samples", "pool_size", "p300s_mount", "p300m_mount",
        "deepwell_plate_type")

    pool_size = int(pool_size)
    total_samples = int(total_samples)

    # Load Tip Racks
    tiprack_200ul_filter = protocol.load_labware(
        'opentrons_96_filtertiprack_200ul', 5)
    tiprack_300ul = protocol.load_labware('opentrons_96_tiprack_300ul', 6)

    # Load Pipettes
    p300s = protocol.load_instrument('p300_single_gen2', p300s_mount,
                                     tip_racks=[tiprack_200ul_filter])
    p300m = protocol.load_instrument('p300_multi_gen2', p300m_mount,
                                     tip_racks=[tiprack_300ul])

    # Deep Well Plate (DWP)
    deepwell_plate = protocol.load_labware(deepwell_plate_type, 2)

    # Lysis Buffer Reservoir
    buffer_reservoir = protocol.load_labware('nest_1_reservoir_195ml', 3)['A1']

    # Load 7 Tube Racks with Samples in 30 mL Tubes
    tube_racks = []
    for slot in range(1, 12):
        if slot not in protocol.loaded_labwares:
            tube_racks.append(protocol.load_labware('caplugs_6_tuberack_30ml',
                                                    slot))

    all_wells = [well for tube in tube_racks for well
                 in tube.wells()][:total_samples]
    sample_wells = [all_wells[i:i + pool_size] for i in range(0,
                    len(all_wells), pool_size)]
    dest_wells = deepwell_plate.wells()[0:len(sample_wells)]

    # Transfer 40 uL samples into DWP
    protocol.comment(f'Adding 40 uL samples with a pool size of {pool_size}')
    p300s.flow_rate.aspirate = 30
    for s, d in zip(sample_wells, dest_wells):
        p300s.transfer(40, s, d, new_tip='always')

    # Transfer 240 uL of Lysis Buffer into variable wells using multichannel
    buffer_wells = len(dest_wells)
    columns = math.floor(buffer_wells / 8)
    left_over_wells = buffer_wells % 8
    protocol.comment('Transferring 240 uL of Lysis buffer into DWP')
    for i in range(columns):
        p300m.pick_up_tip(tiprack_300ul.columns()[i][0])
        p300m.transfer(240, buffer_reservoir, deepwell_plate.columns()[i][0],
                       new_tip='never')
        p300m.drop_tip()
    if left_over_wells > 0:
        p300m.pick_up_tip(tiprack_300ul.columns()[columns][8-left_over_wells])
        p300m.transfer(240, buffer_reservoir,
                       deepwell_plate.columns()[columns][0], new_tip='never')
        p300m.drop_tip()
