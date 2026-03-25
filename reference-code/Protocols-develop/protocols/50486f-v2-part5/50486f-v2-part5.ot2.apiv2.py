metadata = {
    'protocolName': 'APIv2 PCR Prep: POOL',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p20_mount, tip_strategy] = get_values(  # noqa: F821
        'p20_mount', 'tip_strategy')

    ctp = 'custom_pcr_plate_for_tempdeck'

    pcr_plates = [
        protocol.load_labware(
            ctp, str(slot), 'PCR product Plate') for slot in range(2, 6)]
    pcr_well = protocol.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        '1', 'chilled aluminum block w/ PCR strip')
    tipracks = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', str(slot)) for slot in range(6, 11)]

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

    dest = pcr_well['A1']

    # transfer 2ul of sample to 8-well PCR strip
    if tip_strategy == 'different tip':
        for plate in pcr_plates:
            for col in plate.rows()[0]:
                pick_up(pip20)
                pip20.transfer(2, col, dest, new_tip='never')
                pip20.blow_out()
                pip20.drop_tip()
    else:
        pick_up(pip20)
        for plate in pcr_plates:
            for col in plate.rows()[0]:
                pip20.transfer(2, col, dest, new_tip='never')
                pip20.blow_out()
        pip20.drop_tip()

    protocol.comment("Pooling protocol now complete.")
