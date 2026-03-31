metadata = {
    'protocolName': 'APIv2 PCR Prep 1/4: HYB',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p20_mount, number_of_plates] = get_values(  # noqa: F821
        'p20_mount', 'number_of_plates')

    # load labware and pipette
    pcrcoolplate = 'labcon_96_wellplate_pcr_on_cooler'

    pcrcoolstrip = 'labcon_8strip_pcr_on_cooler'

    tempplate = protocol.load_labware(
        pcrcoolplate, '1', 'Labcon Plate on PCR Cooler')

    pcr_well = protocol.load_labware(
        pcrcoolstrip, '2', 'PCR Strip on PCR Cooler')

    sample_plate = protocol.load_labware(
                'biorad_96_wellplate_200ul_pcr', '3', 'sample plate')
    tipracks = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', str(slot),
            '20uL Tips') for slot in range(4, 12)
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
    samps = sample_plate.rows()[0]

    # step 1

    for i in range(number_of_plates):
        pick_up(pip20)

        mm_count = 0

        for d in dest:
            if mm_count == 0:
                pip20.aspirate(12, pcr_well['A1'])
            pip20.dispense(2, d)
            mm_count += 1
            if mm_count > 5:
                mm_count = 0

        pip20.drop_tip()

        # step 2

        for d, s in zip(dest, samps):
            pick_up(pip20)
            pip20.transfer(8, s, d, new_tip='never')
            pip20.blow_out()
            pip20.drop_tip()

        if i == number_of_plates-1:
            protocol.comment("Part 1/4 (HYB) complete. Please remove plate from \
            Slot 1 and run on PCR program. When ready, load materials and \
            run Part 2/4 (GAP) on the OT-2.")
        else:
            protocol.pause("Part 1/4 (HYB), plate "+str(i+1)+" now complete. \
            Please remove plate from Slot 1 and run on PCR program. You may \
            now load new materials (PCR plate, Sample plate, Mastermix) into \
            the robot. When ready to fill the next plate, click RESUME.")
