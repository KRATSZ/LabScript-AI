"""OPENTRONS."""
import math
import threading
from time import sleep
from opentrons import types
from opentrons import protocol_api


metadata = {
    'protocolName': 'SPRI Bead Purification, Size Selection',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.11'
}


"""
Here is where you can modify the magnetic module engage height:
"""
TEST_MODE = False
mag_height = 10  # for custom labware sitting on mag modules
# Definitions for deck light flashing


class CancellationToken:
    """FLASH SETUP."""

    def __init__(self):
        """FLASH SETUP."""
        self.is_continued = False

    def set_true(self):
        """FLASH SETUP."""
        self.is_continued = True

    def set_false(self):
        """FLASH SETUP."""
        self.is_continued = False


def turn_on_blinking_notification(hardware, pause):
    """FLASH SETUP."""
    while pause.is_continued:
        hardware.set_lights(rails=True)
        sleep(1)
        hardware.set_lights(rails=False)
        sleep(1)


def create_thread(ctx, cancel_token):
    """FLASH SETUP."""
    t1 = threading.Thread(target=turn_on_blinking_notification,
                          args=(ctx._hw_manager.hardware, cancel_token))
    t1.start()
    return t1


# Start protocol
def run(ctx):
    """PROTOCOL."""
    # Setup for flashing lights notification to empty trash
    cancellationToken = CancellationToken()

    [num_samples, vol_start, bead_ratio_1, bead_ratio_2,
     vol_trans, air_dry_time, incubation_delay_time, bead_delay_time,
     elution_vol, elution_time, vol_final_plate,
     flash, p300_mount, size_select] = get_values(  # noqa: F821
        'num_samples', 'vol_start', 'bead_ratio_1',
        'bead_ratio_2', 'vol_trans', 'air_dry_time', 'incubation_delay_time',
        'bead_delay_time', 'elution_vol', 'elution_time', 'vol_final_plate',
        'flash', 'p300_mount', 'size_select')

    # Drop Down Variables for Testing
    # num_samples = 96
    # vol_start = 50  # volume of starting well
    # bead_ratio_1 = 0.6  # ratio of SPRI by volume
    # bead_ratio_2 = 0.8
    # vol_trans = 75
    # air_dry_time = 10
    # incubation_delay_time = 5
    # bead_delay_time = 5  # minutes real run, seconds for test run
    # elution_vol = 50
    # elution_time = 10
    # vol_final_plate = 50
    # flash = True
    # p300_mount = 'left'

    # Math and Calculations
    num_cols = math.ceil(num_samples/8)
    vol_bead_add_1 = vol_start*bead_ratio_1
    vol_post_add_1 = vol_bead_add_1+vol_start
    vol_bead_add_2 = (bead_ratio_2*vol_start*(vol_trans/vol_post_add_1))\
        - vol_bead_add_1

    """Above vol_bead_add_2 equation came from Illumina website. Source here:
        https://support.illumina.com/bulletins/2020/07/library-size-selection-
        using-sample-purification-beads.html"""

    # Deprecated calculations below
    # PEG_conc_correction = (vol_trans_post_SPRI_1/vol_total)*bead_ratio
    # PEG_vol_correction = round(PEG_conc_correction*vol_total, 1)

    supernatant_headspeed_modulator = 10
    flow_mod = 0.25
    if p300_mount == 'right':
        p20_mount = 'left'
    else:
        p20_mount = 'right'
    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck_1 = ctx.load_module('magnetic module gen2', '7')
    if size_select:
        magdeck_2 = ctx.load_module('magnetic module gen2', '6')
        magdeck_2.disengage()
        magplate_2 = magdeck_2.load_labware('customadapter_96_wellplate_200ul')
    magdeck_1.disengage()
    magplate_1 = magdeck_1.load_labware('customadapter_96_wellplate_200ul',
                                        'sample plate')
    elutionplate = ctx.load_labware(
                'customadapter_96_wellplate_200ul',
                '3')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '4',
                             'Liquid Waste').wells()[0].top()
    res1 = ctx.load_labware('nest_12_reservoir_15ml', '5',
                            'reagent reservoir 1')
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200µl filtertiprack')
               for slot in ['2', '9', '11']]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                               '20µl filtertiprack')
              for slot in ['1', '8', '10']]

    parking_spots = [column for column in tips300[0].rows()[0][:num_cols]]
    parking_spots_2 = [column for column in tips300[0].rows()[0][:num_cols]]
    """
    Above are the same location purely for clerical reasons to help track open
    tip rack parking spots
    """

    sample_loc_1 = magplate_1.rows()[0][:num_cols]
    if size_select:  # where samples start
        sample_dest_1 = magplate_2.rows()[0][:num_cols]  # first super dest
    sample_dest_2 = elutionplate.rows()[0][:num_cols]  # where final samples go

    bead_well = res1.wells()[0]
    # PEG = res1.wells()[1]
    etoh_1_wells = res1.wells()[1:3]  # 10mL in each, 6 columns each
    etoh_2_wells = res1.wells()[3:5]  # 10mL in each, 6 columns each
    elution_solution = res1.wells()[-1]
    # load pipettes
    m300 = ctx.load_instrument(
        'p300_multi_gen2', p300_mount, tip_racks=tips300)
    m20 = ctx.load_instrument('p20_multi_gen2', p20_mount, tip_racks=tips20)

    # Custom Functions
    def bead_mixing(well, pip, mvol, asp_speed_mod, disp_speed_mod, reps=10):
        """bead_mixing."""
        """
        'bead_mixing' will mix liquid that contains beads. This will be done by
        aspirating from the middle of the well & dispensing from the bottom to
        mix the beads with the other liquids as much as possible. Aspiration &
        dispensing will also be reversed to ensure proper mixing.
        param well: The current well that the mixing will occur in.
        param pip: The pipet that is currently attached/ being used.
        param mvol: The volume that is transferred before the mixing steps.
        param reps: The number of mix repetitions that should occur. Note~
        During each mix rep, there are 2 cycles of aspirating from bottom,
        dispensing at the top and 2 cycles of aspirating from middle,
        dispensing at the bottom
        """
        vol = mvol * .9

        pip.move_to(well.center())
        pip.flow_rate.aspirate *= asp_speed_mod
        pip.flow_rate.dispense *= disp_speed_mod
        for _ in range(reps):
            pip.aspirate(vol, well.bottom(1))
            pip.dispense(vol, well.bottom(5))
            pip.aspirate(vol, well.bottom(5))
            pip.dispense(vol, well.bottom(1))
        pip.flow_rate.aspirate /= asp_speed_mod
        pip.flow_rate.dispense /= disp_speed_mod

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            pip.home()
            ctx.pause('\n\n~~~~~~~~~~~~~~PLEASE REPLACE TIPRACKS~~~~~~~~~~~~~~~\n')  # noqa: E501
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            ctx.set_rail_lights(True)
            pip.reset_tipracks()
            pick_up(pip)

    tips_dropped = 0

    def drop_tip(pip, home=True):
        nonlocal tips_dropped
        pip.drop_tip(home_after=home)
        if pip == m300:
            tips_dropped += 8
        else:
            tips_dropped += 4
        if tips_dropped >= 288:
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            pip.home()
            ctx.pause('\n\n~~~~~~~~~~~~~~PLEASE EMPTY TRASH~~~~~~~~~~~~~~~\n')
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            ctx.set_rail_lights(True)
            tips_dropped = 0

    # Default Values
    ctx.max_speeds['Z'] = 400
    ctx.max_speeds['A'] = 400
    m300.flow_rate.aspirate = 94
    m300.flow_rate.dispense = 94
    m20.flow_rate.aspirate = 7.6
    m20.flow_rate.dispense = 7.6

    # Begin Protocol
    if size_select:
        # bead addition 1
        ctx.comment('\n\n~~~~~~~~~~~~~~BEAD ADDITION 1~~~~~~~~~~~~~~~\n')
        for i, dest in enumerate(sample_loc_1):
            if vol_bead_add_1 > 15:
                pip = m300
                speed_mod = 2.5
            else:
                pip = m20
                speed_mod = 2
            pick_up(pip)
            pip.flow_rate.aspirate *= flow_mod
            pip.flow_rate.dispense *= flow_mod
            if i == 0:
                bead_mixing(bead_well, pip, 20, flow_mod, flow_mod, reps=5)
                pip.aspirate(5, bead_well.top())
            pip.aspirate(vol_bead_add_1, bead_well)
            # pip.move_to(dest.top())
            pip.dispense(pip.current_volume, dest)
            pip.flow_rate.aspirate /= flow_mod
            pip.flow_rate.dispense /= flow_mod
            bead_mixing(dest, pip, vol_bead_add_1, speed_mod,
                        speed_mod, reps=5)
            pip.aspirate(5, dest.top())
            drop_tip(pip)

        # 5 Minute Incubation
        ctx.comment('\n\n~~~~~~~~~~~~~~INCUBATING BEADS~~~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=incubation_delay_time)
        else:
            ctx.delay(minutes=incubation_delay_time)

        # Magnet engage
        ctx.comment('\n\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~~~\n')
        magdeck_1.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Move supernatant to new plate (everything under a certain size)
        ctx.comment('\n\n~~~~~~~~~~~MOVING SUPERNATANT TO SLOT 6~~~~~~~~~~~\n')
        for src, dest in zip(sample_loc_1, sample_dest_1):
            side = -1 if i % 2 == 0 else 1
            pick_up(m300)
            m300.aspirate(10, src.top())  # extra air for full liquid dispense
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_trans,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            m300.aspirate(10, src.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(10, dest.top())
            m300.dispense(m300.current_volume, dest)
            m300.aspirate(20, dest.top())  # suck in droplets before drop_tip
            drop_tip(m300)

        magdeck_1.disengage()
        # samples are now in slot 6's mag plate, aka magdeck_2
        # Add second bead volume (this binds things above a certain size but
        # lower than the previous sizes selected!)
        # bead addition 2
        ctx.comment('\n\n~~~~~~~~~~~~~~BEAD ADDITION 2~~~~~~~~~~~~~~~\n')
        for i, dest in enumerate(sample_dest_1):
            if vol_bead_add_2 > 15:
                pip = m300
                speed_mod = 2.5
            else:
                pip = m20
                speed_mod = 2
            pick_up(pip)
            pip.flow_rate.aspirate *= flow_mod
            pip.flow_rate.dispense *= flow_mod
            if i == 0:
                bead_mixing(bead_well, pip, 20, flow_mod, flow_mod, reps=5)
                pip.aspirate(5, bead_well.top(1))
            pip.aspirate(vol_bead_add_2, bead_well)
            pip.dispense(pip.current_volume, dest)
            pip.flow_rate.aspirate /= flow_mod
            pip.flow_rate.dispense /= flow_mod
            bead_mixing(dest, pip, vol_bead_add_2,
                        speed_mod, speed_mod, reps=5)
            pip.aspirate(5, dest.top())
            drop_tip(pip)

        # 5 minute incubation for the new beads to help out
        ctx.comment('\n\n~~~~~~~~~~~~~~INCUBATING BEADS~~~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=incubation_delay_time)
        else:
            ctx.delay(minutes=incubation_delay_time)

        # Engage magnet 2
        ctx.comment('\n\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~~~\n')
        magdeck_2.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Trash Super, leaves the bead-bound base pairs for specific size range
        ctx.comment('\n\n~~~~~~~~~~~MOVING SUPERNATANT TO TRASH~~~~~~~~~~~~\n')
        for src in sample_dest_1:
            side = -1 if i % 2 == 0 else 1
            pick_up(m300)
            m300.aspirate(10, src.top())  # extra air for full dispense
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_trans+vol_bead_add_2,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            m300.aspirate(10, src.top())  # air gap
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(10, waste)
            m300.dispense(m300.current_volume, dest)
            m300.aspirate(20, waste)  # suck in droplets before drop_tip
            drop_tip(m300)
        magdeck_2.disengage()

        # EtOH Wash 1
        ctx.comment('\n\n~~~~~~~~~~~~ETHANOL WASH 1~~~~~~~~~~~~~\n')
        for i, (dest, park_loc) in enumerate(zip(sample_dest_1,
                                                 parking_spots)):
            pick_up(m300)
            m300.aspirate(200, etoh_1_wells[i//6])
            m300.dispense(200, dest.top(-1))
            m300.drop_tip(park_loc)

        # Mag 2 Engage
        ctx.comment('\n\n~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
        magdeck_2.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Remove EtOH wash 1
        ctx.comment('\n\n~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~\n')
        for src, park_loc in zip(sample_dest_1, parking_spots):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(200,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(200, waste)
            m300.aspirate(20, waste)  # suck in droplets before drop_tip
            m300.drop_tip(park_loc)

        magdeck_2.disengage()

        # EtOH wash 2
        ctx.comment('\n\n~~~~~~~~~~~~ETHANOL WASH 2~~~~~~~~~~~~~\n')
        for i, (dest, park_loc) in enumerate(zip(sample_dest_1,
                                                 parking_spots)):
            m300.pick_up_tip(park_loc)
            m300.aspirate(200, etoh_2_wells[i//6])
            m300.dispense(200, dest.top(-1))
            m300.drop_tip(park_loc)

        ctx.comment('\n\n~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
        magdeck_2.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Remove EtOH wash 2
        ctx.comment('\n\n~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~\n')
        for src, park_loc in zip(sample_dest_1, parking_spots):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(200,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(200, waste)
            m300.aspirate(20, waste)  # suck in droplets before drop_tip
            drop_tip(m300)

        magdeck_2.disengage()
        # Air dry
        ctx.comment('\n\n~~~~~~~~~~~~AIR DRYING BEADS~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=air_dry_time)
        else:
            ctx.delay(minutes=air_dry_time)

        # Elute from beads!
        ctx.comment('\n\n~~~~~~~~~~~~ADDING ELUTION SOLUTION~~~~~~~~~~~~~\n')
        for dest, park_loc in zip(sample_dest_1, parking_spots_2):
            pick_up(m300)
            m300.aspirate(elution_vol, elution_solution)
            m300.dispense(m300.current_volume, dest)
            bead_mixing(dest, m300, 50, 2.5, 2.5, reps=5)
            m300.aspirate(20, dest.top())
            m300.drop_tip(park_loc)
        ctx.comment('\n\n~~~~~~~~~INCUBATING WITH ELUTION SOLUTION~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=elution_time)
        else:
            ctx.delay(minutes=elution_time)

        # Mag deck 2 engage
        magdeck_2.engage(height_from_base=mag_height)
        ctx.comment('\n\n~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # move elution solution to new, final plate
        ctx.comment('\n\n~~~~~~~~~~~~MOVING ELUTIONS TO SLOT 3~~~~~~~~~~~~~\n')
        for src, dest, park_loc in zip(sample_dest_1, sample_dest_2,
                                       parking_spots_2):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_final_plate,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, dest)
            m300.aspirate(20, dest)  # suck in droplets before drop_tip
            drop_tip(m300)

    else:
        # single purification
        # bead addition
        ctx.comment('\n\n~~~~~~~~~~~~~~BEAD ADDITION~~~~~~~~~~~~~~~\n')
        for i, dest in enumerate(sample_loc_1):
            if vol_bead_add_1 > 15:
                pip = m300
                speed_mod = 2.5
            else:
                pip = m20
                speed_mod = 2
            pick_up(pip)
            pip.flow_rate.aspirate *= flow_mod
            pip.flow_rate.dispense *= flow_mod
            if i == 0:
                bead_mixing(bead_well, pip, 22, flow_mod, flow_mod, reps=5)
                pip.aspirate(5, bead_well.top())
            pip.aspirate(vol_bead_add_1, bead_well)
            # pip.move_to(dest.top())
            pip.dispense(pip.current_volume, dest)
            pip.flow_rate.aspirate /= flow_mod
            pip.flow_rate.dispense /= flow_mod
            bead_mixing(dest, pip, vol_bead_add_1, speed_mod,
                        speed_mod, reps=5)
            pip.aspirate(5, dest.top())
            drop_tip(pip)

        # 5 Minute Incubation
        ctx.comment('\n\n~~~~~~~~~~~~~~INCUBATING BEADS~~~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=incubation_delay_time)
        else:
            ctx.delay(minutes=incubation_delay_time)

        # Magnet engage
        ctx.comment('\n\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~~~\n')
        magdeck_1.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)
        # Move supernatant to trash
        ctx.comment('\n\n~~~~~~~~~~~~REMOVING SUPERNATANT~~~~~~~~~~~~~\n')
        for src in sample_loc_1:
            side = -1 if i % 2 == 0 else 1
            pick_up(m300)
            m300.aspirate(10, src.top())  # extra air for full liquid dispense
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_trans,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            m300.aspirate(10, src.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(10, waste)
            m300.dispense(m300.current_volume, dest)
            m300.aspirate(20, dest.top())  # suck in droplets before drop_tip
            drop_tip(m300)

        # EtOH Wash 1
        ctx.comment('\n\n~~~~~~~~~~~~ETHANOL WASH 1~~~~~~~~~~~~~\n')
        for i, (dest, park_loc) in enumerate(zip(sample_loc_1,
                                                 parking_spots)):
            pick_up(m300)
            m300.aspirate(200, etoh_1_wells[i//6])
            m300.dispense(200, dest.top(-1))
            m300.drop_tip(park_loc)

        # Mag 2 Engage
        ctx.comment('\n\n~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
        magdeck_1.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Remove EtOH wash 1
        ctx.comment('\n\n~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~\n')
        for src, park_loc in zip(sample_loc_1, parking_spots):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(200,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(200, waste)
            m300.aspirate(20, waste)  # suck in droplets before drop_tip
            m300.drop_tip(park_loc)

        magdeck_1.disengage()

        # EtOH wash 2
        ctx.comment('\n\n~~~~~~~~~~~~ETHANOL WASH 2~~~~~~~~~~~~~\n')
        for i, (dest, park_loc) in enumerate(zip(sample_loc_1,
                                                 parking_spots)):
            m300.pick_up_tip(park_loc)
            m300.aspirate(200, etoh_2_wells[i//6])
            m300.dispense(200, dest.top(-1))
            m300.drop_tip(park_loc)

        ctx.comment('\n\n~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
        magdeck_1.engage(height_from_base=mag_height)
        if TEST_MODE:
            ctx.delay(seconds=bead_delay_time)
        else:
            ctx.delay(minutes=bead_delay_time)

        # Remove EtOH wash 2
        ctx.comment('\n\n~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~\n')
        for src, park_loc in zip(sample_loc_1, parking_spots):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(200,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(200, waste)
            m300.aspirate(20, waste)  # suck in droplets before drop_tip
            drop_tip(m300)

        magdeck_1.disengage()
        # Air dry
        ctx.comment('\n\n~~~~~~~~~~~~AIR DRYING BEADS~~~~~~~~~~~~~\n')
        if TEST_MODE:
            ctx.delay(seconds=air_dry_time)
        else:
            ctx.delay(minutes=air_dry_time)

        # move elution solution to new, final plate
        ctx.comment('\n\n~~~~~~~~~~~~MOVING ELUTIONS TO SLOT 3~~~~~~~~~~~~~\n')
        for src, dest, park_loc in zip(sample_loc_1, sample_dest_2,
                                       parking_spots_2):
            side = -1 if i % 2 == 0 else 1
            m300.pick_up_tip(park_loc)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(vol_final_plate,
                          src.bottom().move(types.Point(x=side,
                                                        y=0, z=0.2)))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, dest)
            m300.aspirate(20, dest)  # suck in droplets before drop_tip
            drop_tip(m300)

    for c in ctx.commands():
        print(c)
