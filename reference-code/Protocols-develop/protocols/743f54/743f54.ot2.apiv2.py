metadata = {
    'protocolName': 'KingFisher Flex Magnetic Particle Processing Plate Prep',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(protocol):
    [numSamps, pipMnt] = get_values(  # noqa: F821
     'numSamps', 'pipMnt')

    # load labware
    tips = [protocol.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    pip = protocol.load_instrument('p300_single_gen2', pipMnt, tip_racks=tips)

    rsvr1 = protocol.load_labware('nest_1_reservoir_195ml', '7')
    rsvr2 = protocol.load_labware('nest_1_reservoir_195ml', '8')
    rsvr3 = protocol.load_labware('nest_12_reservoir_15ml', '5')
    tubeRack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '6')

    plate1, plate2, plateElution = [
        protocol.load_labware(
            'kingfisher_96_deepwell_plate_2ml',
            s,
            n) for s, n in zip(
                ['4', '1', '2'],
                ['KF Deepwell-96 Wash 1',
                 'KF Deepwell-96 Wash 2',
                 'KF Deepwell-96 Elution'])]

    platePK = protocol.load_labware(
        'biorad_96_wellplate_200ul_pcr', '3', 'KF-96 microplate PK plate')

    # Create Variables
    wash1 = rsvr1.wells()[0]
    wash2 = rsvr2.wells()[0]
    elution = rsvr3.wells()[0]

    protK = [w for w in tubeRack.wells()[:4] for _ in range(24)]

    # Transfer Wash 1
    protocol.comment(f'\nTransferring Wash 1 to {numSamps} wells...')

    pip.pick_up_tip()

    for well in plate1.wells()[:numSamps]:
        for _ in range(2):
            pip.aspirate(175, wash1)
            pip.dispense(175, well)
        pip.aspirate(150, wash1)
        pip.dispense(150, well)

    pip.drop_tip()

    # Transfer Wash 2
    protocol.comment(f'\nTransferring Wash 2 to {numSamps} wells...')

    pip.pick_up_tip()

    for well in plate2.wells()[:numSamps]:
        for _ in range(5):
            pip.aspirate(200, wash2)
            pip.dispense(200, well)
    pip.drop_tip()

    # Transfer Elution
    protocol.comment(f'\nTransferring Elution Buffer to {numSamps} wells...')

    pip.pick_up_tip()

    for well in plateElution.wells()[:numSamps]:
        if pip.current_volume == 0:
            pip.aspirate(200, elution)
        pip.dispense(50, well)

    pip.dispense(pip.current_volume, elution)
    pip.drop_tip()

    # Transfer Proteinase K
    protocol.comment(f'\nTransferring Proteinase K to {numSamps} wells...')

    pip.pick_up_tip()

    for well, src in zip(platePK.wells()[:numSamps], protK):
        if pip.current_volume < 25:
            pip.dispense(pip.current_volume, src)
            pip.aspirate(140, src)
        pip.dispense(5, well)

    pip.drop_tip()

    protocol.comment('\nProtocol is complete!')
