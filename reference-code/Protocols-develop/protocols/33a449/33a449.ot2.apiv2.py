from opentrons.types import Point
from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'NucleoMag Blood for DNA purification from blood',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx: protocol_api.ProtocolContext):

    [
     _num_col,
     _filter_tips,
     _mbl5_vol,
     _mag_height,
     _m300_mount
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "_num_col",
        "_filter_tips",
        "_mbl5_vol",
        "_mag_height",
        "_m300_mount")

    # VARIABLES
    num_col = _num_col
    filter_tips = _filter_tips
    m300_mount = _m300_mount
    mag_height = _mag_height
    mbl5_vol = int(_mbl5_vol)

    # load module
    mag_mod = ctx.load_module('magnetic module gen2', '1')

    # load labware
    mag_plate = mag_mod.load_labware('96_squarewell_block_macherey_nagel')
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '3')
    res2 = ctx.load_labware('nest_12_reservoir_15ml', '6')
    waste_res = ctx.load_labware('nest_12_reservoir_15ml', '9')
    elute_plate = ctx.load_labware('abgene_96_wellplate_700ul', '2')

    # load tip_racks
    tipracks = [ctx.load_labware('opentrons_96_filtertiprack_200ul'
                                 if filter_tips
                                 else 'opentrons_96_tiprack_300ul',
                                 slot) for slot in ['4', '5', '7',
                                                    '8', '10', '11']]

    # load instrument
    m300 = ctx.load_instrument('p300_multi_gen2',
                               m300_mount, tip_racks=tipracks)

    def pick_up():
        try:
            m300.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace all tip racks on Slots 7, 8, 10, and 11")
            m300.reset_tipracks()
            m300.pick_up_tip()

    waste_vol_ctr = 0
    waste_well_ctr = 0

    def remove_supernatant():
        nonlocal waste_vol_ctr
        nonlocal waste_well_ctr

        ctx.comment('\n\n\nREMOVING SUPERNATANT\n')
        for i, col in enumerate(sample_cols):
            side = -1 if i % 2 == 0 else 1
            aspirate_loc = col.bottom(1).move(
                    Point(x=(col.length/2-2)*side))
            pick_up()
            for _ in range(2):
                m300.aspirate(200 if filter_tips else 300, aspirate_loc, rate=0.6)  # noqa E501
                m300.dispense(200 if filter_tips else 300, waste_res.wells()[waste_well_ctr].top())    # noqa E501
                m300.blow_out(waste_res.wells()[waste_well_ctr].top())
                waste_vol_ctr += 200
                if waste_vol_ctr >= 12000:
                    waste_vol_ctr = 0
                    waste_well_ctr += 1
            m300.drop_tip()

    # map liquids
    num_samp = num_col*8
    bead_buffer_wells = math.ceil(num_samp*162.5/10000)
    mbl3_wells = math.ceil(num_samp*800/10000)
    eth_wells = math.ceil(num_samp*400/10000)

    prok = res1.wells()[0]
    bead_buffer = res1.wells()[1:1+bead_buffer_wells]*num_col
    mbl3 = res1.wells()[4:4+mbl3_wells]*num_col
    ethanol = res2.wells()[:eth_wells]*num_col
    mbl5 = res2.wells()[-1]
    sample_cols = mag_plate.rows()[0][:num_col]

    ctx.comment('\n\n\nDISPENSING PRO-K\n')
    for col in sample_cols:
        pick_up()
        m300.aspirate(50, prok)
        m300.dispense(50, col)
        m300.mix(10, 90, col, rate=1.5)
        m300.drop_tip()

    ctx.comment('\n\n\nDISPENSING BEAD BUFFER\n')
    airgap = 20
    for reagent_col, col in zip(bead_buffer, sample_cols):
        pick_up()
        m300.mix(5, 200 if filter_tips else 300, reagent_col, rate=2.0)
        m300.aspirate(162.5, reagent_col)
        m300.air_gap(airgap)
        m300.dispense(162.5+airgap, col)
        m300.mix(10, 150, col, rate=1.5)
        m300.air_gap(airgap)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=6)
    remove_supernatant()
    mag_mod.disengage()

    ctx.comment('\n\n\nDISPENSING MBL3\n')
    for reagent_col, col in zip(mbl3, sample_cols):
        pick_up()
        m300.aspirate(200, reagent_col)
        m300.dispense(200, col.top())
        m300.aspirate(200, reagent_col)
        m300.dispense(200, col)
        m300.mix(10, 200 if filter_tips else 300, col, rate=1.5)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=6)
    remove_supernatant()
    mag_mod.disengage()

    ctx.comment('\n\n\nDISPENSING ETHANOL\n')
    for reagent_col, col in zip(ethanol, sample_cols):
        pick_up()
        m300.aspirate(200, reagent_col)
        m300.dispense(200, col.top())
        m300.aspirate(200, reagent_col)
        m300.dispense(200, col)
        m300.mix(10, 200 if filter_tips else 300, col, rate=1.5)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=6)
    remove_supernatant()
    ctx.delay(minutes=20)
    mag_mod.disengage()

    ctx.comment('\n\n\nDISPENSING MBL5\n')
    for col in sample_cols:
        pick_up()
        m300.aspirate(mbl5_vol, mbl5)
        m300.dispense(mbl5_vol, col)
        m300.mix(5, 0.6*mbl5_vol, col)
        m300.drop_tip()

    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=6)

    for i, (sample_col, elute_col) in enumerate(
                                    zip(sample_cols, elute_plate.rows()[0])):
        side = -1 if i % 2 == 0 else 1
        aspirate_loc = sample_col.bottom(1).move(
                Point(x=(sample_col.length/2-2)*side))
        pick_up()
        m300.aspirate(mbl5_vol, aspirate_loc, rate=0.6)
        m300.dispense(mbl5_vol, elute_col)
        m300.drop_tip()
