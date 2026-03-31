metadata = {
    'protocolName': 'Mastermix Filling 9 Plates',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [starting_tip_col, reag, source_labware, num_rounds,
        p20_mount, p300_mount] = get_values(  # noqa: F821
        "starting_tip_col", "reag", "source_labware", "num_rounds",
            "p20_mount", "p300_mount")

    # start of protocol
    reag_dict = {

        "synth1_columns": [0, 2],
        "synth1_vol": 14,
        "synth1_num_disp": 1,

        "screen10_columns": [2, 4],
        "screen10_vol": 10,
        "screen10_num_disp": 1,

        "seq5_columns": [4, 6],
        "seq5_vol": 8,
        "seq5_num_disp": 2,

        "lba_columns": [6, 8],
        "lba_vol": 30,
        "lba_num_disp": 6,

        "lbk_columns": [8, 10],
        "lbk_vol": 30,
        "lbk_num_disp": 6,

        "pcr_columns": [10, 12],
        "pcr_vol": 20,
        "pcr_num_disp": 9

    }

    reag_cols = reag_dict[reag + "_columns"]
    reag_vol = reag_dict[reag + "_vol"]
    reag_num_disp = reag_dict[reag + "_num_disp"]

    # labware
    source_plate = ctx.load_labware(source_labware, 11)
    dest_plates = [ctx.load_labware('doublepcr_96_wellplate_300ul', slot)
                   for slot in [7, 8, 9, 4, 5, 6, 1, 2, 3]]
    tips = [ctx.load_labware(
            'opentrons_96_tiprack_20ul' if reag_vol < 20 else
            'opentrons_96_filtertiprack_200ul', slot)
            for slot in [10]]

    starting_tip = tips[0].rows()[0][starting_tip_col-1]

    ctx.pause(f"""
    Ensure that there is a {tips[0]}.
    Select "Resume" on the Opentrons app.
        """)

    # pipettes
    pip = ctx.load_instrument('p20_multi_gen2' if reag_vol < 20 else
                              'p300_multi_gen2',
                              "right" if reag_vol < 20 else "left",
                              tip_racks=tips)

    all_dest_columns = [
                        col
                        for plate in dest_plates
                        for col in plate.rows()[0]
                        ]

    # source mapping
    reag_start_col = reag_cols[0]
    reag_end_col = reag_cols[1]

    source_cols = source_plate.rows()[0][
                                         reag_start_col:reag_end_col
                                         ]*1000

    src_col_ctr = 0
    disp_vol = 1 if reag_vol < 20 else 20

    for _ in range(num_rounds):
        if reag_num_disp > 1:
            all_chunks = [all_dest_columns[i:i+reag_num_disp]
                          for i in range(0, len(all_dest_columns),
                                         reag_num_disp)]

            if not pip.has_tip:
                pip.pick_up_tip(starting_tip)

            for chunk in all_chunks:
                source = source_cols[src_col_ctr]
                pip.aspirate(reag_vol*len(chunk)+disp_vol, source)
                src_col_ctr += 1
                for well in chunk:
                    pip.dispense(reag_vol, well.bottom(z=1))
                pip.dispense(disp_vol, source)
                ctx.comment('\n')
        else:
            if not pip.has_tip:
                pip.pick_up_tip(starting_tip)
            for source, dest in zip(source_cols, all_dest_columns):
                pip.aspirate(reag_vol, source)
                pip.dispense(reag_vol, dest.bottom(z=1))
                ctx.comment('\n')
        ctx.pause("Select Resume for another round")
