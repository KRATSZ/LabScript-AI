from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Zymo Quick-DNA HMW MagBead Kit',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.11'
}

TEST_MODE_BEADS = False
TEST_MODE_TEMP = False
TEST_MODE_BIND_INCUBATE = False
TEST_MODE_AIRDRY = False


def run(ctx):

    [num_samples, lw_deepwell_plate, starting_vol, mixreps,
     time_settling_minutes, time_airdry_minutes,
     vol_final_elution] = get_values(  # noqa: F821
        'num_samples', 'lw_deepwell_plate', 'starting_vol',
        'mixreps', 'time_settling_minutes', 'time_airdry_minutes',
        'vol_final_elution')

    if TEST_MODE_BEADS:
        mixreps = 1
    vol_mix = 200
    z_offset = 3.0
    radial_offset_fraction = 0.4  # fraction of radius
    vol_scalar = starting_vol/200
    vol_binding_buffer = 216*vol_scalar
    vol_quick_dna_magbinding_buffer = 250*vol_scalar
    vol_dna_pre_wash_buffer = 250*vol_scalar
    vol_g_dna_wash_buffer = 450*vol_scalar
    vol_elution = vol_final_elution + 15
    engage_height = 7.6

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    magdeck = ctx.load_module('magnetic module gen2', '4')
    magdeck.disengage()
    magplate = magdeck.load_labware(lw_deepwell_plate, 'deepwell plate')
    tempdeck = ctx.load_module('Temperature Module Gen2', '1')
    elutionplate = tempdeck.load_labware(
                'opentrons_96_aluminumblock_biorad_wellplate_200ul',
                'elution plate')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '7',
                             'Liquid Waste').wells()[0].top()
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '5',
                            'reagent reservoir 1')
    res2 = ctx.load_labware('nest_12_reservoir_15ml', '2',
                            'reagent reservoir 2')
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                         '200µl filtertiprack')
        for slot in [
                '3', '6', '8', '9', '10', '11'][:math.ceil(num_samples/16)]]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    binding_buffer = res1.wells()[:3]
    quick_dna_magbinding_buffer = res1.wells()[3:7]
    dna_pre_wash_buffer = res1.wells()[7:11]
    elution_buffer = res1.wells()[11:]
    g_dna_wash_buffer = [res2.wells()[i*4:(i+1)*4] for i in range(2)]

    num_cols = math.ceil(num_samples/8)
    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
    all_tips = [well for rack in tips300 for well in rack.rows()[0]]
    parking_sets = []
    for i in range(6):
        if (i+1)*num_cols <= len(all_tips):
            set = all_tips[i*num_cols:(i+1)*num_cols]
        else:
            set = all_tips[
                (i*num_cols) % len(all_tips):(i+1)*num_cols % len(all_tips)]
        parking_sets.append(set)
    if mag_samples_m[0].width:
        radius = mag_samples_m[0].width/2
    else:
        radius = mag_samples_m[0].diameter/2

    magdeck.disengage()  # just in case

    last_index = 0

    def check_set(set):
        nonlocal last_index
        new_index = all_tips.index(set[0])
        if new_index < last_index:
            ctx.pause('Please refill tipracks before resuming.')
        last_index = new_index

    waste_vol = 0
    waste_threshold = 185000

    def remove_supernatant(vol, parking_spots, park=False):
        """
        `remove_supernatant` will transfer supernatant from the deepwell
        extraction plate to the liquid waste reservoir.
        :param vol (float): The amount of volume to aspirate from all deepwell
                            sample wells and dispense in the liquid waste.
        :param park (boolean): Whether to pick up sample-corresponding tips
                               in the 'parking rack' or to pick up new tips.
        """

        def _waste_track(vol):
            nonlocal waste_vol
            if waste_vol + vol >= waste_threshold:
                # Setup for flashing lights notification to empty liquid waste
                ctx.home()
                ctx.pause('Please empty liquid waste before resuming.')
                waste_vol = 0
            waste_vol += vol

        check_set(parking_spots)

        m300.flow_rate.aspirate /= 5
        for m, spot in zip(mag_samples_m, parking_spots):
            m300.pick_up_tip(spot)
            _waste_track(vol)
            num_trans = math.ceil(vol/200)
            vol_per_trans = vol/num_trans
            for _ in range(num_trans):
                m300.dispense(m300.current_volume, m.top())
                m300.transfer(vol_per_trans, m.bottom(0.8), waste,
                              new_tip='never')
                ctx.delay(seconds=2)
                # m300.blow_out(waste)
                m300.air_gap(5)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 5

    def resuspend(location, reps=mixreps, vol=vol_mix, method='mix',
                  samples=mag_samples_m, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=8):

        if method == 'shake':
            pass
        elif 'mix' in method:
            m300.flow_rate.aspirate *= 4
            m300.flow_rate.dispense *= 4
            side_x = 1 if samples.index(location) % 2 == 0 else -1
            m300.move_to(location.center())
            for r_ind in range(reps):
                side_y = 1 if r_ind % 2 == 0 else -1
                bead_loc = location.bottom().move(
                    Point(x=side_x*radius*radial_offset_fraction,
                          y=side_y*radius*radial_offset_fraction,
                          z=z_mix))
                m300.aspirate(vol, bead_loc)
                m300.dispense(vol, bead_loc.move(Point(z=dispense_height_rel)))
            m300.flow_rate.aspirate /= 4
            m300.flow_rate.dispense /= 4

    def bind(vol, parking_spots):
        """
        `bind` will perform magnetic bead binding on each sample in the
        deepwell plate. Each channel of binding beads will be mixed before
        transfer, and the samples will be mixed with the binding beads after
        the transfer. The magnetic deck activates after the addition to all
        samples, and the supernatant is removed after bead bining.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """

        check_set(parking_spots)

        latest_chan = -1
        chan_ind = 0
        vol_track = 0
        max_vol_per_chan = 0.95*res1.wells()[0].max_volume
        for i, (well, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            m300.pick_up_tip(spot)
            if vol_track + 8*vol > max_vol_per_chan:
                chan_ind += 1
                vol_track = 0
            vol_track += 8*vol
            source = binding_buffer[chan_ind]
            if chan_ind != latest_chan:  # mix if accessing new channel
                m300.flow_rate.aspirate *= 4
                m300.flow_rate.dispense *= 4
                for _ in range(3):
                    m300.aspirate(200, source.bottom(0.5))
                    m300.dispense(200, source.bottom(5))
                latest_chan = chan_ind
                m300.flow_rate.aspirate /= 4
                m300.flow_rate.dispense /= 4
            m300.transfer(vol, source, well.top(), new_tip='never')
            m300.flow_rate.aspirate *= 4
            m300.flow_rate.dispense *= 4
            m300.mix(mixreps, vol_mix, well.bottom(2))
            m300.flow_rate.aspirate /= 4
            m300.flow_rate.dispense /= 4
            m300.air_gap(20)
            m300.drop_tip(spot)

        magdeck.engage(engage_height)
        if not TEST_MODE_BEADS:
            ctx.delay(minutes=time_settling_minutes, msg=f'Incubating on \
MagDeck for {time_settling_minutes} minutes.')

        # remove initial supernatant
        remove_supernatant(vol+starting_vol, parking_spots)

    def wash(vol, source, parking_spots, remove=True,
             resuspend_method='mix', supernatant_volume=None,
             samples=mag_samples_m, shake_time=5, incubation_time=None,
             resuspend_vol=None, mix_before=False,
             aspiration_location: Point = None):
        """
        `wash` will perform bead washing for the extraction protocol.
        :param vol (float): The amount of volume to aspirate from each
                            source and dispense to each well containing beads.
        :param source (List[Well]): A list of wells from where liquid will be
                                    aspirated. If the length of the source list
                                    > 1, `wash` automatically calculates
                                    the index of the source that should be
                                    accessed.
        :param mix_reps (int): The number of repititions to mix the beads with
                               specified wash buffer (ignored if resuspend is
                               False).
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding wash buffer and removing
                               supernatant.
        :param resuspend (boolean): Whether to resuspend beads in wash buffer.
        """

        check_set(parking_spots)

        if magdeck.status == 'engaged':
            magdeck.disengage()

        latest_chan_ind = -1
        cols_per_source_chan = math.ceil(12/len(source))
        num_trans = math.ceil(vol/200)
        air_gap_vol = None
        vol_per_trans = vol/num_trans
        for i, (well, spot) in enumerate(zip(samples, parking_spots)):
            m300.pick_up_tip(spot)
            chan_ind = i//cols_per_source_chan
            src = source[chan_ind]
            if aspiration_location:
                src_asp_loc = src.bottom().move(aspiration_location)
            else:
                src_asp_loc = src.bottom(0.5)

            # mix if accessing new channel of beads
            if mix_before and chan_ind != latest_chan_ind:
                m300.flow_rate.aspirate *= 4
                m300.flow_rate.dispense *= 4
                for _ in range(5):
                    m300.aspirate(200, src_asp_loc)
                    m300.dispense(200, src.bottom(5))
                latest_chan_ind = chan_ind
                m300.flow_rate.aspirate /= 4
                m300.flow_rate.dispense /= 4

            for n in range(num_trans):
                m300.dispense(m300.current_volume, src.top())
                m300.aspirate(vol_per_trans, src_asp_loc)
                m300.move_to(src.top())
                if air_gap_vol:
                    m300.aspirate(air_gap_vol, src.top())
                m300.dispense(m300.current_volume, well.top())
                ctx.delay(seconds=2)
                # m300.blow_out(well.top())
                if n < num_trans - 1:
                    m300.aspirate(10, well.top())
            resus_vol = resuspend_vol if resuspend_vol else vol_mix
            resuspend(well, mixreps, resus_vol, method=resuspend_method,
                      samples=samples)
            m300.move_to(well.top())
            ctx.delay(seconds=2)
            m300.air_gap(5)
            m300.drop_tip(spot)

        if incubation_time and not TEST_MODE_BIND_INCUBATE:
            ctx.delay(minutes=incubation_time, msg=f'Incubating off MagDeck \
for {incubation_time} minutes.')

        if remove:
            if magdeck.status == 'disengaged':
                magdeck.engage(engage_height)

            if not TEST_MODE_BEADS:
                ctx.delay(minutes=time_settling_minutes, msg=f'Incubating on \
MagDeck for {time_settling_minutes} minutes.')

            removal_vol = supernatant_volume if supernatant_volume else vol
            remove_supernatant(removal_vol, parking_spots)

    def elute(vol, parking_spots):
        """
        `elute` will perform elution from the deepwell extraciton plate to the
        final clean elutions PCR plate to complete the extraction protocol.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """

        check_set(parking_spots)

        # resuspend beads in elution
        magdeck.disengage()
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            m300.pick_up_tip(spot)
            m300.aspirate(vol, elution_buffer[0])
            m300.dispense(vol, m.bottom(1))
            resuspend(m, mixreps, 40, x_mix_fraction=0.2, z_mix=1.0,
                      dispense_height_rel=0)
            m300.blow_out(m.bottom(5))
            m300.air_gap(5)
            m300.drop_tip(spot)

        if not TEST_MODE_BIND_INCUBATE:
            ctx.delay(minutes=5, msg='Incubating off MagDeck for 5 minutes.')

        magdeck.engage(engage_height)

        if not TEST_MODE_BEADS:
            ctx.delay(minutes=time_settling_minutes, msg=f'Incubating on \
MagDeck for {time_settling_minutes} minutes.')

        m300.flow_rate.aspirate /= 5
        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            m300.pick_up_tip(spot)
            m300.aspirate(vol_final_elution, m.bottom(0.8))
            m300.dispense(vol_final_elution, e.bottom(5))
            m300.move_to(e.bottom().move(Point(x=e.diameter/2*0.8, z=7)))
            m300.blow_out(e.top(-2))
            m300.air_gap(5)
            m300.drop_tip(spot)

    wash(vol_binding_buffer, binding_buffer, parking_spots=parking_sets[0],
         mix_before=True, supernatant_volume=starting_vol+vol_binding_buffer,
         incubation_time=10.0)
    wash(vol_quick_dna_magbinding_buffer, quick_dna_magbinding_buffer,
         parking_spots=parking_sets[1])
    wash(vol_dna_pre_wash_buffer, dna_pre_wash_buffer,
         parking_spots=parking_sets[2])
    for i, set_ind in enumerate([3, 4]):
        wash(vol_g_dna_wash_buffer, g_dna_wash_buffer[i],
             parking_spots=parking_sets[set_ind],
             aspiration_location=Point(x=-4.5, z=0.5))
    if not TEST_MODE_AIRDRY:
        ctx.delay(minutes=time_airdry_minutes, msg=f'Air drying for \
{time_airdry_minutes} minutes before final elution.')
    if not TEST_MODE_TEMP:
        tempdeck.set_temperature(4)
    elute(vol_elution, parking_spots=parking_sets[5])

    magdeck.disengage()
    ctx.comment('Protocol complete.')
