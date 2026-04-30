metadata = {
    'protocolName': 'qPCR GCN Prep',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


def run(protocol):
    [p10mnt, p300mnt, wet_tip] = get_values(  # noqa: F821
        'p10mnt', 'p300mnt', 'wet_tip')

    # labware and pipette set-up
    tuberack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '4',
        'Tube Rack')
    DNA_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '2', 'DNA Plate')
    qPCR_plate = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '1', 'qPCR Plate')
    tips10 = [protocol.load_labware(
        'opentrons_96_tiprack_10ul', s, 'Single 10ul Tip') for s in ['5', '6']]
    tips10s = protocol.load_labware(
        'opentrons_96_tiprack_10ul', '3', '10ul Tips')
    tips300 = protocol.load_labware(
        'opentrons_96_tiprack_300ul', '7', '300ul Tips')

    p10 = protocol.load_instrument('p10_multi', p10mnt, tip_racks=tips10)
    p300 = protocol.load_instrument(
        'p300_single_gen2', p300mnt, tip_racks=[tips300])

    # transfer of Mix 1 (22ul) from the tube-rack (A1) to the qPCR plate
    for well in ['A1', 'A2']:
        p300.pick_up_tip()
        if wet_tip == 'yes':
            p300.mix(1, 22, tuberack['A1'])
        p300.transfer(22, tuberack['A1'], qPCR_plate[well],
                      blow_out=True, touch_tip=True, new_tip='never')
        p300.drop_tip()

    # transfer of Mix 2 (22ul) from the tube-rack (B1) to the qPCR plate
    b1_wells = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'B2', 'C2', 'D2',
                'E2', 'F2', 'G2', 'H2', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12']

    for well in b1_wells:
        p300.pick_up_tip()
        if wet_tip == 'yes':
            p300.mix(1, 22, tuberack['B1'])
        p300.transfer(22, tuberack['B1'], qPCR_plate[well],
                      blow_out=True, touch_tip=True, new_tip='never')
        p300.drop_tip()

    # transfer of Mix 3 (22ul) from the tube-rack (C1) to the qPCR plate
    c1_wells = ['A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
                'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
                'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
                'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
                'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
                'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
                'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
                'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
                'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
                'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']

    for well in c1_wells:
        p300.pick_up_tip()
        if wet_tip == 'yes':
            p300.mix(1, 22, tuberack['C1'])
        p300.transfer(22, tuberack['C1'], qPCR_plate[well],
                      blow_out=True, touch_tip=True, new_tip='never')
        p300.drop_tip()

    # transfer spike DNA into the wells A1, A2
    for well in ['A1', 'A2']:
        p10.pick_up_tip()
        if wet_tip == 'yes':
            p10.mix(1, 3, tuberack['D5'])
        p10.aspirate(3, tuberack['D5'])
        p10.dispense(3, qPCR_plate[well])
        p10.touch_tip(qPCR_plate[well])
        p10.drop_tip()

    # transfer GCN DNA standard 1 into the wells A1, A2
    for well in ['A1', 'A2']:
        p10.pick_up_tip()
        if wet_tip == 'yes':
            p10.mix(1, 3, tuberack['A6'])
        p10.aspirate(3, tuberack['A6'])
        p10.dispense(3, qPCR_plate[well])
        p10.mix(2, 10, qPCR_plate[well])
        p10.touch_tip(qPCR_plate[well])
        p10.drop_tip()

    # transfer GCN DNA standard 2 into the wells A3, A4
    for well in ['A3', 'A4']:
        p10.pick_up_tip()
        if wet_tip == 'yes':
            p10.mix(1, 3, tuberack['B6'])
        p10.aspirate(3, tuberack['B6'])
        p10.dispense(3, qPCR_plate[well])
        p10.mix(2, 10, qPCR_plate[well])
        p10.touch_tip(qPCR_plate[well])
        p10.drop_tip()

    # transfer GCN DNA standard 3 into the wells A5, A6
    for well in ['A5', 'A6']:
        p10.pick_up_tip()
        if wet_tip == 'yes':
            p10.mix(1, 3, tuberack['C6'])
        p10.aspirate(3, tuberack['C6'])
        p10.dispense(3, qPCR_plate[well])
        p10.mix(2, 10, qPCR_plate[well])
        p10.touch_tip(qPCR_plate[well])
        p10.drop_tip()

    # transfer H2O into the wells A7 - A12 NTC
    for well in ['A' + str(i) for i in range(7, 13)]:
        p10.pick_up_tip()
        if wet_tip == 'yes':
            p10.mix(1, 3, tuberack['D1'])
        p10.aspirate(3, tuberack['D1'])
        p10.dispense(3, qPCR_plate[well])
        p10.mix(2, 10, qPCR_plate[well])
        p10.touch_tip(qPCR_plate[well])
        p10.drop_tip()

    # pre-wet the pipette tips p10 + mixing the DNA
    dna_row = DNA_plate['A1']
    qpcr_rows = qPCR_plate.rows_by_name()['A']

    # transfer GCN DNA with 8-channel pipette into the rows 1 - 12 on the qPCR
    # plate, mixing 3 times after
    for row, tip in zip(qpcr_rows, ['A'+str(i) for i in range(1, 13)]):
        p10.pick_up_tip(tips10s[tip])
        if wet_tip == 'yes':
            p10.mix(1, 3, dna_row)
        p10.transfer(3.5, dna_row, row, new_tip='never')
        p10.mix(2, 10, row)
        p10.touch_tip(row)
        p10.drop_tip()

    protocol.home()

    protocol.comment('THIS IS IT')
