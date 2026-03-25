metadata = {
    'protocolName': 'UTI Batch qPCR Setup',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [tip_start, m20_mount] = get_values(  # noqa: F821
        "tip_start", "m20_mount")

    if not 1 <= tip_start <= 12:
        raise Exception("Enter a column number between 1-12")

    # load labware
    source_plate = ctx.load_labware('thermofisherscientificdeepwell_96_wellplate_2000ul', 4)  # noqa: E501
    dest_plate = ctx.load_labware('thermofisher_384_wellplate_50ul', 5)
    tips = ctx.load_labware('opentrons_96_tiprack_20ul', 6)

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=[tips])

    tip_cols = [col for col in tips.rows()[0]][tip_start-1:]

    tip_pickups_by_col = [8, 8]

    for i, pickup in enumerate(tip_pickups_by_col):
        if pickup > 0:
            m20.pick_up_tip(tip_cols[i])
            for dest in dest_plate.rows()[i]:
                m20.aspirate(10, source_plate.rows()[0][i])
                m20.dispense(10, dest)
            m20.drop_tip()
            ctx.comment('\n')
