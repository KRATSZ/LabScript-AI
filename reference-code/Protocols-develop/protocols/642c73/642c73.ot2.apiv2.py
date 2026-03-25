metadata = {
    'protocolName': 'PCR Prep - Plate Filling',
    'author': 'Chaz <chaz@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(protocol):
    [numSamps] = get_values(  # noqa: F821
     'numSamps')

    # load labware and pipette
    tips = [protocol.load_labware('opentrons_96_filtertiprack_20ul', '6')]
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    destPlate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '2')
    destWells = [
        well for row in destPlate.rows() for well in row][:numSamps+1]

    tuberacks = [
        protocol.load_labware(
            'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
            s) for s in [1, 4, 7, 10, 3]
            ]
    mm = tuberacks[-1].wells()[0]
    water = tuberacks[-1].wells()[-1]

    samples = []
    for rack in tuberacks[:4]:
        for row in rack.rows():
            for well in row:
                samples.append(well)

    # Transfer Master Mix
    protocol.comment('Transferring 20uL of Master Mix to all wells...\n')

    p20.pick_up_tip()

    for well in destWells:
        p20.aspirate(20, mm)
        p20.dispense(20, well)

    # Transfer water to last well
    protocol.comment('Transferring Water (control) to last well...\n')

    p20.aspirate(5, water)
    p20.dispense(5, destWells[-1])
    p20.mix(2, 20)

    p20.drop_tip()

    # Transfer samples
    protocol.comment('Transferring 5uL of Sample to corresponding wells...\n')
    for src, dest in zip(samples[:numSamps], destWells):
        p20.pick_up_tip()
        p20.aspirate(5, src)
        p20.dispense(5, dest)
        p20.mix(2, 20)
        p20.drop_tip()

    protocol.comment('\nProtocol complete!')
