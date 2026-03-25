metadata = {
    'protocolName': 'SuperScript III: qRT-PCR Prep with CSV File',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [num_col, m20_mount] = get_values(  # noqa: F821
        "num_col", "m20_mount")

    if not 1 <= num_col <= 6:
        raise Exception("Enter a column number between 1-6")

    # load labware
    sample_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 1)
    mmx_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 2)
    pool_mmx_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 3)
    final_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', 4)

    # load tipracks
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                for slot in [10, 11]]

    # load pipettes
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tipracks)

    # mapping
    mmx = mmx_plate.wells()[0]
    pool_reagents = [pool_mmx_plate.rows()[0][0], pool_mmx_plate.rows()[0][1]]

    ctx.comment('\n\nMOVING MASTERMIX TO PLATE\n')
    for col in sample_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        m20.aspirate(2, mmx)
        m20.dispense(2, col)
        m20.mix(3, 7, col)
        m20.blow_out()
        m20.touch_tip()
        m20.drop_tip()

    ctx.pause('''
    2ul of mastermix added to each sample. Incubate as described in Table 3 in
    section 8.1.4 of the protocol. Program NEB cDNA Synthesis on thermal
    cycler. After completed, return the sample plate to slot 1 of the deck and
    select "Resume" on the Opentrons app for Target enrichment.
    ''')

    ctx.comment('\n\nADDING POOL REAGENT TO SPLIT COLUMNS\n')
    for start_col in range(2):
        m20.pick_up_tip()
        for col in final_plate.rows()[0][start_col:num_col*2:2]:
            m20.aspirate(8, pool_reagents[start_col])
            m20.dispense(8, col)
            m20.blow_out()
            m20.touch_tip()
        m20.drop_tip()

    ctx.comment('\n\nSPLITTING 4.5ul OF SAMPLE FOR POOLING\n')
    split_ctr = 0
    for col in sample_plate.rows()[0][:num_col]:
        m20.pick_up_tip()
        for _ in range(2):
            m20.aspirate(4.5, col)
            m20.dispense(4.5, final_plate.rows()[0][split_ctr])
            m20.blow_out()
            m20.touch_tip()
            split_ctr += 1
        m20.drop_tip()

    ctx.pause('''
    4.5ul of samples are split into the final plate on slot 4.
    Incubate as described in Table 5 in section 8.2.3 of the protocol.
    Program NEB Targeted Synthesis on thermal cycler.
    After completed, return the plate to slot 4 of the deck and
    select "Resume" on the Opentrons app. Split columns will be combined to
    the left.
    ''')

    ctx.comment('\n\nRECOMBINING SPLIT COLUMNS TO THE LEFT\n')
    left_split_ctr = 0
    for col in final_plate.rows()[0][1:num_col*2:2]:
        m20.pick_up_tip()
        m20.aspirate(12.5, col)
        m20.dispense(12.5, final_plate.rows()[0][left_split_ctr])
        m20.mix(10, 20, final_plate.rows()[0][left_split_ctr])
        m20.blow_out()
        m20.touch_tip()
        m20.drop_tip()
        left_split_ctr += 2

    ctx.pause('''
    Protocol complete. Target Enrichment Quantification and Normalization to be
    done off deck. Part 2 on the OT-2 begins at section 8.4: Library Prep.
    ''')
