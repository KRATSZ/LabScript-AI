metadata = {
    'protocolName': 'DMSO and Compound Stock Solution Addition - Part 1',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [dmso_dil_factor, pre_dilution,
        pre_dil_factor, m20_mount] = get_values(  # noqa: F821
        "dmso_dil_factor", "pre_dilution",
            "pre_dil_factor", "m20_mount")
    #
    # dmso_dil_factor = 1.5
    # m20_mount = 'right'
    # pre_dilution = False
    # pre_dil_factor = 2

    # labware
    dmso = ctx.load_labware('nest_12_reservoir_15ml', 1).wells()[0]

    plates = [ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
              slot, 'plate')
              for slot in [2, 4, 5, 10, 11]]

    plates = plates
    deep_plates = [ctx.load_labware('nest_96_wellplate_2ml_deep',
                   slot, 'plate')
                   for slot in [6, 7, 8, 9]]
    deep_plates = deep_plates
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in [3]]

    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips)

    # mapping
    compound_plate = plates[0]
    dmso_plate_11 = ctx.loaded_labwares[4]
    dmso_plate_12 = ctx.loaded_labwares[5]
    dmso_plate_21 = ctx.loaded_labwares[10]
    dmso_plate_22 = ctx.loaded_labwares[11]
    media_plate_11 = ctx.loaded_labwares[9]
    media_plate_12 = ctx.loaded_labwares[6]
    media_plate_21 = ctx.loaded_labwares[7]
    media_plate_22 = ctx.loaded_labwares[8]

    # protocol
    dmso_vol = -13.3*(1-dmso_dil_factor)

    # transfer dmso to most cols dilution plates dmso 1-1, 1-2
    m20.pick_up_tip()

    for plate in [dmso_plate_11, dmso_plate_21]:
        for col in plate.rows()[0][1:]:
            m20.aspirate(dmso_vol, dmso)
            m20.dispense(dmso_vol, col)
        ctx.comment('\n')

    # transfer dmso to all cols dilution plates dmso 1-2, 2-2
    for plate in [dmso_plate_12, dmso_plate_22]:
        for col in plate.rows()[0]:
            m20.aspirate(dmso_vol, dmso)
            m20.dispense(dmso_vol, col)
        ctx.comment('\n')

    if pre_dilution:
        dmso_pre_dil_vol = 20-20/pre_dil_factor
        compound_source_A = compound_plate.rows()[0][10]
        compound_source_B = compound_plate.rows()[0][11]
        m20.aspirate(dmso_pre_dil_vol, dmso)
        m20.dispense(dmso_pre_dil_vol, compound_source_A)
        m20.aspirate(dmso_pre_dil_vol, dmso)
        m20.dispense(dmso_pre_dil_vol, compound_source_B)
        m20.drop_tip()
        ctx.comment('\n')

        m20.pick_up_tip()
        m20.aspirate(20-dmso_pre_dil_vol, compound_plate.rows()[0][0])
        m20.dispense(20-dmso_pre_dil_vol, compound_source_A)
        m20.mix(10, 18, compound_source_A)
        m20.drop_tip()
        ctx.comment('\n')

        m20.pick_up_tip()
        m20.aspirate(20-dmso_pre_dil_vol, compound_plate.rows()[0][1])
        m20.dispense(20-dmso_pre_dil_vol, compound_source_B)
        m20.mix(10, 18, compound_source_B)
        m20.drop_tip()
        ctx.comment('\n')

    else:
        m20.drop_tip()
        compound_source_A = compound_plate.rows()[0][0]
        compound_source_B = compound_plate.rows()[0][1]

    # transfer compound to plate
    ctx.comment('\nTransferring Compound \n')
    for compound, first_plate, second_plate in zip(
                            [compound_source_A, compound_source_B],
                            [dmso_plate_11, dmso_plate_21],
                            [dmso_plate_12, dmso_plate_22]):
        m20.pick_up_tip()
        m20.aspirate(20, compound)
        m20.dispense(20, first_plate.wells()[0])
        for i, col in enumerate(first_plate.rows()[0][:10]):
            m20.aspirate(13.3, first_plate.rows()[0][i])
            m20.dispense(13.3, first_plate.rows()[0][i+1])
            m20.mix(6, 0.9*(dmso_vol+13.3), first_plate.rows()[0][i+1])
        ctx.comment('\n\n')

        m20.aspirate(13.3, first_plate.rows()[0][10])
        m20.dispense(13.3, second_plate.rows()[0][0])
        m20.mix(6, 0.9*(dmso_vol+13.3), second_plate.rows()[0][0])

        for i, col in enumerate(second_plate.rows()[0][:10]):
            m20.aspirate(13.3, second_plate.rows()[0][i])
            m20.dispense(13.3, second_plate.rows()[0][i+1])
            m20.mix(6, 0.9*(dmso_vol+13.3), second_plate.rows()[0][i+1])
        m20.drop_tip()
        ctx.comment('\n\n\n\n\n\n\n\n')

    ctx.pause("Replace Tip Rack")
    m20.reset_tipracks()
    for source_plate, dest_plate in zip(

                                        [dmso_plate_11, dmso_plate_12,
                                         dmso_plate_21, dmso_plate_22],
                                        [media_plate_11, media_plate_12,
                                         media_plate_21, media_plate_22]):

        for source, dest in zip(source_plate.rows()[0], dest_plate.rows()[0]):
            m20.pick_up_tip()
            m20.aspirate(2.4, source)
            m20.dispense(2.4, dest)
            m20.drop_tip()

        ctx.pause("Replace Tip Rack")
        m20.reset_tipracks()

        ctx.comment('\n\n')
