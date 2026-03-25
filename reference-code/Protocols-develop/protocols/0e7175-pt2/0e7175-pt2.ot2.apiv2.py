metadata = {
    'protocolName': 'Luminex Assay Bead and Antibody Transfer',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    [sample_volume, use_middle_2, antibody_vol, sape_vol,
        p300_mount] = get_values(  # noqa: F821
         "sample_volume", "use_middle_2", "antibody_vol", "sape_vol",
         "p300_mount")

    # labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', 3)
    plates = [ctx.load_labware('greiner_96_wellplate_200ul', slot)
              for slot in [1, 2]]
    if use_middle_2:
        source_isopaks = [ctx.load_labware('custom_24_wellplate_2000ul', slot)
                          for slot in [4, 5, 7, 8]]
    else:
        source_isopaks = [ctx.load_labware('custom_24_wellplate_2000ul', slot)
                          for slot in [4, 5, 6, 7, 8, 9]]
    if use_middle_2:
        tips = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                for slot in [9, 10, 11]]
    else:
        tips = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                for slot in [10, 11]]

    # pipettes
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount, tip_racks=tips)

    # mapping
    beads = reservoir.wells()[0]
    antibodies = reservoir.wells()[1]
    sape = reservoir.wells()[2]

    plate_wells = [col for plate in plates for col in plate.rows()[0]]
    full_tips = [col for col in tips[0].rows()[0]]
    alternate_tips = [col for rack in tips[1:] for col in rack.rows()[0]]
    full_tip_count = 0
    alternate_tip_count = 0

    def pick_up_full():
        nonlocal full_tip_count
        p300.pick_up_tip(full_tips[full_tip_count])
        full_tip_count += 1

    def pick_up_alternate():
        nonlocal alternate_tip_count
        p300.pick_up_tip(alternate_tips[alternate_tip_count])
        alternate_tip_count += 1

    # protocol
    ctx.comment('\n---------------Transferring Beads----------------\n\n')

    pick_up_full()
    p300.aspirate(p300.max_volume, beads)
    vol_ctr = p300.max_volume
    for col in plate_wells:
        p300.dispense(50, col)
        vol_ctr -= 50
        if vol_ctr < 50 + sample_volume*0.1:
            p300.dispense(p300.current_volume, beads)
            p300.aspirate(p300.max_volume, beads)
            vol_ctr = p300.max_volume
    p300.dispense(p300.current_volume, beads)
    p300.drop_tip()
    ctx.comment('\n')
    ctx.pause('Incubate sample then select "Resume" on the Opentrons App.')

    ctx.comment('\n---------------Transferring Sample----------------\n\n')

    if use_middle_2:

        plate1_source_isopaks = source_isopaks[:2]
        plate2_source_isopaks = source_isopaks[2:]

        for j, pak in enumerate(plate1_source_isopaks):
            for i, s_col in zip(range(0, 12, 2), pak.rows()[0]):
                pick_up_alternate()
                p300.aspirate(200, s_col)
                p300.dispense(100, plates[0].rows()[j][i].top(z=-3))
                p300.touch_tip()
                p300.dispense(100, plates[0].rows()[j][i+1].top(z=-3))
                p300.blow_out()
                p300.touch_tip()
                p300.drop_tip()
            ctx.comment('\n')

        for j, pak in enumerate(plate2_source_isopaks):
            for i, s_col in zip(range(0, 12, 2), pak.rows()[0]):
                pick_up_alternate()
                p300.aspirate(200, s_col)
                p300.dispense(100, plates[1].rows()[j][i])
                p300.touch_tip()
                p300.dispense(100, plates[1].rows()[j][i+1])
                p300.blow_out()
                p300.touch_tip()
                p300.drop_tip()
            ctx.comment('\n')

    else:

        plate1_source_isopaks = source_isopaks[:3]
        plate2_source_isopaks = source_isopaks[3:]
        source_cols_first_3 = []
        source_cols_last_3 = []
        dest_cols_first_3 = [col for i in range(2)
                             for col in plates[0].rows()[i]]
        dest_cols_last_3 = [col for i in range(2)
                            for col in plates[1].rows()[i]]

        for set_pack, source_col_set in zip([plate1_source_isopaks,
                                             plate2_source_isopaks],
                                            [source_cols_first_3,
                                            source_cols_last_3]):
            for i, pak in enumerate(set_pack):
                for col in pak.rows()[0][:2]:
                    source_col_set.append(col)
                for col in pak.rows()[0][4:]:
                    source_col_set.append(col)

        for iteration, source_col_set, dest_col_set in zip(
                                                [0, 1],
                                                [source_cols_first_3,
                                                 source_cols_last_3],
                                                [dest_cols_first_3,
                                                 dest_cols_last_3]):
            for i, duplicate in enumerate(range(0, 24, 2)):
                pick_up_alternate()
                p300.aspirate(200, source_col_set[i])
                p300.dispense(100, dest_col_set[duplicate].top(z=-3))
                p300.touch_tip()
                p300.dispense(100, dest_col_set[duplicate+1].top(z=-3))
                p300.blow_out()
                p300.touch_tip()
                p300.drop_tip()
            ctx.comment('\n')
            if iteration == 0:
                ctx.pause("""Replace alternate tip rack on slot 11,
                            then select "Resume" on the Opentrons App.""")
            alternate_tip_count = 0

    ctx.pause('Incubate sample then select "Resume" on the Opentrons App.')

    ctx.comment('\n---------------Transferring Antibodies----------------\n\n')

    pick_up_full()
    for col in plate_wells:
        p300.aspirate(antibody_vol, antibodies)
        p300.dispense(antibody_vol, col.top())
        p300.blow_out()
    p300.drop_tip()
    ctx.comment('\n')
    ctx.pause('Incubate sample then select "Resume" on the Opentrons App.')

    ctx.comment('\n---------------Transferring SA-PE----------------\n\n')
    pick_up_full()
    for col in plate_wells:
        p300.aspirate(sape_vol, sape)
        p300.dispense(sape_vol, col.top())
        p300.blow_out()
    p300.drop_tip()
    ctx.comment('\n')
