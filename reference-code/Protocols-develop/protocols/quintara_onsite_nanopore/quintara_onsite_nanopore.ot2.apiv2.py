metadata = {
    'protocolName': 'Nanopore Aliquoting',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_plates, p20_mount] = get_values(  # noqa: F821
        "num_plates", "p20_mount")

    # labware
    source_plate = ctx.load_labware('barcode_96_wellplate_200ul', 9,
                                    label='Source Plate')
    dest_plates = [ctx.load_labware('combo_96_wellplate_300ul',
                                    slot, label='Dest Plate')
                   for slot in [
                                1, 2, 3, 4, 5, 6, 7
                                ][:num_plates]]

    water_res = ctx.load_labware('nest_12_reservoir_15ml', 8)
    tips = [ctx.load_labware('opentrons_96_tiprack_20ul', slot)
            for slot in [10]]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tips)

    # mapping
    dest_cols = [plate.rows()[0][i]
                 for i in range(12) for plate in dest_plates]

    water = water_res.wells()[0]

    # protocol
    ctx.comment('\n--------------ADDING BARCODE TO PLATES--------------\n\n')
    d_col_ctr = 0
    for s in source_plate.rows()[0]:
        m20.pick_up_tip()
        m20.aspirate(8.5, water)
        m20.dispense(8.5, s)
        m20.mix(3, 14, s)
        for _ in range(num_plates):
            m20.aspirate(2, s, rate=0.5)
            m20.dispense(2, dest_cols[d_col_ctr], rate=0.5)
            # m20.blow_out() ????????????????????
            d_col_ctr += 1
        m20.drop_tip()
        ctx.comment('\n\n')
