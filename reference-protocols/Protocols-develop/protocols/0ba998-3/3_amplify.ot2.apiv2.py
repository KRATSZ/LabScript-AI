from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': '3. Illumina DNA Prep - Amplify Tagmented DNA',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_TEMP = False
TEST_MODE_DROP = False
TEST_MODE_MIX = False
TEST_MODE_BEADS = False
TEST_MODE_BIND_INCUBATE = False


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        "num_samples")

    # tuning parameters
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200
    reps_mix = 0 if TEST_MODE_MIX else 10
    vol_mix = 30
    z_offset = 3.0
    radial_offset_fraction = 0.3  # fraction of radius

    # modules
    tempdeck = ctx.load_module('temperature module gen2', '7')
    magdeck = ctx.load_module('magnetic module gen2', '4')
    if not TEST_MODE_TEMP:
        tempdeck.set_temperature(4)
    magdeck.disengage()

    # labware
    mag_plate = magdeck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'PCR plate')
    reagent_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', 'reagent plate')
    index_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                   '1', 'index plate')
    waste_res = ctx.load_labware('nest_1_reservoir_195ml', '5', 'waste')
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
    num_cols = math.ceil(num_samples/8)
    mag_samples = mag_plate.rows()[0][:num_cols]
    indexes = index_plate.rows()[0][:num_cols]
    mm_pcr = reagent_plate.rows()[0][3:6]
    liquid_trash = [
        waste_res.wells()[0].top()
        for _ in range(math.ceil(num_cols/6))]

    vol_supernatant = 100.0
    vol_mm_pcr = 40.0
    vol_index = 10.0

    ref_well = mag_plate.wells()[0]
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

    parked_tips = []

    def remove_supernatant(vol, pip=None, z_asp=0.2, park=True,
                           destinations=liquid_trash):
        nonlocal parked_tips
        if not pip:
            pip = m300 if vol >= 20 else m20
        pip.flow_rate.aspirate /= 20
        for i, s in enumerate(mag_samples):
            if not pip.has_tip:
                if park:
                    pick_up(pip, parked_tips[i])
                else:
                    pick_up(pip)
            pip.move_to(s.top())
            ctx.max_speeds['A'] = 25
            ctx.max_speeds['Z'] = 25
            side = -1 if mag_samples.index(s) % 2 == 0 else 1
            pip.aspirate(vol, s.bottom().move(Point(x=side, z=z_asp)))
            pip.move_to(s.top())
            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']
            pip.dispense(vol, liquid_trash[i//6])
            pip.blow_out(liquid_trash[i//6])
            pip.air_gap(10)
            if TEST_MODE_DROP:
                pip.return_tip()
            else:
                pip.drop_tip()
        parked_tips = []
        pip.flow_rate.aspirate *= 20

    def resuspend(location, reps=reps_mix, vol=vol_mix,
                  samples=mag_samples, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=5.0):
        side_x = 1 if samples.index(location) % 2 == 0 else -1
        m300.move_to(location.center())
        for r_ind in range(reps):
            bead_loc = location.bottom().move(
                Point(x=side_x*radius*radial_offset_fraction,
                      z=z_mix))
            m300.aspirate(vol, bead_loc)
            m300.dispense(vol, bead_loc.move(Point(z=dispense_height_rel)))
        slow_withdraw(m300, location)

    magdeck.engage()
    ctx.delay(minutes=3, msg='Incubating on MagDeck for 3 minutes.')

    # remove supernatant
    remove_supernatant(vol_supernatant, pip=m300, park=False)
    magdeck.disengage()

    # transfer PCR mastermix
    for i, d in enumerate(mag_samples):
        mm_source = mm_pcr[i//4]
        pick_up(m300)
        m300.aspirate(vol_mm_pcr, mm_source.bottom(0.5))
        slow_withdraw(m300, mm_source)
        side = 1 if mag_plate.rows()[0].index(d) % 2 == 0 else -1
        loc_dispense = d.bottom().move(
            Point(x=side*radial_offset_fraction, z=z_offset))
        m300.dispense(vol_mm_pcr, loc_dispense)
        m300.flow_rate.aspirate *= 1.5
        m300.flow_rate.dispense *= 1.5
        m300.mix(vol_mix, reps_mix, d.bottom(0.5))
        m300.flow_rate.aspirate /= 1.5
        m300.flow_rate.dispense /= 1.5
        m300.blow_out(d.bottom(0.5))
        ctx.delay(seconds=2)
        slow_withdraw(m300, d)
        if TEST_MODE_DROP:
            m300.return_tip()
        else:
            m300.drop_tip()

    ctx.pause('Seal the sample plate and centrifuge at 280 × g for 3 seconds')

    # transfer indexes
    for ind, d in zip(indexes, mag_samples):
        pick_up(m20)
        m20.aspirate(vol_index, ind.bottom(0.5))
        slow_withdraw(m20, ind)
        m20.dispense(vol_index, d.bottom(2))
        m20.mix(reps_mix, 20, d.bottom(2))
        ctx.delay(seconds=2)
        slow_withdraw(m20, d)
        if TEST_MODE_DROP:
            m20.return_tip()
        else:
            m20.drop_tip()

    ctx.comment('Seal the plate with Microseal B, and then centrifuge at \
280 × g for 30 seconds. 11 Place on the thermal cycler and run the BLT PCR \
program.')
