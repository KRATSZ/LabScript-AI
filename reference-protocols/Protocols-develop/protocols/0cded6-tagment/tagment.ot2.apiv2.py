from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': '4. Illumina COVIDSeq - Tagment PCR Amplicons',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_TEMP = True
TEST_MODE_DROP = True

num_samples = 96


def run(ctx):

    # tuning parameters
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    # modules
    tempdeck = ctx.load_module('temperature module gen2', '4')
    magdeck = ctx.load_module('magnetic module gen2', '7')
    if not TEST_MODE_TEMP:
        tempdeck.set_temperature(4)
    magdeck.disengage()

    # labware
    tag1_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                  '2', 'TAG1 plate')
    reagent_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'reagent plate')
    cov1_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                  '1', 'COV1 plate')
    cov2_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr',
                                  '5', 'COV2 plate')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3']]
    tips200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['9']]

    # load P300M pipette
    m20 = ctx.load_instrument(
        'p20_multi_gen2', 'right', tip_racks=tips20)
    m300 = ctx.load_instrument(
         'p300_multi_gen2', 'left', tip_racks=tips200)

    # reagents and variables
    mm = reagent_plate.rows()[0][6:8]

    vol_mm = 30.0
    vol_amplicon = 10.0
    num_cols = math.ceil(num_samples/8)
    ref_well = tag1_plate.wells()[0]
    if ref_well.width:
        radius = ref_well.width/2
    else:
        radius = ref_well.diameter/2

    def wick(pip, well, side=1):
        pip.move_to(well.bottom().move(Point(x=side*radius*0.7, z=3)))

    def slow_withdraw(pip, well):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def pick_up(pip, spot=None):
        if spot:
            pip.pick_up_tip(spot)
        else:
            try:
                pip.pick_up_tip()
            except protocol_api.labware.OutOfTipsError:
                ctx.pause("\n\n\n\nReplace 200ul filtertipracks before \
resuming.\n\n\n\n")
                pip.reset_tipracks()
                pip.pick_up_tip()

    for i, cov_plate in enumerate([cov1_plate, cov2_plate]):
        for s, d in zip(cov_plate.rows()[0][:num_cols],
                        tag1_plate.rows()[0][:num_cols]):
            pick_up(m20)
            m20.aspirate(vol_amplicon, s.bottom(0.5))
            slow_withdraw(m20, s)
            m20.dispense(m20.current_volume, d.bottom(0.5))
            if i == 0:
                wick(m20, d)
            else:
                slow_withdraw(m20, d)
            if TEST_MODE_DROP:
                m20.return_tip()
            else:
                m20.drop_tip()

    for i, d in enumerate(tag1_plate.rows()[0][:num_cols]):
        mm_source = mm[i//6]
        pick_up(m300)
        m300.aspirate(vol_mm, mm_source.bottom(0.5))
        slow_withdraw(m300, mm_source)
        m300.dispense(vol_mm, d.bottom(2))
        slow_withdraw(m300, d)
        if TEST_MODE_DROP:
            m300.return_tip()
        else:
            m300.drop_tip()

    ctx.comment('\n\n\n\nSeal and shake at 1600 rpm for 1 minute. Place on \
the preprogrammed thermal cycler and run the COVIDSeq TAG program.\n\n\n\n')
