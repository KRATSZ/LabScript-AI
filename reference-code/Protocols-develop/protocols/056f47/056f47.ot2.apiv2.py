metadata = {
    'protocolName': 'DMSO and Compound Stock Solution Addition - Part 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [n, m20_mount, m300_mount] = get_values(  # noqa: F821
        "n", "m20_mount", "m300_mount")

    # labware
    dmso = ctx.load_labware('nest_12_reservoir_15ml', 1).wells()[0]

    plates = [ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt' if n < 15 else "nest_96_wellplate_2ml_deep",   # noqa: E501
                               slot, 'plate')
              for slot in [4, 5]]

    plates = plates

    compound_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt' if n < 15 else "nest_96_wellplate_2ml_deep",  # noqa: E501
                                      2,
                                      'plate')
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in [3]]

    tips200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in [6]]

    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tips200)

    # mapping
    dmso_plate_1 = ctx.loaded_labwares[4]
    dmso_plate_2 = ctx.loaded_labwares[5]

    # protocol

    # transfer dmso to most cols dilution plates dmso 1-1, 1-2
    dmso_vol = n*2.4

    pip = m300 if dmso_vol > 20 else m20
    pip.pick_up_tip()

    for col in dmso_plate_1.rows()[0][1:]:
        pip.aspirate(dmso_vol, dmso)
        pip.dispense(dmso_vol, col)
    ctx.comment('\n')

    # transfer dmso to all cols dilution plates dmso 1-2, 2-2
    for col in dmso_plate_2.rows()[0]:
        pip.aspirate(dmso_vol, dmso)
        pip.dispense(dmso_vol, col)
    ctx.comment('\n')

    pip.drop_tip()

    compound = compound_plate.rows()[0][0]

    # transfer compound to plate
    ctx.comment('\nTransferring Compound \n')

    compound_vol = n*7.2
    pip = m300 if compound_vol > 20 else pip

    pip.pick_up_tip()
    pip.transfer(compound_vol, compound,
                 dmso_plate_1.wells()[0], new_tip='never')

    pip.drop_tip()

    dilution_vol = n*4.8
    pip = m300 if dilution_vol > 20 else pip
    pip.pick_up_tip()

    for i, col in enumerate(dmso_plate_1.rows()[0][:10]):
        pip.transfer(dilution_vol, dmso_plate_1.rows()[0][i],
                     dmso_plate_1.rows()[0][i+1], new_tip='never')
        pip.mix(6,
                0.9*(dmso_vol+dilution_vol) if dmso_vol+dilution_vol < 200 else 200,  # noqa: E501
                dmso_plate_1.rows()[0][i+1])
    ctx.comment('\n\n')

    pip.transfer(dilution_vol, dmso_plate_1.rows()[0][10],
                 dmso_plate_2.rows()[0][0], new_tip='never')
    pip.mix(6, 0.9*(dmso_vol+dilution_vol) if dmso_vol+dilution_vol < 200 else 200,  # noqa: E501
            dmso_plate_2.rows()[0][0])

    for i, col in enumerate(dmso_plate_2.rows()[0][:10]):
        pip.transfer(dilution_vol, dmso_plate_2.rows()[0][i],
                     dmso_plate_2.rows()[0][i+1], new_tip='never')
        pip.mix(6, 0.9*(dmso_vol+dilution_vol) if dmso_vol+dilution_vol < 200 else 200,  # noqa: E501
                dmso_plate_2.rows()[0][i+1])
    pip.drop_tip()
    ctx.comment('\n\n\n\n\n\n\n\n')
