"""Protocol."""
metadata = {
    'protocolName': 'Plate Filling Heat Inactivated Covid Samples for PCR - Part 3',  # noqa: E501
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):
    """Protocol."""

    [num_plates] = get_values(  # noqa: F821
        'num_plates')

    # load labware
    reservoirs = [ctx.load_labware('nest_1_reservoir_195ml', slot)
                  for slot in ['1', '2']]
    tiprack = [ctx.load_labware('opentrons_96_tiprack_300ul', '3')]
    plates = [ctx.load_labware(
        'nest_96_wellplate_2ml_deep', slot)
        for slot in ['4', '5', '6', '7', '8', '9', '10', '11']][:num_plates]

    # load instrument
    p300L = ctx.load_instrument('p300_multi_gen2', "left",
                                tip_racks=tiprack)
    p300R = ctx.load_instrument('p300_multi_gen2', "right",
                                tip_racks=tiprack)

    cols_L = [col for plate in plates for col in plate.rows()[0][::2]]
    cols_R = [col for plate in plates for col in plate.rows()[0][1::2]]
    res_wells = [well for res in reservoirs for well in res.wells()]

    # protocol
    p300L.pick_up_tip()
    p300R.pick_up_tip()
    for i, (s, left, right) in enumerate(zip(res_wells*12,
                                             cols_L,
                                             cols_R)):
        for _ in range(2):
            p300L.aspirate(300, s)
            p300R.aspirate(300, s)
            p300L.dispense(300, left)
            p300L.blow_out()
            p300R.dispense(300, right)
            p300R.blow_out()
        ctx.comment('\n\n')
    p300L.drop_tip()
    p300R.drop_tip()
