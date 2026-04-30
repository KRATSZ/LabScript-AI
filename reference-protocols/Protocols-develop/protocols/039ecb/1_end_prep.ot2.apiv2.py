# flake8: noqa

from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': 'NEBNext® Ultra™ II FS DNA Library Prep Kit for \
Illumina',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [num_samples, start_place, mount_m300, mount_p20] = get_values(  # noqa: F821
        'num_samples', "start_place", 'mount_m300', 'mount_p20')

    # tuning parameters
    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200
    z_offset = 3.0
    radial_offset_fraction = 0.3  # fraction of radius

    # modules
    tc = ctx.load_module('thermocycler')
    tempdeck = ctx.load_module('temperature module gen2', '3')
    tempdeck.set_temperature(4)
    magdeck = ctx.load_module('magnetic module gen2', '1')

    # labware
    tc_plate = tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    pcr_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '2', 'PCR plate')
    mag_plate = magdeck.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tuberack = tempdeck.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    reagent_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '4',
                                     'reagent plate')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['5', '6']]
    tips200 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['9']]

    # load pipette
    p20 = ctx.load_instrument('p20_single_gen2', mount_p20, tip_racks=tips20)
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount_m300, tip_racks=tips200)

    liquid_trash = ctx.loaded_labwares[12].wells()[0].top()

    # reagents and variabless
    mm = tuberack.wells()[0]

    num_cols = math.ceil(num_samples/8)
    samples_s = pcr_plate.wells()[:num_samples]
    samples_m = pcr_plate.rows()[0][:num_cols]
    samples_s_tc = tc_plate.wells()[:num_samples]
    samples_m_tc = tc_plate.rows()[0][:num_cols]
    samples_s_mag = mag_plate.wells()[:num_samples]
    samples_m_mag = mag_plate.rows()[0][:num_cols]
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

    def remove_supernatant(vol, pip=m300, z_asp=0.2):

        ###############################

        # USER TO ADJUST THESE VARIABLES
        left_or_right_distance = 2
        mm_from_bottom = 0
        aspirate_flow_rate = 10  # the larger the number, the slower it will be

        ###############################

        pip.flow_rate.aspirate /= aspirate_flow_rate
        for i, s in enumerate(samples_m_mag):
            if not pip.has_tip:
                pick_up(pip)
            pip.move_to(s.top())
            ctx.max_speeds['A'] = 25
            ctx.max_speeds['Z'] = 25

            side = -left_or_right_distance if samples_m_mag.index(s) % 2 == 0 else left_or_right_distance  # ADJUST MM IN THE X, CHANGE LEFT_OR_RIGHT_DISTANCE
            pip.aspirate(vol, s.bottom(z=mm_from_bottom).move(Point(x=side, z=z_asp)))
            pip.move_to(s.top())
            del ctx.max_speeds['A']
            del ctx.max_speeds['Z']
            pip.dispense(vol, liquid_trash)
            pip.blow_out(liquid_trash)
            pip.air_gap(10)
            pip.drop_tip()
        pip.flow_rate.aspirate *= 5

    def resuspend(location, reps, vol, samples,
                  x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=2.0,
                  speed_up=True):
        if speed_up:
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
        slow_withdraw(m300, location)
        if speed_up:
            m300.flow_rate.aspirate /= 4
            m300.flow_rate.dispense /= 4

    def wash(vol, reagent, time_incubation=0,
             time_settling=0, premix=False,
             do_discard_supernatant=True, do_resuspend=False,
             vol_supernatant=0, park=True):

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        last_source = None

        for i, well in enumerate(samples_m_mag):
            source = reagent[i//columns_per_channel]
            pick_up(m300)
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
                magdeck.disengage()
                resuspend(well)
            m300.air_gap(20)
            m300.drop_tip()

        if time_incubation > 0:
            ctx.delay(minutes=time_incubation,
                      msg=f'Incubating off MagDeck for \
{time_incubation} minutes.')
        if do_discard_supernatant:
            magdeck.engage()
            ctx.delay(minutes=time_settling, msg=f'Incubating on \
MagDeck for {time_settling} minutes.')

            remove_supernatant(vol_supernatant)
            magdeck.disengage()

    """

    1. Fragmentation/End Preparation

    """

    vol_mm = 4.5
    vol_reaction = 17.5

    if start_place < 1:

        for s in samples_s_tc:
            pick_up(p20)
            p20.aspirate(vol_mm, mm)
            slow_withdraw(p20, mm)
            p20.dispense(vol_mm, s.bottom(1))
            p20.blow_out(s.bottom(1))
            ctx.delay(seconds=2)
            slow_withdraw(p20, s)
            p20.drop_tip()

        for m in samples_m_tc:
            pick_up(m300)
            m300.mix(10, 10, m)
            m300.blow_out(m)
            ctx.delay(seconds=2)
            slow_withdraw(m300, m)
            m300.drop_tip()

        ctx.pause('\n\n\n\nCentrifugre PCR plate if necessary. Resume once \
    plate is returned to slot 2.\n\n\n\n')

        tc.open_lid()
        tc.set_lid_temperature(75)

        for s, d in zip(samples_m, samples_m_tc):
            pick_up(m300)
            m300.aspirate(vol_reaction, s.bottom(0.5))
            ctx.delay(seconds=2)
            slow_withdraw(m300, s)
            m300.dispense(vol_reaction, d.bottom(1))
            ctx.delay(seconds=2)
            slow_withdraw(m300, d)
            m300.drop_tip()

        profile = [
            {'temperature': 37, 'hold_time_minutes': 5},
            {'temperature': 65, 'hold_time_minutes': 30}
        ]
        tc.close_lid()
        tc.execute_profile(steps=profile, repetitions=1,
                           block_max_volume=vol_reaction)
        tc.set_block_temperature(4)
        tc.open_lid()

        ctx.pause('\n\n\n\nCentrifuge PCR plate if necessary. Resume once \
    plate is returned to Thermocycler.\n\n\n\n')




    """

    2. Adaptor Ligation

    """
    mm = tuberack.wells()[1]
    user = tuberack.wells()[2]
    vol_mm = 16.75
    vol_user = 1.5

    if start_place < 2:


        tc.deactivate_lid()

        for s in samples_s_tc:
            pick_up(p20)
            p20.aspirate(vol_mm, mm)
            slow_withdraw(p20, mm)
            p20.dispense(vol_mm, s.bottom(1))
            slow_withdraw(p20, s)
            p20.drop_tip()

        for m in samples_m_tc:
            pick_up(m300)
            m300.mix(10, 25, m)
            m300.blow_out()
            ctx.delay(seconds=2)
            slow_withdraw(m300, m)
            m300.drop_tip()

        ctx.pause('\n\n\n\nCentrifuge PCR plate if necessary. Resume once \
    plate is returned to Thermocycler.\n\n\n\n')

        tc.close_lid()
        tc.set_block_temperature(20, hold_time_minutes=15)
        tc.open_lid()

        ctx.pause('\n\n\n\nPlace USER enzyme in position C1 of tuberack on \
    temprature module. Resume once finished.\n\n\n\n')

        for s in samples_s_tc:
            pick_up(p20)
            p20.aspirate(vol_user, user, rate=0.4)
            slow_withdraw(p20, user)
            p20.dispense(vol_user, s.bottom(1))
            p20.mix(1, 15, s.bottom(1))
            p20.blow_out()
            slow_withdraw(p20, s)
            p20.drop_tip()

        for m in samples_m_tc:
            pick_up(m300)
            m300.mix(10, 25, m)
            m300.blow_out()
            ctx.delay(seconds=2)
            slow_withdraw(m300, m)
            m300.drop_tip()

        ctx.pause('\n\n\n\nCentrifuge PCR plate if necessary. Resume once \
    plate is returned to Thermocycler.\n\n\n\n')

        tc.set_lid_temperature(47)
        tc.close_lid()

        tc.set_block_temperature(37, hold_time_minutes=15)
        tc.set_block_temperature(4)
        tc.open_lid()

        ctx.pause('\n\n\n\nCentrifuge PCR plate if necessary. Move Thermocycler plate to magnetic module.\n\n\n')



    """

    3. Cleanup of Adaptor-Ligated DNA

    """
    samples_s_tc = tc_plate.wells()[num_samples:num_samples*2]
    samples_m_tc = tc_plate.rows()[0][num_cols:num_cols*2]

    vahts_beads = reagent_plate.rows()[0][0]
    etoh = reagent_plate.rows()[0][2]
    nuclease_free_water = reagent_plate.rows()[0][11]
    vol_vahts_beads = 28.5
    vol_etoh = 100.0
    vol_water = 9.0
    vol_elution = 7.5

    if start_place < 3:





        for i, s in enumerate(samples_m_mag):
            pick_up(m300)
            if i == 0:
                m300.mix(10, 20, vahts_beads)
                m300.blow_out()
            m300.aspirate(vol_vahts_beads, vahts_beads)
            slow_withdraw(m300, vahts_beads)
            m300.dispense(vol_vahts_beads, s)
            m300.mix(10, 20, s)
            m300.blow_out()
            ctx.delay(seconds=2)
            slow_withdraw(m300, s)
            m300.drop_tip()

        ctx.pause('\n\n\n\nCentrifuge PCR plate if necessary. Resume once \
    plate is returned to Thermocycler.\n\n\n\n')

        ctx.delay(minutes=5, msg='\n\n\n\nIncubating\n\n\n\n')
        magdeck.engage()
        ctx.delay(minutes=5, msg='\n\n\n\nBeads separating\n\n\n\n')

        ctx.pause('\n\n\n\nResume once supernatant is clear\n\n\n\n')
        remove_supernatant(62)

        # washes
        for _ in range(2):
            pick_up(m300)
            for s in samples_m_mag:
                if not m300.has_tip:
                    pick_up(m300)
                m300.aspirate(vol_etoh, etoh)
                slow_withdraw(m300, etoh)
                m300.dispense(vol_etoh, s.top())
                m300.drop_tip()

            if not m300.has_tip:
                m300.pick_up_tip()
            ctx.delay(seconds=30, msg='\n\n\n\nIncubating\n\n\n\n')
            remove_supernatant(102)

        ctx.pause('Resume once beads are dry.')
        magdeck.disengage()

        for s in samples_m_mag:
            pick_up(m300)
            m300.aspirate(vol_water, nuclease_free_water)
            slow_withdraw(m300, nuclease_free_water)
            m300.dispense(vol_water, s)
            resuspend(s, reps=10, vol=7, samples=samples_m_mag, speed_up=False)
            m300.drop_tip()

        ctx.delay(minutes=2, msg='\n\n\n\nIncubating\n\n\n\n')
        magdeck.engage()
        ctx.delay(minutes=5, msg='\n\n\n\nBeads separating\n\n\n\n')

        ctx.pause('\n\n\n\nResume once supernatant is clear.\n\n\n\n')

        for s, d in zip(samples_s_mag, samples_s_tc):
            pick_up(p20)
            p20.aspirate(vol_elution, s.bottom(0.2))
            p20.dispense(vol_elution, d.bottom(0.2))
            wick(p20, d)
            p20.drop_tip()

        magdeck.disengage()

    """

    4. PCR Amplification

    """

    mm = tuberack.wells()[3]
    vol_mm = 12.5

    if start_place < 4:

        for s in samples_s_tc:
            pick_up(p20)
            p20.aspirate(vol_mm, mm)
            slow_withdraw(p20, mm)
            p20.dispense(vol_mm, s.bottom(1))
            slow_withdraw(p20, s)
            p20.drop_tip()

        ctx.pause('Add 5ul of Primer indexes, vortex and centrifuge manually. \
    Place back into the thermocycler block when finished.')

        profile = [
            {'temperature': 98, 'hold_time_seconds': 10},
            {'temperature': 65, 'hold_time_seconds': 75}
        ]
        tc.close_lid()
        tc.set_block_temperature(98, hold_time_seconds=30)
        tc.execute_profile(profile, repetitions=6)
        tc.set_block_temperature(65, hold_time_minutes=5)
        tc.set_block_temperature(4)
        tc.open_lid()

        ctx.pause('\n\n\n\nRefill all tips and reagents, and move \
    Thermocycler plate to magnetic module.\n\n\n\n')
        p20.reset_tipracks()
        m300.reset_tipracks()



    """

    5. Cleanup of PCR Reaction

    """

    samples_s_mag = mag_plate.wells()[num_samples:num_samples*3]
    samples_m_mag = mag_plate.rows()[0][num_cols:num_cols*3]
    samples_m_eluton = pcr_plate.rows()[0][:num_cols]

    vol_vahts_beads = 22.5
    vol_etoh = 100.0
    vol_water = 27.0
    vol_elution = 25.0

    if start_place < 5:

        for i, s in enumerate(samples_m_mag):
            pick_up(m300)
            if i == 0:
                m300.mix(10, 20, vahts_beads)
                m300.blow_out()
            m300.aspirate(vol_vahts_beads, vahts_beads)
            slow_withdraw(m300, vahts_beads)
            m300.dispense(vol_vahts_beads, s)
            m300.mix(10, 20, s)
            m300.blow_out()
            ctx.delay(seconds=2)
            slow_withdraw(m300, s)
            m300.drop_tip()

        ctx.delay(minutes=5, msg='\n\n\n\nIncubating\n\n\n\n')
        magdeck.engage()
        ctx.delay(minutes=5, msg='\n\n\n\nBeads separating\n\n\n\n')

        ctx.pause('\n\n\n\nResume once supernatant is clear\n\n\n\n')
        remove_supernatant(46)

        # washes
        for _ in range(2):
            pick_up(m300)
            for s in samples_m_mag:
                if not m300.has_tip:
                    pick_up(m300)
                m300.aspirate(vol_etoh, etoh)
                slow_withdraw(m300, etoh)
                m300.dispense(vol_etoh, s.top())
                m300.drop_tip()
            if not m300.has_tip:
                pick_up(m300)
            ctx.delay(seconds=30, msg='\n\n\n\nIncubating\n\n\n\n')
            remove_supernatant(102)

        ctx.pause('Resume once beads are dry.')
        magdeck.disengage()

        for s in samples_m_mag:
            pick_up(m300)
            m300.aspirate(vol_water, nuclease_free_water)
            slow_withdraw(m300, nuclease_free_water)
            m300.dispense(vol_water, s)
            resuspend(s, reps=10, vol=7, samples=samples_m_mag)
            m300.drop_tip()

        ctx.delay(minutes=2, msg='\n\n\n\nIncubating\n\n\n\n')
        magdeck.engage()
        ctx.delay(minutes=5, msg='\n\n\n\nBeads separating\n\n\n\n')

        ctx.pause('\n\n\n\nResume once supernatant is clear\n\n\n\n')

        for s, d in zip(samples_m_mag, samples_m_eluton):
            pick_up(m300)
            m300.aspirate(vol_elution, s.bottom(0.2))
            m300.dispense(vol_elution, d.bottom(0.2))
            wick(m300, d)
            m300.drop_tip()

        magdeck.disengage()
