from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Nucleic Acid Purification',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_BEADS = False
TEST_MODE_BIND_INCUBATE = False
TEST_MODE_AIRDRY = False


def run(ctx):

    [num_samples, vol_water, vol_ampure_beads,
     mount_m300] = get_values(  # noqa: F821
        'num_samples', 'vol_water', 'vol_ampure_beads', 'mount_m300')

    # tuning parameters
    mixreps = 1 if TEST_MODE_BEADS else 15
    time_settling_minutes = 0 if TEST_MODE_BEADS else 3.0
    [time_incubation_minutes, time_airdry_minutes] = [0, 0] \
        if TEST_MODE_BIND_INCUBATE else [5.0, 3.0]
    time_airdry_minutes = 3.0
    vol_mix = 25
    z_offset = 2.0
    radial_offset_fraction = 0.4  # fraction of radius
    # engage_height = 7.6

    # volumes
    vol_sample = 12.5
    vol_etoh = 200.0
    vol_elution = 28.0
    vol_elution_final = 25.0

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    # load modules
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()

    magplate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr')
    elutionplate = ctx.load_labware('biorad_96_aluminumblock_350ul',
                                    '2', 'elution plate')
    waste = ctx.loaded_labwares[12].wells()[0]
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '4',
                            'reagent reservoir 1')
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                         '200µl filtertiprack')
        for slot in ['3', '5', '6', '7', '8', '9', '10', '11']]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount_m300, tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    water = res1.rows()[0][:1]
    ampure_beads = res1.rows()[0][1:2]
    etoh_sets = [res1.rows()[0][i*2:(i+1)*2] for i in range(1, 3)]

    num_cols = math.ceil(num_samples/8)
    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
    if mag_samples_m[0].width:
        radius = mag_samples_m[0].width/2
    else:
        radius = mag_samples_m[0].diameter/2

    def pick_up(pip=m300, spot=None):
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

    def slow_withdraw(well, pip=m300):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    parking_spots = []

    def remove_supernatant(vol, destinations, z_asp=0.3, z_disp=1.0,
                           park=False):
        nonlocal parking_spots

        dest_list = [destinations]*num_cols \
            if type(destinations) != list else destinations

        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)
        m300.flow_rate.aspirate /= 10
        for i, (m, dest) in enumerate(zip(mag_samples_m, dest_list)):
            if park:
                pick_up(m300, parking_spots[i])
            else:
                pick_up()
            for _ in range(num_transfers):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, m.top())
                m300.aspirate(vol_per_transfer, m.bottom(z_asp))
                slow_withdraw(m)
                m300.dispense(vol_per_transfer, dest.bottom(z_disp))
                m300.blow_out(dest.bottom(z_disp))
                ctx.delay(seconds=2)
                slow_withdraw(dest)
                m300.air_gap(5)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 10
        parking_spots = []

    def resuspend(location, reps=mixreps, vol=vol_mix,
                  samples=mag_samples_m, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=3):
        m300.flow_rate.aspirate *= 3
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
            m300.blow_out(location.top(-5))
        m300.flow_rate.aspirate /= 3
        m300.flow_rate.dispense /= 4

    def lyse_bind_wash(vol, reagent, time_incubation=0,
                       time_settling=time_settling_minutes, premix=False,
                       do_blowout=False,
                       do_discard_supernatant=True, do_resuspend=True,
                       vol_supernatant=0, supernatant_locations=waste,
                       park=False, z_disp=2.0, disengage_after=True):
        nonlocal parking_spots

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        last_source = None
        if do_resuspend:
            magdeck.disengage()
        else:
            magdeck.engage()

        for i, well in enumerate(mag_samples_m):
            source = reagent[i//columns_per_channel]
            pick_up()
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
                slow_withdraw(source)
                m300.dispense(vol_per_transfer, well.top(-1))
                if do_blowout:
                    m300.blow_out(well.top(-1))
            if do_resuspend:
                resuspend(well)
            ctx.delay(seconds=2)
            slow_withdraw(well, m300)
            m300.air_gap(20, height=0)
            if park:
                parking_spots.append(m300._last_tip_picked_up_from)
                m300.return_tip()
            else:
                m300.drop_tip()

        if time_incubation > 0:
            ctx.delay(minutes=time_incubation,
                      msg='\n\n\n\nIncubating\n\n\n\n')

        if do_discard_supernatant:
            if not magdeck.status == 'engaged':
                magdeck.engage()
            if time_settling > 0:
                ctx.delay(minutes=time_settling, msg='\n\n\n\nBeads \
settling.\n\n\n\n')
            remove_supernatant(vol_supernatant,
                               destinations=supernatant_locations,
                               park=park, z_disp=z_disp)
        if disengage_after:
            magdeck.disengage()

    lyse_bind_wash(vol=vol_water, reagent=water, do_resuspend=False,
                   do_discard_supernatant=False, park=False, do_blowout=True)
    lyse_bind_wash(vol=vol_ampure_beads, reagent=ampure_beads,
                   time_incubation=5, time_settling=5,
                   do_discard_supernatant=True, premix=True, do_resuspend=True,
                   vol_supernatant=vol_sample+vol_water+vol_ampure_beads)
    if not magdeck.status == 'engaged':
        magdeck.engage()
    for etoh in etoh_sets:
        lyse_bind_wash(vol=vol_etoh, reagent=etoh, time_incubation=0.5,
                       time_settling=0,
                       do_discard_supernatant=True, do_resuspend=False,
                       vol_supernatant=vol_etoh, disengage_after=False)

    ctx.delay(minutes=time_airdry_minutes, msg='\n\n\n\nAirdrying\n\n\n\n')
    lyse_bind_wash(vol=vol_elution, reagent=water,
                   time_incubation=time_incubation_minutes,
                   do_discard_supernatant=True, do_resuspend=True,
                   vol_supernatant=vol_elution_final,
                   supernatant_locations=elution_samples_m, z_disp=2.0)
