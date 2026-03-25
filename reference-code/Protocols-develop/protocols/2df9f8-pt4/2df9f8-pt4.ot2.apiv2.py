"""Protocol."""
metadata = {
    'protocolName': 'Pooling Deep Well Plates by Column',  # noqa: E501
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""

    [num_plates, num_col, p300_mount] = get_values(  # noqa: F821
        'num_plates', "num_col", "p300_mount")

    num_plates = int(num_plates)
    num_col = int(num_col)

    # load labware
    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['1', '2', '3', '4', '5']]
    plates = [ctx.load_labware(
        'nest_96_wellplate_2ml_deep', slot)
        for slot in ['6', '7', '8', '9', '10']][:num_plates]
    pooled_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '11')

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tiprack)

    # protocol
    for plate in plates:
        for col, dest in zip(plate.rows()[0][:num_col],
                             pooled_plate.rows()[0]):
            m300.pick_up_tip()
            m300.aspirate(100, col)
            m300.dispense(100, dest)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()
