metadata = {
    'protocolName': 'Human Islets - Sample Barcoding Oligos',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [m300_mount] = get_values(  # noqa: F821
        "m300_mount")

    # labware
    samp_plate = ctx.load_labware(
                                       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',  # noqa: E501
                                       1,
                                       label='sample plate')

    barcode_plate = ctx.load_labware(
                                       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',  # noqa: E501
                                       3,
                                       label='barcode plate')

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 2)

    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [4, 5, 6, 7, 8]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    # mapping
    trash = ctx.loaded_labwares[12].wells()[0].top()

    wash_buff = reservoir.wells()[0]
    smart_seq_3 = reservoir.wells()[1]
    pool_res_well = reservoir.wells()[-1]

    samp_cols = samp_plate.rows()[0]
    barcode_cols = barcode_plate.rows()[0]

    def remove_super(vol):
        for col in samp_cols:
            m300.pick_up_tip()
            m300.aspirate(vol, col)
            m300.dispense(vol, trash)
            m300.drop_tip()

    # protocol
    ctx.comment('\n---------------ADD BARCODE----------------\n\n')
    for s, d in zip(barcode_cols, samp_cols):
        m300.pick_up_tip()
        m300.aspirate(20, s)
        m300.dispense(20, d)
        m300.mix(10, 50, d)
        m300.drop_tip()

    for _ in range(3):

        ctx.comment('\n---------------ADD WASH BUFFER----------------\n\n')
        m300.pick_up_tip()
        for col in samp_cols:
            m300.aspirate(150, wash_buff)
            m300.dispense(150, col.top())
        m300.drop_tip()

        ctx.pause("Spin at 800g for 6 min")

        ctx.comment('\n---------------REMOVE SUPER----------------\n\n')
        remove_super(150)

    ctx.comment('\n---------------ADD SMART SEQ3----------------\n\n')

    for _ in range(3):
        m300.pick_up_tip()
        m300.aspirate(150, smart_seq_3)
        m300.dispense(150, samp_plate.rows()[0][0])
        m300.mix(5, 150, samp_plate.rows()[0][0])
        m300.aspirate(200, samp_plate.rows()[0][0])
        m300.dispense(50, pool_res_well)
        m300.dispense(150, samp_plate.rows()[0][1])
        for col in range(1, 11):
            m300.mix(5, 150, samp_plate.rows()[0][col])
            m300.aspirate(200, samp_plate.rows()[0][col])
            m300.dispense(50, pool_res_well)
            m300.dispense(150, samp_plate.rows()[0][col+1])
        m300.mix(5, 150, samp_plate.rows()[0][-1])
        m300.aspirate(150, samp_plate.rows()[0][-1])  # move entire col 12
        m300.dispense(150, pool_res_well)
        m300.drop_tip()
