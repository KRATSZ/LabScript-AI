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
    pcr_plate = ctx.load_labware(
                'custom_384_wellplate_50ul', 8)
    pool_plate = ctx.load_labware(
                'custom_384_wellplate_50ul', 9)
    index_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 7)

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 5)

    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [2, 4, 6, 10, 11]]

    mmx_tiprack = ctx.load_labware('opentrons_96_filtertiprack_20ul', 3)

    # instruments
    p20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tipracks)

    # protocol
    ctx.comment('\nADDING MASTERMIX\n\n')
    p20.pick_up_tip(mmx_tiprack.wells()[0])
    for i in range(2):
        for col in pool_plate.rows()[i]:
            p20.aspirate(16, reservoir.wells()[0])
            p20.dispense(16, col)
            p20.blow_out()
        ctx.comment('\n')
    p20.drop_tip()

    ctx.comment('\nADDING INDEX\n\n')
    index_row_order = [0, 0, 1, 1]
    index_col_order = [0, 1, 0, 1]

    col_ctr = 0

    for col_96_plate in range(12):
        p20.pick_up_tip()
        p20.aspirate(8, index_plate.rows()[0][col_96_plate])
        for index_row, index_col in zip(index_row_order, index_col_order):
            p20.dispense(2,
                         pcr_plate.rows()[index_row][index_col+col_ctr],
                         rate=0.5)
        col_ctr += 2
        p20.return_tip()

    ctx.comment('\nADDING SAMPLE\n\n')

    for i in range(2):
        for s_col, d_col in zip(pool_plate.rows()[i], pcr_plate.rows()[i]):
            p20.pick_up_tip()
            p20.aspirate(2, s_col)
            p20.dispense(2, d_col)
            p20.blow_out()
            p20.return_tip()
        ctx.comment('\n')
