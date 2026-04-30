from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Zymo Quick-DNA/RNA™ Viral MagBead Extraction',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.13'
}

TEST_MODE_BEADS = False
TEST_MODE_BIND_INCUBATE = False
TEST_MODE_AIRDRY = False


def run(ctx):

    [num_samples] = get_values(  # noqa: F821
        'num_samples')

    # tuning parameters
    mixreps = 1 if TEST_MODE_BEADS else 15
    time_settling_minutes = 3.0
    time_airdry_minutes = 10.0
    vol_mix = 200
    z_offset = 3.0
    radial_offset_fraction = 0.4  # fraction of radius
    engage_height = 7.6

    # volumes
    vol_sample = 400.0
    vol_viral_dna_rna_buffer = 400.0
    vol_magbinding_beads = 20.0
    vol_wash_magbead_dna_rna_1 = 250.0
    vol_wash_magbead_dna_rna_2 = 250.0
    vol_ethanol = 250.0
    vol_elution = 30.0

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    # load modules
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()

    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep',
                                    'deepwell plate')
    elutionplate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                    '3', 'elution plate')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '4',
                             'Liquid Waste').wells()[0]
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '5',
                            'reagent reservoir 1')
    res2 = ctx.load_labware('nest_1_reservoir_195ml', '2',
                            'reagent reservoir 2')
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                         '200µl filtertiprack')
        for slot in ['6', '7', '8', '9', '10', '11']]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    viral_dna_rna_buffer = res2.rows()[0][:1]
    magbinding_beads = res1.rows()[0][:1]
    wash_magbead_dna_rna_1 = res1.rows()[0][1:3]
    wash_magbead_dna_rna_2 = res1.rows()[0][3:5]
    ethanol1 = res1.rows()[0][5:7]
    ethanol2 = res1.rows()[0][7:9]
    dnase_rnase_free_water = res1.rows()[0][9:10]

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

    def remove_supernatant(vol, destinations, z_asp=z_offset, z_disp=1.0,
                           park=False):
        nonlocal parking_spots

        dest_list = [destinations]*num_cols \
            if type(destinations) != list else destinations

        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)
        m300.flow_rate.aspirate /= 5
        for i, (m, dest) in enumerate(zip(mag_samples_m, dest_list)):
            if park:
                pick_up(m300, parking_spots[i])
            else:
                pick_up()
            for _ in range(num_transfers):
                m300.aspirate(vol_per_transfer, m.bottom(z_asp))
                slow_withdraw(m)
                m300.dispense(vol_per_transfer, dest.bottom(z_disp))
                ctx.delay(seconds=2)
                m300.air_gap(5)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 5
        parking_spots = []

    def resuspend(location, reps=mixreps, vol=vol_mix,
                  samples=mag_samples_m, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=8):
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

    def lyse_bind_wash(vol, reagent, time_incubation=0,
                       time_settling=time_settling_minutes, premix=False,
                       do_discard_supernatant=True, do_resuspend=True,
                       vol_supernatant=0, supernatant_locations=waste,
                       park=True):
        nonlocal parking_spots

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        last_source = None
        if do_resuspend:
            magdeck.disengage()

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
            if park:
                parking_spots.append(m300._last_tip_picked_up_from)
                m300.return_tip()
            else:
                m300.drop_tip()

        if do_discard_supernatant:
            magdeck.engage(engage_height)
            ctx.delay(minutes=time_settling, msg='\n\n\n\nBeads \
settling.\n\n\n\n')
            remove_supernatant(vol_supernatant,
                               destinations=supernatant_locations,
                               park=park)

    lyse_bind_wash(vol=vol_viral_dna_rna_buffer, reagent=viral_dna_rna_buffer,
                   do_discard_supernatant=False, park=False)
    lyse_bind_wash(vol=vol_magbinding_beads, reagent=magbinding_beads,
                   do_discard_supernatant=True,
                   vol_supernatant=vol_sample +
                   vol_viral_dna_rna_buffer +
                   vol_magbinding_beads)
    lyse_bind_wash(vol=vol_wash_magbead_dna_rna_1,
                   reagent=wash_magbead_dna_rna_1,
                   vol_supernatant=vol_wash_magbead_dna_rna_1,
                   do_discard_supernatant=True)
    lyse_bind_wash(vol=vol_wash_magbead_dna_rna_2,
                   reagent=wash_magbead_dna_rna_2,
                   vol_supernatant=vol_wash_magbead_dna_rna_2,
                   do_discard_supernatant=True)
    lyse_bind_wash(vol=vol_ethanol,
                   reagent=ethanol1,
                   vol_supernatant=vol_ethanol,
                   do_discard_supernatant=True)
    lyse_bind_wash(vol=vol_ethanol,
                   reagent=ethanol2,
                   vol_supernatant=vol_ethanol,
                   do_discard_supernatant=True)
    lyse_bind_wash(vol=vol_wash_magbead_dna_rna_2,
                   reagent=wash_magbead_dna_rna_2,
                   vol_supernatant=vol_wash_magbead_dna_rna_2,
                   do_discard_supernatant=True)

    ctx.delay(minutes=time_airdry_minutes, msg=f'Airdrying for \
{time_airdry_minutes} minutes.')

    lyse_bind_wash(vol=vol_elution,
                   reagent=dnase_rnase_free_water,
                   vol_supernatant=vol_elution,
                   do_discard_supernatant=True,
                   supernatant_locations=elution_samples_m)
