from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': '2. Illumina DNA Prep - Post Tagmentation Clean Up',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_BEADS = False
TEST_MODE_BIND_INCUBATE = False
TEST_MODE_TEMP = False
TEST_MODE_DROP = False


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        "num_samples")

    reps_mix = 1 if TEST_MODE_BEADS else 10
    time_settling_minutes = 3.0
    vol_mix = 70
    z_offset = 3.0
    radial_offset_fraction = 0.3  # fraction of radius

    # tuning parameters
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

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
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '2', 'reservoir')
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
    tsb = reagent_plate.rows()[0][2]
    twb = reservoir.rows()[0][1:1+(math.ceil(num_cols/6))]
    liquid_trash = [
        waste_res.wells()[0].top()
        for _ in range(math.ceil(num_cols/6))]

    vol_tsb = 10.0
    vol_wash = 100.0
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

    def remove_supernatant(vol, pip=None, z_asp=0.2, park=False):
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
                  z_mix=z_offset, dispense_height_rel=5.0, rate=1.0):
        side_x = 1 if samples.index(location) % 2 == 0 else -1
        m300.move_to(location.center())
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        for r_ind in range(reps):
            bead_loc = location.bottom().move(
                Point(x=side_x*radius*radial_offset_fraction,
                      z=z_mix))
            m300.aspirate(vol, bead_loc, rate=rate)
            m300.dispense(vol, bead_loc.move(Point(z=dispense_height_rel)),
                          rate=rate)
        slow_withdraw(m300, location)
        m300.flow_rate.aspirate /= 2
        m300.flow_rate.dispense /= 2

    def wash(vol, reagent, time_incubation=0,
             time_settling=0, premix=False,
             do_discard_supernatant=True, do_resuspend=False,
             vol_supernatant=0, park=False):
        nonlocal parked_tips

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        last_source = None

        if do_resuspend:
            magdeck.disengage()
        for i, well in enumerate(mag_samples):
            source = reagent[i//columns_per_channel]
            pick_up(m300)
            if park:
                parked_tips.append(m300._last_tip_picked_up_from)
            if premix and last_source != source:
                m300.flow_rate.aspirate *= 4
                m300.flow_rate.dispense *= 4
                for _ in range(5):
                    m300.aspirate(200, source.bottom(0.5))
                    m300.dispense(200, source.bottom(5))
                m300.flow_rate.aspirate /= 4
                m300.flow_rate.dispense /= 4
            last_source = source
            for n in range(num_transfers):
                m300.aspirate(vol_per_transfer, source)
                slow_withdraw(m300, source)
                if n < num_transfers - 1:
                    loc_dispense = well.top
                else:
                    side = 1 if mag_plate.rows()[
                        0].index(well) % 2 == 0 else -1
                    loc_dispense = well.bottom().move(
                        Point(x=side*radial_offset_fraction, z=z_offset))
                m300.dispense(vol_per_transfer, loc_dispense, rate=0.2)
            if do_resuspend:
                resuspend(well, rate=0.5)
            ctx.delay(seconds=2)
            slow_withdraw(m300, well)
            m300.air_gap(20)
            if park or TEST_MODE_DROP:
                m300.return_tip()
            else:
                m300.drop_tip()

        if not TEST_MODE_BIND_INCUBATE:
            ctx.delay(minutes=time_incubation,
                      msg=f'Incubating off MagDeck for \
{time_incubation} minutes.')
        if do_discard_supernatant:
            magdeck.engage()
            if not TEST_MODE_BEADS:
                ctx.delay(minutes=time_settling, msg=f'Incubating on \
MagDeck for {time_settling} minutes.')

            remove_supernatant(vol_supernatant)
            magdeck.disengage()

    for d in mag_samples:
        pick_up(m20)
        m20.flow_rate.aspirate /= 2
        m20.flow_rate.dispense /= 2
        m20.aspirate(vol_tsb, tsb.bottom(0.5))
        slow_withdraw(m20, tsb)
        m20.dispense(m20.current_volume, d.bottom(2))
        m20.flow_rate.aspirate *= 8  # double default
        m20.flow_rate.dispense *= 8  # double default
        m20.mix(reps_mix*2, 20, d.bottom(2))
        m20.flow_rate.aspirate /= 4  # back to default
        m20.flow_rate.dispense /= 4  # back to default
        slow_withdraw(m20, d)
        if TEST_MODE_DROP:
            m20.return_tip()
        else:
            m20.drop_tip()

    ctx.pause('Seal the plate with Microseal B, place on the preprogrammed \
thermal cycler, and run the PTC program. Replace on magnetic module when \
finished.')

    if not TEST_MODE_BEADS:
        magdeck.engage()
        ctx.delay(minutes=time_settling_minutes, msg=f'Incubating on \
MagDeck for {time_settling_minutes} minutes.')

    remove_supernatant(60, pip=m300, park=False)

    # wash
    wash(vol_wash, twb, time_incubation=0, time_settling=time_settling_minutes,
         premix=False, do_discard_supernatant=True, do_resuspend=True,
         vol_supernatant=vol_wash)
    wash(vol_wash, twb, time_incubation=0, time_settling=time_settling_minutes,
         premix=False, do_discard_supernatant=True, do_resuspend=True,
         vol_supernatant=vol_wash)
    wash(vol_wash, twb, time_incubation=0, time_settling=time_settling_minutes,
         premix=False, do_discard_supernatant=False, do_resuspend=True,
         vol_supernatant=vol_wash, park=False)
