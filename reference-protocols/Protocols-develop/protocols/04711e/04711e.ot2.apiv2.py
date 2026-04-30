# flake8: noqa

import math

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp,
      p300_mount, m20_mount] = get_values(  # noqa: F821
      "num_samp", "p300_mount", "m20_mount")

    # num_samp = 16
    # p300_mount = 'left'
    # m20_mount = 'right'

    # labware
    tuberack = ctx.load_labware('opentrons_24_tuberack_2000ul', 4)

    source_plate = ctx.load_labware('pcrplate_96_wellplate_200ul', 1)
    middle_plate = ctx.load_labware('pcrplate_96_wellplate_200ul', 2)
    final_plate = ctx.load_labware('pcrplate_96_wellplate_200ul', 3)

    tip300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
              for slot in [6]]
    tip20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
               for slot in [10, 11]]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tip300)
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount,
                                tip_racks=tip20)

    # mapping
    mmx = tuberack['A1']
    primer = tuberack['A2']
    final_mmx = tuberack['A3']
    num_col = math.ceil(num_samp/8)

    # protocol
    ctx.comment('\n---------------MAKING MASTERMIX----------------\n\n')
    mmx_vol = 9.1
    primer_vol = 5.57

    p300.pick_up_tip()
    p300.transfer(mmx_vol*num_samp*1.15, mmx, final_mmx, new_tip='never')
    p300.drop_tip()

    total_vol = num_samp*(primer_vol+mmx_vol)
    p300.pick_up_tip()
    p300.transfer(primer_vol*num_samp*1.15, primer, final_mmx, new_tip='never')
    for _ in range(20):
        p300.aspirate(total_vol if total_vol < 300 else 300, final_mmx)
        p300.dispense(total_vol if total_vol < 300 else 300, final_mmx.top(z=-3))
    p300.mix(20, total_vol if total_vol < 300 else 300, final_mmx)
    p300.drop_tip()

    vol_per_col_well = (mmx_vol+primer_vol)*12*1.1
    p300.pick_up_tip()
    for well in middle_plate.columns()[0]:
        p300.aspirate(vol_per_col_well, final_mmx)
        p300.dispense(vol_per_col_well, well)
    p300.drop_tip()

    ctx.comment('\n---------------DISTRIBUTING MASTERMIX----------------\n\n')
    m20.pick_up_tip()
    for col in final_plate.rows()[0][:num_col]:
        m20.aspirate(14.7, middle_plate.rows()[0][0])
        m20.dispense(14.7, col)
    m20.drop_tip()

    ctx.comment('\n---------------DISTRIBUTING SAMPLE----------------\n\n')
    for s, d in zip(source_plate.rows()[0][:num_col], final_plate.rows()[0]):
        m20.pick_up_tip()
        m20.aspirate(4, s)
        m20.dispense(4, d)
        m20.mix(5, 15, d)
        m20.drop_tip()
