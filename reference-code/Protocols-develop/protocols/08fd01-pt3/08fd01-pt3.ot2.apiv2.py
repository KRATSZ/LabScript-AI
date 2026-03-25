# flake8: noqa

metadata = {
    'protocolName': 'PCR Prep and Pooling with 384 Plates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [p20_mount] = get_values(  # noqa: F821
        "p20_mount")

    # labware
    pcr_plate_384 = ctx.load_labware(
                'custom_384_wellplate_50ul', 8)
    pool_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 5)


    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [11]]

    # instruments
    p20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tipracks)

    # protocol
    pool_wells = pool_plate.rows()[0][::2][:4]
    row_starts = [0, 0, 1, 1]
    col_starts = [0, 1, 0, 1]
    col_ctr = 0
    airgap = 3



    for row_start, col_start, pool_well in zip(row_starts,
                                               col_starts,
                                               pool_wells):
        p20.pick_up_tip()
        col_ctr = 0

        for _ in range(4):
            for _ in range(3):
                source_well = pcr_plate_384.rows()[row_start][col_start+col_ctr]
                p20.aspirate(3, source_well)
                p20.air_gap(airgap)
                col_ctr += 2
            p20.dispense(3*3+airgap*3, pool_well)

        p20.drop_tip()
