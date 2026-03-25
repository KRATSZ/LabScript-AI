metadata = {
    'protocolName': '8-Pin Pickup',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):

    [num_cols, m300_type, m300_mount] = get_values(  # noqa: F821
        'num_cols', 'm300_type', 'm300_mount')

    # check
    if not 1 <= num_cols <= 12:
        raise Exception('Invalid number of columns (must be 1-12).')

    # labware
    plate1, plate2 = [
        ctx.load_labware('corning_96_wellplate_360ul_flat', slot,
                         'plate ' + str(i+1))
        for i, slot in enumerate(['1', '2'])]
    pinrack = [ctx.load_labware('opentrons_96_tiprack_300ul', '5',
                                'custom pin adapter')]

    # pipette
    m300 = ctx.load_instrument(m300_type, m300_mount, tip_racks=pinrack)
    m300.pick_up_tip()
    m300.aspirate(1, plate1.rows()[0][0].top(1))
    m300.dispense(1)
    m300.aspirate(1, plate2.rows()[0][0].top(1))
    m300.dispense(1)

    for col1, col2 in zip(plate1.rows()[0], plate2.rows()[0]):
        # plate 1
        m300.default_speed = 40
        for _ in range(3):
            m300.move_to(col1.top(1))
            m300.move_to(col1.bottom(-0.5))
        m300.default_speed = 400

        # plate 2
        m300.default_speed = 40
        m300.move_to(col2.top(1))
        m300.move_to(col2.bottom(-0.5))
        ctx.delay(seconds=3)
        m300.default_speed = 400

    m300.default_speed = 40
    m300.return_tip()
