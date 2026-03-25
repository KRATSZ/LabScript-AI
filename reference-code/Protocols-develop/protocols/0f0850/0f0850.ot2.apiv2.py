# flake8: noqa
from opentrons import types

metadata = {
    'protocolName': 'Mastermix Creation and Distribution',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp_mmx, num_samp_lysis, vol_primer, vol_pcr_mix,
        vol_lysis_mix, m20_mount, p300_mount] = get_values(  # noqa: F821
        "num_samp_mmx", "num_samp_lysis", "vol_primer", "vol_pcr_mix",
            "vol_lysis_mix", "m20_mount", "p300_mount")

    # num_samp_mmx = 96
    # num_samp_lysis = 48
    # vol_primer = 0.5
    # vol_pcr_mix = 10
    # vol_lysis_mix = 20
    # m20_mount = 'left'
    # p20_mount = 'right'

    # labware
    temp_mod = ctx.load_module('temperature module gen2', 4)
    reagent_block = temp_mod.load_labware('tuberack_24_wellplate_1500ul')
    lysis_plate = ctx.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul', 5)
    mmx_plate = ctx.load_labware('genesee_96_wellplate_200ul', 6)

    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in [10, 11]]

    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [9]]

    # pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips300)


    num_chan = 1
    tips_ordered = [
        tip
        for row in tips20[0].rows()[
            len(tips20[0].rows())-num_chan::-1*num_chan]
        for tip in row]

    tip_count = 0

    def pick_up_one():

        mounted_on = {"left": types.Mount.LEFT, "right": types.Mount.RIGHT}

        pick_up_current = 0.1  # 150 mA for single tip
        ctx._hw_manager.hardware._attached_instruments[
          mounted_on[m20.mount]].update_config_item(
          'pick_up_current', pick_up_current)
        nonlocal tip_count
        m20.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # mapping
    temp_mod.set_temperature(4)
    taq_mid_red = reagent_block.rows()[0][0]
    forward_primer = reagent_block.rows()[0][1]
    reverse_primer = reagent_block.rows()[0][2]
    h20 = reagent_block.rows()[0][3]

    worm_lysis_buffer_A = reagent_block.rows()[1][0]
    worm_lysis_buffer_B = reagent_block.rows()[1][2]

    taq_mid_red_vol = 5*num_samp_mmx
    forward_primer_vol = vol_primer*num_samp_mmx
    reverse_primer_vol = vol_primer*num_samp_mmx
    h20_vol_mmx = 3*num_samp_mmx
    h20_vol_lysis = 7*num_samp_lysis
    worm_lysis_buffer_A_vol = 3*num_samp_lysis
    worm_lysis_buffer_B_vol = num_samp_lysis

    # protocol
    ctx.comment('\n---------------Making Mastermix, Buffer Mix----------------\n\n')

    mmx_reagents = [taq_mid_red, forward_primer, reverse_primer, h20]
    mmx_vols = [taq_mid_red_vol, forward_primer_vol, reverse_primer_vol, h20_vol_mmx]
    dest_tube_mmx = reagent_block['A6']

    for i, (mmx_reagent, vol) in enumerate(zip(mmx_reagents, mmx_vols)):

        if vol > 20:
            p300.pick_up_tip()
            pip = p300
        else:
            pick_up_one()
            pip = m20
        pip.transfer(vol*1.15, mmx_reagent, dest_tube_mmx, new_tip='never')

        if i == len(mmx_reagents)-1:
            if not p300.has_tip:
                p300.pick_up_tip()
            p300.mix(15, 200, dest_tube_mmx)


        if p300.has_tip:
            p300.drop_tip()
        if m20.has_tip:
            m20.drop_tip()

    # lysis_buffer
    lysis_reagents = [worm_lysis_buffer_A, worm_lysis_buffer_B, h20]
    lysis_vols = [taq_mid_red_vol, forward_primer_vol, reverse_primer_vol, h20_vol_lysis]
    dest_tube_lysis = reagent_block['B6']

    for i, (lysis_reagent, vol) in enumerate(zip(lysis_reagents, lysis_vols)):

        if vol > 20:
            p300.pick_up_tip()
            pip = p300
        else:
            pick_up_one()
            pip = m20
        pip.transfer(vol*1.15, lysis_reagent, dest_tube_lysis, new_tip='never')

        if i == len(lysis_reagents)-1:
            if not p300.has_tip:
                p300.pick_up_tip()
            p300.mix(15, 200, dest_tube_lysis)

        if p300.has_tip:
            p300.drop_tip()
        if m20.has_tip:
            m20.drop_tip()

    pick_up_one()
    for well in mmx_plate.wells()[:num_samp_mmx]:
        m20.aspirate(vol_pcr_mix, dest_tube_mmx)
        m20.dispense(vol_pcr_mix, well)
    m20.drop_tip()

    lysis_wells = [well for col in lysis_plate.columns()[::2] for well in col][:num_samp_lysis]
    pick_up_one()
    for well in lysis_wells:
        m20.aspirate(vol_lysis_mix, dest_tube_lysis)
        m20.dispense(vol_lysis_mix, well)
    m20.drop_tip()
