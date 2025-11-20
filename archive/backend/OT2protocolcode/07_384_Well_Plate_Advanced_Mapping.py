metadata = {
    'protocolName': '384 Plate to 96 Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [p20_mount] = get_values(  # noqa: F821
        "p20_mount")

    # labware
    source_plate = ctx.load_labware('appliedbiosystem_384_wellplate_40ul', 1)
    dest_plate = ctx.load_labware('quintara_96_wellplate_300ul', 2)
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
            for slot in [10, 11, 7, 8]]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tips)

    # mapping
    all_source_wells = [
                        col
                        for i, j in zip([0, 0, 1, 1], [0, 1, 0, 1])
                        for col in source_plate.rows()[i][j::2]
                        ]

    chunked_source_cols = [all_source_wells[i:i+4]
                           for i in range(0, len(all_source_wells), 4)]

    for chunk, dest_col in zip(
                                  chunked_source_cols,
                                  dest_plate.rows()[0]
                                          ):

        for j, well in enumerate(chunk):
            if j == 0 or j == 3:
                vol = 20
            if j == 1 or j == 2:
                vol = 2
            m20.pick_up_tip()
            m20.aspirate(vol, well)
            m20.dispense(vol, dest_col)
            m20.return_tip()
        ctx.comment('\n\n')
