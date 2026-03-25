from opentrons import protocol_api

metadata = {
    'protocolName': 'Human Islets - RT Barcoding',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [m20_mount, m300_mount] = get_values(  # noqa: F821
        "m20_mount", "m300_mount")

    # modules
    temp_mod = ctx.load_module('temperature module gen2', 1)
    temp_mod.set_temperature(25)

    # labware
    samp_plate = temp_mod.load_labware(
                                       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',  # noqa: E501
                                       1)

    barcode_plate = ctx.load_labware(
                                       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',  # noqa: E501
                                       2,
                                       label='barcode plate')

    pcr_strip_plate = ctx.load_labware(
                                       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',  # noqa: E501
                                       3,
                                       label='reagent plate')

    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 4)

    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [5, 6, 7, 8, 9]]

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [10, 11]]

    # pipettes
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)

    # mapping
    trash = ctx.loaded_labwares[12].wells()[0].top()

    wash_buff = reservoir.wells()[0]
    smart_seq_3 = pcr_strip_plate.wells()[0]
    pool_res_well = reservoir.wells()[-2]

    samp_cols = samp_plate.rows()[0]
    barcode_cols = barcode_plate.rows()[0]

    def remove_super(vol):
        for col in samp_cols:
            pick_up()
            m300.aspirate(vol, col)
            m300.dispense(vol, trash)
            m300.drop_tip()

    def pick_up():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f"Replace empty tip rack for {m300}")
            m300.reset_tipracks()
            m300.pick_up_tip()

    # protocol
    ctx.comment('\n---------------ADD BARCODE----------------\n\n')
    for s, d in zip(barcode_cols, samp_cols):
        m20.pick_up_tip()
        m20.aspirate(1, s)
        m20.dispense(1, d)
        m20.mix(3, 1, d)
        m20.drop_tip()

    temp_mod.set_temperature(72)
    ctx.delay(minutes=10)
    temp_mod.set_temperature(4)

    ctx.comment('\n---------------ADD MIX----------------\n\n')

    for col in samp_cols:
        m20.pick_up_tip()
        m20.aspirate(2, smart_seq_3)
        m20.dispense(2, col)
        m20.mix(3, 3, d)
        m20.drop_tip()

    ctx.pause(""""
                  Run thermocycler profile and place sample plate back
                  on temperature module.
                  """)

    ctx.comment('\n---------------ADD WASH BUFFER----------------\n\n')
    m300.pick_up_tip()
    for col in samp_cols:
        m300.aspirate(60, wash_buff)
        m300.dispense(60, col.top())
    m300.drop_tip()

    ctx.comment('\n---------------ADD SMART SEQ3----------------\n\n')

    for _ in range(3):
        m300.pick_up_tip()
        m300.aspirate(100, smart_seq_3)
        m300.dispense(100, samp_plate.rows()[0][0])
        m300.mix(5, 120, samp_plate.rows()[0][0])
        m300.aspirate(150, samp_plate.rows()[0][0])
        m300.dispense(50, pool_res_well)
        m300.dispense(100, samp_plate.rows()[0][1])
        for col in range(1, 11):
            m300.mix(5, 120, samp_plate.rows()[0][col])
            m300.aspirate(150, samp_plate.rows()[0][col])
            m300.dispense(50, pool_res_well)
            m300.dispense(100, samp_plate.rows()[0][col+1])
        m300.mix(5, 120, samp_plate.rows()[0][-1])
        m300.aspirate(150, samp_plate.rows()[0][-1])  # move entire col 12
        m300.dispense(150, pool_res_well)
        m300.drop_tip()
        ctx.comment('\n')
