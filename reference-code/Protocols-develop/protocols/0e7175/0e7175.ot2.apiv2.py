metadata = {
    'protocolName': 'Luminex Assay Creating Replicates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_samp, use_middle_2, sample_volume,
        p300_mount] = get_values(  # noqa: F821
        "num_samp", "use_middle_2", "sample_volume", "p300_mount")

    num_samp = int(num_samp)

    if num_samp == 24:
        num_isopaks_source = 1
        num_isopaks_dest = 7
    else:
        num_isopaks_source = 2
        num_isopaks_dest = 6

    # labware
    source_isopaks = [ctx.load_labware('custom_24_wellplate_2000ul', slot)
                      for slot in [10, 11]][:num_isopaks_source]
    dest_isopaks = [ctx.load_labware('custom_24_wellplate_2000ul', slot)
                    for slot in [1, 2, 3, 4, 5, 6, 7]][:num_isopaks_dest]
    tips = [ctx.load_labware('opentrons_96_tiprack_300ul', 9)]

    # pipettes
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount, tip_racks=tips)

    # protocol
    ctx.comment('\n-----------REPLICATING SAMPLES IN PLATE-----------\n\n')
    source_isopak_cols_24 = source_isopaks[0].columns()
    if num_samp > 24:
        source_isopak_cols_48 = source_isopaks[1].columns()
    dest_cols = [pak for pak in dest_isopaks]

    if not use_middle_2:

        del source_isopak_cols_24[2]
        del source_isopak_cols_24[2]
        if num_samp > 24:
            del source_isopak_cols_48[2]
            del source_isopak_cols_48[2]
        dest_cols = [[] for i in range(len(dest_isopaks))]

        for i, pak in enumerate(dest_isopaks):
            for col in pak.rows()[0][:2]:
                dest_cols[i].append(col)
            for col in pak.rows()[0][4:]:
                dest_cols[i].append(col)

    if num_samp == 24:
        for i, s_col in enumerate(source_isopak_cols_24):
            num_paks = num_isopaks_dest
            pickup_vol = sample_volume*1.2
            num_transfers_per_asp = int(p300.max_volume // pickup_vol)
            aspirate_vol = sample_volume*num_transfers_per_asp*1.2 if num_paks*pickup_vol >= p300.max_volume else num_paks*pickup_vol  # noqa: E501

            p300.pick_up_tip()
            p300.aspirate(aspirate_vol, s_col[0])
            vol_ctr = aspirate_vol

            if use_middle_2:
                for pak in dest_isopaks:
                    p300.dispense(sample_volume, pak.rows()[0][i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = sample_volume*1.2
                        num_transfers_per_asp = int(300 // pickup_vol)
                        aspirate_vol = sample_volume*num_transfers_per_asp*1.2 if num_paks*pickup_vol >= 300 else num_paks*pickup_vol  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()
                ctx.comment('\n')

            else:
                for pak in dest_cols:
                    p300.dispense(sample_volume, pak[i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = sample_volume*1.2
                        num_transfers_per_asp = int(300 // pickup_vol)
                        aspirate_vol = sample_volume*num_transfers_per_asp*1.2 if num_paks*pickup_vol >= 300 else num_paks*pickup_vol  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()
                ctx.comment('\n')

    else:
        for i, s_col in enumerate(source_isopak_cols_24):
            num_paks = 3
            pickup_vol = num_paks*sample_volume*1.2
            aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume

            p300.pick_up_tip()
            p300.aspirate(aspirate_vol, s_col[0])
            vol_ctr = aspirate_vol
            if use_middle_2:
                for pak in dest_isopaks[:3]:
                    p300.dispense(sample_volume, pak.rows()[0][i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = num_paks*sample_volume*1.2
                        aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()

            else:
                for pak in dest_cols[:3]:
                    p300.dispense(sample_volume, pak[i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = num_paks*sample_volume*1.2
                        aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()
                ctx.comment('\n')

        ctx.comment('\n\n\n\n')

        for i, s_col in enumerate(source_isopak_cols_48):
            num_paks = 3
            pickup_vol = num_paks*sample_volume*1.2
            aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume

            p300.pick_up_tip()
            p300.aspirate(aspirate_vol, s_col[0])
            vol_ctr = aspirate_vol

            if use_middle_2:
                for pak in dest_isopaks[3:]:
                    p300.dispense(sample_volume, pak.rows()[0][i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = num_paks*sample_volume*1.2
                        aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()

            else:
                for pak in dest_cols[3:]:
                    p300.dispense(sample_volume, pak[i])
                    vol_ctr -= sample_volume
                    num_paks -= 1
                    if vol_ctr < sample_volume + sample_volume*0.1 and num_paks > 0:  # noqa: E501
                        pickup_vol = num_paks*sample_volume*1.2
                        aspirate_vol = pickup_vol if pickup_vol < 300 else p300.max_volume  # noqa: E501
                        p300.dispense(p300.current_volume, s_col[0])
                        p300.aspirate(aspirate_vol, s_col[0])
                        vol_ctr = aspirate_vol
                if p300.current_volume > 0:
                    p300.dispense(p300.current_volume, s_col[0])
                p300.drop_tip()
