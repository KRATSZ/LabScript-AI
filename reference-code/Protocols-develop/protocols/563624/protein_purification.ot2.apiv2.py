metadata = {
    'protocolName': 'Phytip Protein Purification',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [m300_mount, deep_name, plate_name, start_column,
     end_column] = get_values(  # noqa: F821
        'm300_mount', 'deep_name', 'plate_name', 'start_column', 'end_column')

    # load labware
    tiprack = ctx.load_labware('phynexus_96_tiprack_300ul', '1',
                               '300ul resin tiprack')
    plate_labels = [
        'equilibration buffer', 'sample', 'wash buffer 1', 'wash buffer 2'
    ]
    mix_plates = [
        ctx.load_labware(deep_name, str(slot), name + ' plate')
        for slot, name in zip(range(2, 6), plate_labels)] + [
            ctx.load_labware('eppendorftwintec_96_wellplate_150ul', '6',
                             'elution buffer plate')
    ]

    # check
    if start_column < 1 or end_column > 12:
        raise Exception('Invalid columns must be between 1 and 12.')
    if start_column > end_column:
        raise Exception('Start column must be before end column')

    m300 = ctx.load_instrument(
        'p300_multi_gen2', m300_mount, tip_racks=[tiprack])
    m300.flow_rate.aspirate = 5
    m300.flow_rate.dispense = 5

    # mix sequences
    def plate_mix(cycles, volume, plate, col, delay=20, blow_out=False):
        mix_loc = plate.rows_by_name()['A'][col]
        for _ in range(cycles):
            m300.aspirate(volume, mix_loc)
            ctx.delay(seconds=delay)
            m300.dispense(volume, mix_loc)
            ctx.delay(seconds=delay)
            if blow_out:
                m300.blow_out(mix_loc.top(-2))

    for col in range(start_column-1, end_column):
        tip_loc = tiprack.rows_by_name()['A'][col]
        m300.pick_up_tip(tip_loc)

        # perform
        plate_mix(2, 90, mix_plates[0], col)
        plate_mix(4, 180, mix_plates[1], col, blow_out=True)
        plate_mix(2, 180, mix_plates[2], col)
        plate_mix(2, 180, mix_plates[3], col, blow_out=True)
        plate_mix(4, 70, mix_plates[4], col, blow_out=True)
        m300.return_tip()
