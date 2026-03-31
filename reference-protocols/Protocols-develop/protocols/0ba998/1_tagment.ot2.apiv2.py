from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': '1. Illumina DNA Prep - Tagment Genomic DNA',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_TEMP = False
TEST_MODE_DROP = False
TEST_MODE_MIX = False


def run(ctx):

    num_samples, vol_dna = get_values(  # noqa: F821
        "num_samples", "vol_dna")

    # tuning parameters
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200
    reps_mix = 0 if TEST_MODE_MIX else 10

    # modules
    tempdeck = ctx.load_module('temperature module gen2', '7')
    magdeck = ctx.load_module('magnetic module gen2', '4')
    if not TEST_MODE_TEMP:
        tempdeck.set_temperature(4)
    magdeck.disengage()

    # labware
    pcr_plate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                     'PCR plate')
    dna_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                 '1', 'source DNA plate')
    reagent_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', 'reagent plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2', 'reservoir')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3', '6']]
    tips200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['8', '9', '10', '11']]

    # load P300M pipette
    m20 = ctx.load_instrument(
        'p20_multi_gen2', 'right', tip_racks=tips20)
    m300 = ctx.load_instrument(
         'p300_multi_gen2', 'left', tip_racks=tips200)

    # reagents and variables
    mm = reagent_plate.rows()[0][:2]
    water = reservoir.rows()[0][0]

    vol_water = 30 - vol_dna
    vol_mm = 20.0
    num_cols = math.ceil(num_samples/8)
    ref_well = pcr_plate.wells()[0]
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

    # transfer water and sample
    if vol_water > 0:
        pip = m20 if vol_water <= 20 else m300
        pick_up(pip)
        for d in pcr_plate.rows()[0][:num_cols]:
            pip.aspirate(vol_water, water)
            slow_withdraw(pip, water)
            pip.dispense(vol_water, d.bottom(0.5))
            # pip.blow_out(d.bottom(2))
            slow_withdraw(pip, d)

    pip = m20 if vol_dna <= 20 else m300
    for s, d in zip(dna_plate.rows()[0][:num_cols],
                    pcr_plate.rows()[0][:num_cols]):
        if not pip.has_tip:
            pick_up(pip)
        pip.aspirate(vol_dna, s.bottom(0.5))
        slow_withdraw(pip, s)
        pip.dispense(vol_dna, d.bottom(0.5))
        ctx.delay(seconds=2)
        # pip.blow_out(d.bottom(2))
        ctx.delay(seconds=2)
        slow_withdraw(pip, d)
        if TEST_MODE_DROP:
            pip.return_tip()
        else:
            pip.drop_tip()

    for pip in [m20, m300]:
        if pip.has_tip:
            if not TEST_MODE_DROP:
                pip.drop_tip()
            else:
                pip.return_tip()

    # transfer tagmentation mastermix
    m300.flow_rate.aspirate /= 2
    m300.flow_rate.dispense /= 2
    last_source = None
    for i, d in enumerate(pcr_plate.rows()[0][:num_cols]):
        mm_source = mm[i//6]
        pick_up(m300)
        if not mm_source == last_source:
            m300.mix(10, vol_mm, mm_source)
            last_source = mm_source
        m300.aspirate(vol_mm, mm_source.bottom(0.5))
        slow_withdraw(m300, mm_source)
        m300.dispense(vol_mm, d.bottom(0.5))
        ctx.delay(seconds=2)
        m300.mix(reps_mix, 30, d.bottom(2))
        m300.blow_out(d.bottom(2))
        ctx.delay(seconds=2)
        slow_withdraw(m300, d)
        if TEST_MODE_DROP:
            m300.return_tip()
        else:
            m300.drop_tip()
    m300.flow_rate.aspirate *= 2
    m300.flow_rate.dispense *= 2

    ctx.comment('Seal the plate with Microseal B, place on the \
preprogrammed thermal cycler, and run the TAG program.')
