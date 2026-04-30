metadata = {
    'protocolName': 'APIv2 PCR Prep 4/4: PCR',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p20_mount, number_of_plates] = get_values(  # noqa: F821
        'p20_mount', 'number_of_plates')

    # load labware
    pcrcoolplate = 'labcon_96_wellplate_pcr_on_cooler'
    pcrcoolstrip = 'labcon_8strip_pcr_on_cooler'

    tempplate = protocol.load_labware(
        pcrcoolplate, '1', 'Labcon Plate on PCR Cooler')

    pcr_well = protocol.load_labware(
        pcrcoolstrip, '2', 'PCR Strip on PCR Cooler')

    primer_plate = protocol.load_labware(
                'biorad_96_wellplate_200ul_pcr', '4', 'primer plate (BioRad)')
    dna_plate = protocol.load_labware(
                'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '3',
                'DNA plate on Aluminum Block')
    tipracks = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', slot) for slot in range(5, 12)
    ]

    # Check number of plates
    if number_of_plates > 6 or number_of_plates < 1:
        raise Exception('The number of plates should be between 1 and 6.')

    # create pipette

    pip20 = protocol.load_instrument(
        'p20_multi_gen2', p20_mount, tip_racks=tipracks)

    tip20_max = len(tipracks)*12
    tip20_count = 0

    def pick_up(pip):
        nonlocal tip20_count

        if tip20_count == tip20_max:
            protocol.pause(
                'Replace 20ul tipracks before resuming.')
            pip20.reset_tipracks()
            tip20_count = 0
        pip20.pick_up_tip()
        tip20_count += 1

    dest = tempplate.rows()[0]
    primers = primer_plate.rows()[0]
    samps = dna_plate.rows()[0]

    for i in range(number_of_plates):
        # step 1

        pick_up(pip20)

        for d in dest:
            pip20.transfer(8.7, pcr_well['A1'], d, new_tip='never')
            pip20.blow_out()

        pip20.drop_tip()

        # step 2

        for p, d in zip(primers, dest):
            pick_up(pip20)
            pip20.transfer(1.3, p, d, new_tip='never')
            pip20.blow_out()
            pip20.drop_tip()

        # step 3

        for s, d in zip(samps, dest):
            pick_up(pip20)
            pip20.transfer(5, s, d, new_tip='never')
            pip20.blow_out()
            pip20.drop_tip()

        if i == number_of_plates-1:
            protocol.comment("Congratulations, you have completed step 4/4 \
            of this protocol. Please remove samples from OT-2 \
            and properly store.")
        else:
            protocol.pause("Congratulations, you have completed step 4/4 \
            of this protocol for plate "+str(i+1)+". Please remove samples \
            from OT-2 and properly store. When you're ready to fill the \
            next plate, please load proper materials and click RESUME.")
