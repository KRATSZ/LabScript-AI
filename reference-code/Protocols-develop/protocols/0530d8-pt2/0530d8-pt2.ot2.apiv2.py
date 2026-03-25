import math
from opentrons import protocol_api, types

metadata = {
    'protocolName': 'DNA Extraction with Heater Shaker - Part 2',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samp, asp_height, p300_mount, m300_mount] = get_values(  # noqa: F821
        "num_samp", "asp_height", "p300_mount", "m300_mount")

    num_col = math.ceil(num_samp/8)
    engage_height = -1

    # labware
    final_plate = ctx.load_labware('abgene_96_wellplate_2000ul', 1)

    reag_plate = ctx.load_labware('abgene_96_wellplate_2000ul', 8)
    mag_mod = ctx.load_module('magnetic module gen2', 4)
    mag_plate = mag_mod.load_labware('abgene_96_wellplate_2000ul')
    heater_shaker = ctx.load_module('heaterShakerModuleV1', 10)
    hs_plate = heater_shaker.load_labware('abgene_96_wellplate_2000ul')
    heater_shaker.close_labware_latch()

    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in [2, 3, 5, 6, 7, 9]]

    # pipettes
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=tips)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount, tip_racks=tips)

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            pip.home()
            ctx.pause("Please replace the tips and click Resume.")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def remove_supernatant(vol, i, col):
        side = -1 if i % 2 == 0 else 1
        m300.transfer(vol, col.bottom().move(types.Point(
                      x=side, y=0, z=1)),
                      ctx.loaded_labwares[12].wells()[0].top(),
                      rate=0.1, new_tip='never')
        ctx.delay(seconds=1)

    reagent4 = reag_plate.rows()[0][3:5]*12
    reagent5 = reag_plate.rows()[0][5:7]*12
    reagent6 = reag_plate.rows()[0][7:9]*12
    reagent7 = reag_plate.rows()[0][9]

    # mapping
    ctx.comment('\n---------TRANSFERRING SAMPLE TO MAG PLATE-----------\n\n')
    for source, dest in zip(hs_plate.wells(), mag_plate.wells()[:num_samp]):
        pick_up(p300)
        p300.aspirate(200, source.bottom(z=asp_height))
        p300.dispense(200, dest)
        p300.drop_tip()

    ctx.comment('\n---------TRANSFERRING CONTROLS TO MAG PLATE-----------\n\n')
    for source, dest in zip(hs_plate.columns()[11][2:],
                            mag_plate.columns()[11][2:]):
        pick_up(p300)
        p300.aspirate(200, source)
        p300.dispense(200, dest)
        p300.drop_tip()

    ctx.comment('\n---------------ADDING 240 REAGENT----------------\n\n')
    for col, reag_col in zip(hs_plate.rows()[0][:num_col], reagent4):
        pick_up(m300)
        for _ in range(2):
            m300.aspirate(120, reag_col)
            m300.dispense(120, col)
            m300.blow_out(col.top(z=-2))
        m300.mix(15, 200, col)
        m300.drop_tip()
        ctx.comment('\n')

    if num_samp <= 88:
        pick_up(m300)
        for _ in range(2):
            m300.aspirate(120, reagent4)
            m300.dispense(120, hs_plate.rows()[0][11])
            m300.blow_out(col.top(z=-2))
        m300.mix(15, 200, hs_plate.rows()[0][11])
        m300.drop_tip()
        ctx.comment('\n')

    ctx.delay(minutes=5)
    mag_mod.engage(height_from_base=engage_height)
    ctx.delay(minutes=5)

    ctx.comment('\n---------------REMOVING SUPERNATANT----------------\n\n')
    for i, col in enumerate(hs_plate.rows()[0][:num_col]):
        pick_up(m300)
        remove_supernatant(440, i, col)
        m300.drop_tip()
    if num_samp <= 88:
        pick_up(m300)
        remove_supernatant(440, 1, hs_plate.rows()[0][11])
        m300.drop_tip()

    ctx.comment('\n---------------TWO WASHES----------------\n\n')
    for reag_set in [reagent5, reagent6]:
        ctx.comment('\n---------------ADDING 200 REAGENT----------------\n\n')
        for col, reag_col in zip(hs_plate.rows()[0][:num_col], reag_set):
            pick_up(m300)
            m300.aspirate(200, reag_col)
            m300.dispense(200, col)
            m300.blow_out(col.top(z=-2))
            m300.mix(5, 200, col)
            m300.drop_tip()
            ctx.comment('\n')

        if num_samp <= 88:
            pick_up(m300)
            m300.aspirate(200, reag_col)
            m300.dispense(200, hs_plate.rows()[0][11])
            m300.blow_out(col.top(z=-2))
            m300.mix(5, 200, hs_plate.rows()[0][11])
            m300.drop_tip()
            ctx.comment('\n')

        ctx.delay(seconds=30)

        ctx.comment('\n--------------REMOVING SUPERNATANT---------------\n\n')
        for i, col in enumerate(hs_plate.rows()[0][:num_col]):
            pick_up(m300)
            remove_supernatant(200, i, col)
            m300.drop_tip()
        if num_samp <= 88:
            pick_up(m300)
            remove_supernatant(200, 1, hs_plate.rows()[0][11])
            m300.drop_tip()

    mag_mod.disengage()

    ctx.comment('\n---------------ADDING 30ul REAGENT----------------\n\n')
    for col in hs_plate.rows()[0][:num_col]:
        pick_up(m300)
        m300.aspirate(30, reagent7)
        m300.dispense(30, col)
        m300.blow_out(col.top(z=-2))
        m300.mix(10, 20, col)
        m300.drop_tip()
        ctx.comment('\n')

    if num_samp <= 88:
        pick_up(m300)
        m300.aspirate(30, reagent7)
        m300.dispense(30, hs_plate.rows()[0][11])
        m300.blow_out(col.top(z=-2))
        m300.mix(10, 20, hs_plate.rows()[0][11])
        m300.drop_tip()
        ctx.comment('\n')

    ctx.delay(minutes=5)
    mag_mod.engage(height_from_base=engage_height)
    ctx.delay(minutes=5)

    for i, (source, dest) in enumerate(zip(hs_plate.rows()[0][:num_col],
                                       final_plate.rows()[0])):
        side = -1 if i % 2 == 0 else 1

        pick_up(m300)
        m300.transfer(30, source.bottom().move(types.Point(
                      x=side, y=0, z=1)),
                      dest,
                      rate=0.1, new_tip='never')
        m300.blow_out(dest.top(z=-2))
        m300.drop_tip()

    if num_samp <= 88:
        pick_up(m300)
        m300.transfer(30, hs_plate.rows()[0][11].bottom().move(types.Point(
                      x=side, y=0, z=1)),
                      final_plate.rows()[0][11],
                      rate=0.1, new_tip='never')
        m300.blow_out(final_plate.rows()[0][11].top(z=-2))

        m300.drop_tip()
