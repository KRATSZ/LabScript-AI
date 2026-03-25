metadata = {
    'protocolName': 'Four 96 Deepwell to PCR Plate',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_sets, dest_start_col, p20_mount] = get_values(  # noqa: F821
        "num_sets", "dest_start_col", "p20_mount")

    num_cols = num_sets*4
    dest_start_col -= 1

    if num_sets > 12-dest_start_col:
        raise Exception("""You do not have enough destination columns
                           for the number of sets specified""")

    # labware
    source_plates = [ctx.load_labware('deepwell_96_wellplate_2000ul', slot)
                     for slot in [4, 5, 1, 2]]
    dest_plate = ctx.load_labware('quintara_96_wellplate_300ul', 3)
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
            for slot in [10, 11, 7, 8]]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tips)

    # mapping
    all_source_columns = [col for plate in source_plates
                          for col in plate.rows()[0]][:num_cols]

    chunked_source_columns = [all_source_columns[i:i+4]
                              for i in range(0, len(all_source_columns), 4)]

    # protocol
    ctx.comment('\n-----------Filling Destination Plate-------------\n\n')
    for i, chunk in enumerate(chunked_source_columns):
        for j, well in enumerate(chunk):
            if j == 0 or j == 3:
                vol = 20
            if j == 1 or j == 2:
                vol = 2

            m20.pick_up_tip()
            m20.aspirate(vol, well)
            if vol == 20:
                m20.dispense(vol, dest_plate.rows()[0][dest_start_col+i])
            else:
                m20.dispense(vol,
                             dest_plate.rows()[0][
                                            dest_start_col+i].bottom(z=0.4))
            m20.return_tip()
        ctx.comment('\n\n')
