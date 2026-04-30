from opentrons import protocol_api
from opentrons.types import Point
import math

metadata = {
    'protocolName': 'Zymo Zyppy™-96 Plasmid MagBead Miniprep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.12'
}

TEST_MODE_BEADS = False
TEST_MODE_BIND_INCUBATE = False
TEST_MODE_AIRDRY = False


def run(ctx):

    [num_samples, mixreps, time_airdry_minutes, vol_final_elution,
     engage_height,
        mount_m300] = get_values(  # noqa: F821
        'num_samples', 'mixreps', 'time_airdry_minutes', 'vol_final_elution',
        'engage_height',
        'mount_m300')

    if TEST_MODE_BEADS:
        mixreps = 1
    # time_settling_bind_minutes = 5.0
    time_settling_wash_minutes = 2.0
    vol_mix = 180
    z_offset = 3.0
    radial_offset_fraction = 0.6  # fraction of radius
    vol_cleared_lysate = 750.0
    vol_elution = 40
    # engage_height = 4.9
    time_incubation_deep_blue_minutes = 5.0
    time_incubation_elution_minutes = 5.0

    ctx.max_speeds['X'] = 200
    ctx.max_speeds['Y'] = 200

    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep',
                                    'deepwell plate')
    collection_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '2',
                                        'collection plate')
    elutionplate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '3',
                                    'elution plate')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '4',
                             'Liquid Waste').wells()[0]
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '5',
                            'reagent reservoir 1')
    res2 = ctx.load_labware('nest_1_reservoir_195ml', '6',
                            'reagent reservoir 2')
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                         '200µl filtertiprack')
        for slot in ['7', '8', '9', '10', '11']]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount_m300, tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    deep_blue_lysis_buffer = res1.rows()[0][:1]
    neutralization_buffer = res1.rows()[0][1:5]
    magclearing_beads = res1.rows()[0][5:6]
    magbinding_beads = res1.rows()[0][6:7]
    endo_wash_buffer = res1.rows()[0][7:9]
    elution_buffer = res1.rows()[0][9:10]
    zyppy_wash_buffer = res2.rows()[0][:1]

    num_cols = math.ceil(num_samples/8)
    mag_samples_m = magplate.rows()[0][:num_cols]
    collection_samples = collection_plate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]
    if mag_samples_m[0].width:
        radius = mag_samples_m[0].width/2
    else:
        radius = mag_samples_m[0].diameter/2

    def pick_up(pip=m300):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("\n\n\n\nReplace 200ul filtertipracks before resuming.")
            pip.reset_tipracks()
            pip.pick_up_tip()

    def slow_withdraw(well, pip=m300):
        ctx.max_speeds['A'] = 25
        ctx.max_speeds['Z'] = 25
        pip.move_to(well.top())
        del ctx.max_speeds['A']
        del ctx.max_speeds['Z']

    def remove_supernatant(vol, destinations, z_asp=z_offset, z_disp=None):
        """
        `remove_supernatant` will transfer supernatant from the deepwell
        extraction plate to the liquid waste reservoir.
        :param vol (float): The amount of volume to aspirate from all deepwell
                            sample wells and dispense in the liquid waste.
        :param park (boolean): Whether to pick up sample-corresponding tips
                               in the 'parking rack' or to pick up new tips.
        """

        dest_list = [destinations]*num_cols \
            if type(destinations) != list else destinations

        if not z_disp:
            z_disp = dest_list[0].depth

        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)
        m300.flow_rate.aspirate /= 10
        for m, dest in zip(mag_samples_m, dest_list):
            pick_up()
            for _ in range(num_transfers):
                m300.aspirate(vol_per_transfer, m.bottom(z_asp))
                slow_withdraw(m)
                m300.dispense(vol_per_transfer, dest.bottom(z_disp))
                m300.blow_out(dest.bottom(z_disp))
                slow_withdraw(dest, m300)
            m300.drop_tip()
        m300.flow_rate.aspirate *= 10

    def resuspend(location, reps=mixreps, vol=vol_mix,
                  samples=mag_samples_m, x_mix_fraction=radial_offset_fraction,
                  z_mix=z_offset, dispense_height_rel=8, delay_seconds=0):
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
        ctx.delay(seconds=delay_seconds)
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4

    def lyse_bind_wash(vol, reagent, time_incubation=0,
                       time_settling=0, premix=False,
                       do_discard_supernatant=True, do_resuspend=False,
                       vol_supernatant=0, supernatant_locations=None,
                       resuspension_delay_seconds=0,
                       z_disp_supernatant=None):
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

        columns_per_channel = 12//len(reagent)
        num_transfers = math.ceil(vol/m300.tip_racks[0].wells()[0].max_volume)
        vol_per_transfer = round(vol/num_transfers, 2)

        for i, well in enumerate(mag_samples_m):
            source = reagent[i//columns_per_channel]
            pick_up()
            if premix:
                m300.flow_rate.aspirate *= 4
                m300.flow_rate.dispense *= 4
                for _ in range(5):
                    m300.aspirate(200, source.bottom(0.5))
                    m300.dispense(200, source.bottom(5))
                m300.flow_rate.aspirate /= 4
                m300.flow_rate.dispense /= 4
            for _ in range(num_transfers):
                m300.dispense(m300.current_volume, source.top(-1))
                m300.aspirate(vol_per_transfer, source)
                slow_withdraw(source)
                m300.dispense(vol_per_transfer, well.top(-1))
                m300.blow_out(well.top(-1))
                m300.aspirate(10, well.top(-1))  # avoid droplet

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
            m300.drop_tip()

        if not TEST_MODE_BIND_INCUBATE:
            ctx.delay(minutes=time_incubation,
                      msg=f'Incubating off MagDeck for \
{time_incubation_deep_blue_minutes} minutes.')
        if do_discard_supernatant:
            magdeck.engage(engage_height)
            if not TEST_MODE_BEADS:
                ctx.delay(minutes=time_settling, msg=f'Incubating on \
MagDeck for {time_settling} minutes.')

            remove_supernatant(vol_supernatant,
                               destinations=supernatant_locations)
            magdeck.disengage()

    lyse_bind_wash(vol=100, reagent=deep_blue_lysis_buffer,
                   time_incubation=time_incubation_deep_blue_minutes,
                   do_discard_supernatant=False)
    lyse_bind_wash(vol=450, reagent=neutralization_buffer,
                   do_discard_supernatant=False, resuspension_delay_seconds=5)
    lyse_bind_wash(vol=50, reagent=magclearing_beads, premix=True,
                   do_discard_supernatant=False, resuspension_delay_seconds=5)

    ctx.pause('Centrifuge the extraction plate. Replace on magnetic module \
when finished.')
    magdeck.engage(engage_height)
    ctx.delay(minutes=10, msg='Incubating on MagDeck for 10 minutes.')
    remove_supernatant(vol_cleared_lysate, collection_samples,
                       z_disp=2.0)

    ctx.pause('Discard plate on magnetic module. Move collection plate \
(slot 2) to the magnetic module (slot 1)')

    lyse_bind_wash(30, magbinding_beads, do_resuspend=True, premix=True,
                   do_discard_supernatant=True, vol_supernatant=780,
                   supernatant_locations=waste)
    lyse_bind_wash(200, endo_wash_buffer, do_resuspend=True,
                   time_settling=time_settling_wash_minutes,
                   do_discard_supernatant=True, vol_supernatant=200,
                   supernatant_locations=waste)
    for _ in range(2):
        lyse_bind_wash(400, zyppy_wash_buffer, do_resuspend=True,
                       time_settling=time_settling_wash_minutes,
                       do_discard_supernatant=True, vol_supernatant=400,
                       supernatant_locations=waste)

    ctx.pause('Move the collection plate (slot 1) to a heating block for \
30mins 65C to remove the residual ethanol. Replace the plate onto the \
magnetic module when complete.')

    lyse_bind_wash(vol_elution, elution_buffer,
                   time_incubation=time_incubation_elution_minutes,
                   do_resuspend=True, supernatant_locations=elution_samples_m,
                   time_settling=5.0, vol_supernatant=vol_elution-5.0,
                   z_disp_supernatant=2.0)
