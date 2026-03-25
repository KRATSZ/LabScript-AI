from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': '6. Illumina COVIDSeq - Amplify Tagmented Amplicons',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_BEADS = True
TEST_MODE_BIND_INCUBATE = True
TEST_MODE_TEMP = True
TEST_MODE_DROP = True

num_samples = 16


def run(ctx):

    if TEST_MODE_BEADS:
        mixreps = 1
    else:
        mixreps = 15
    time_settling_minutes = 3.0
    vol_mix = 70
    z_offset = 3.0
    radial_offset_fraction = 0.3  # fraction of radius
    engage_height = 8.5

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
    tag1_plate = magdeck.load_labware(
            'agilentwithnonskirted_96_wellplate_200ul', 'TAG1 plate')
    index_plate = ctx.load_labware(
        'agilent_96_wellplate_200ul', '5', 'index adapter plate')
    reagent_plate = tempdeck.load_labware(
        'quantgene_96_aluminumblock_200ul', 'reagent plate')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '8',
                                 'reagent reservoir')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['3', '6']]
    tips200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['9', '11']]

    # load P300M pipette
    m20 = ctx.load_instrument(
        'p20_multi_gen2', 'right', tip_racks=tips20)
    m300 = ctx.load_instrument(
         'p300_multi_gen2', 'left', tip_racks=tips200)

    # reagents and variables
    num_cols = math.ceil(num_samples/8)
    mag_samples = tag1_plate.rows()[0][:num_cols]
    index_adapters = index_plate.rows()[0][:num_cols]
    mm = reagent_plate.rows()[0][9:]
    liquid_trash = [
        well.top()
        for well in reservoir.rows()[0][10:10+(math.ceil(num_cols/6))]]

    vol_mm = 40.0
    vol_index_adapter = 10.0
    vol_wash = 100.0
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

    parked_tips = []

    def remove_supernatant(vol, pip=None, z_asp=0.2, park=True):
        nonlocal parked_tips
        if not pip:
            pip = m300 if vol >= 20 else m20
        pip.flow_rate.aspirate /= 5
        for i, s in enumerate(mag_samples):
            if not pip.has_tip:
                if park:
                    pick_up(pip, parked_tips[i])
                else:
                    pick_up(pip)
            pip.move_to(s.top())
            ctx.max_speeds['A'] = 25
            ctx.max_speeds['Z'] = 25
            side = 0
            pip.aspirate(vol, s.bottom().move(Point(x=side, z=z_asp)))
            pip.move_to(s.top())
            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']
            pip.dispense(vol, liquid_trash[i//6])
            if TEST_MODE_DROP:
                pip.return_tip()
            else:
                pip.drop_tip()
        pip.flow_rate.aspirate *= 5
        parked_tips = []

    def resuspend(location, reps=mixreps, vol=vol_mix,
                  samples=mag_samples, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=2.0):
        m300.flow_rate.aspirate *= 4
        m300.flow_rate.dispense *= 4
        side_x = 1 if samples.index(location) % 2 == 0 else -1
        m300.move_to(location.center())
        for r_ind in range(reps):
            bead_loc = location.bottom().move(
                Point(x=side_x*radius*radial_offset_fraction,
                      z=z_mix))
            m300.aspirate(vol, bead_loc)
            m300.dispense(vol, bead_loc.move(Point(z=dispense_height_rel)))
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4

    def wash(vol, reagent, time_incubation=0,
             time_settling=0, premix=False,
             do_discard_supernatant=True, do_resuspend=False,
             vol_supernatant=0, park=True):
        nonlocal parked_tips

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        last_source = None

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
            for _ in range(num_transfers):
                m300.aspirate(vol_per_transfer, source)
                slow_withdraw(m300, source)
                m300.dispense(vol_per_transfer, well.top())
            if do_resuspend:
                resuspend(well)
            else:
                if mixreps > 0:
                    m300.flow_rate.aspirate *= 4
                    m300.flow_rate.dispense *= 4
                    m300.mix(mixreps, vol_mix, well.bottom(2))
                    m300.flow_rate.aspirate /= 4
                    m300.flow_rate.dispense /= 4
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
            magdeck.engage(engage_height)
            if not TEST_MODE_BEADS:
                ctx.delay(minutes=time_settling, msg=f'Incubating on \
MagDeck for {time_settling} minutes.')

            remove_supernatant(vol_supernatant)
            magdeck.disengage()

    # remove previous supernatant
    magdeck.engage(engage_height)
    if not TEST_MODE_BEADS:
        ctx.delay(minutes=time_settling_minutes, msg=f'Incubating on \
MagDeck for {time_settling_minutes} minutes.')
    remove_supernatant(vol_wash, pip=m300, park=False)
    remove_supernatant(10, pip=m20, z_asp=0.1, park=False)

    for i, d in enumerate(mag_samples):
        pick_up(m300)
        source_mm = mm[i//4]
        m300.aspirate(vol_mm, source_mm.bottom(0.5))
        slow_withdraw(m300, source_mm)
        m300.dispense(vol_mm, d.bottom(2))
        slow_withdraw(m300, d)
        if TEST_MODE_DROP:
            m300.return_tip()
        else:
            m300.drop_tip()

    for s, d in zip(index_adapters, mag_samples):
        pick_up(m20)
        m20.aspirate(vol_index_adapter, s.bottom(0.5))
        slow_withdraw(m20, s)
        m20.dispense(vol_index_adapter, d.bottom(2))
        slow_withdraw(m20, d)
        if TEST_MODE_DROP:
            m20.return_tip()
        else:
            m20.drop_tip()

    ctx.comment('\n\n\n\nSeal and shake at 1600 rpm for 1 minute. If liquid \
is visible on the seal, centrifuge at 500 x g for 1 minute. Inspect to make \
sure beads are resuspended. To resuspend, set your pipette to 35 µl with the \
plunger down, and then slowly pipette to mix. Place on the preprogrammed \
thermal cycler and run the COVIDSeq TAG PCR program')
