import math


metadata = {
    'protocolName': 'PCR Prep Deep Well to 384',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, m20_mount] = get_values(  # noqa: F821
        "num_samp", "m20_mount")

    if not 1 <= num_samp <= 382:
        raise Exception("Enter a sample number 1-382")

    # load labware
    deepwell_plates = [ctx.load_labware(
                       'kingfisher_96_wellplate_2000ul',
                       slot) for slot in [4, 1, 5, 2]]

    final_plate = ctx.load_labware('thermofisher_384_wellplate_50ul', 3)
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [10, 7, 11, 8]]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    # mapping
    num_col = math.ceil(num_samp/8)
    samples = [col for plate in deepwell_plates for col in plate.rows()[0]]
    row_order = [0, 1, 0, 1]
    col_order = [0, 0, 1, 1]
    final_map = [col for row_start, col_start in zip(row_order, col_order)
                 for col in final_plate.rows()[row_start][col_start::2]]

    for source, dest in zip(samples[:num_col], final_map):
        m20.pick_up_tip()
        m20.aspirate(5, source, rate=0.5)
        m20.dispense(5, dest, rate=0.5)
        m20.blow_out()
        m20.drop_tip()
        ctx.comment('\n')
