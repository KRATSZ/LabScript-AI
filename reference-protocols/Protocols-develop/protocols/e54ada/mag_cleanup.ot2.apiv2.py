"""OPENTRONS."""
import math
from opentrons import protocol_api
import threading
from time import sleep
from opentrons import types

metadata = {
    'protocolName': '1, Bio-Rad Test Nucleic Acid Purification with PEG',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


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


def run(ctx):
    """PROTOCOL."""
    cancellationToken = CancellationToken()
    TEST_MODE = False
    [num_samp, rxn_vol, bead_ratio, elute_vol,
        m300_mount, well_plate, flash] = get_values(  # noqa: F821
        "num_samp", "rxn_vol", "bead_ratio", "elute_vol",
            "m300_mount", "well_plate", "flash")

    bead_vol = rxn_vol*bead_ratio
    bead_mag_time = 7
    bead_mag_time_elute = 10
    bead_incubate_time = 10
    etoh_dry_time = 10
    elute_time = 7
    elute_rate = 2
    park_cols = math.ceil(num_samp/8)
    if m300_mount == 'left':
        p300_mount = 'right'
    else:
        p300_mount = 'left'

    # load module
    mag_mod = ctx.load_module('magnetic module gen2', 1)
    mag_plate = mag_mod.load_labware(well_plate)
    if well_plate == 'biorad_96_wellplate_200ul_pcr':
        engage_height = 8
        x_abs_move_super = 0.5  # how far left or right during super removal
        z_asp_height = 0.5  # how far above well bottom during super removal
        z_disp_height = -1  # how far below well top during water addition
        width_multiplier = 2  # how far over during water spray down
        etoh_wash_vol = 120
    else:
        engage_height = 5
        x_abs_move_super = 0
        z_asp_height = 1
        z_disp_height = -2  # how far below well top during water addition
        width_multiplier = 3  # how far over during water spray down
        etoh_wash_vol = 200
    mag_mod.disengage()

    # load labware
    elution_plate = ctx.load_labware(well_plate, 10)
    waste_labware = ctx.load_labware('nest_1_reservoir_195ml', 11)

    if num_samp < 7:
        single_mode = True
    else:
        single_mode = False

    if single_mode:
        reagent_rack = ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 6)  # noqa: E501
        # num_tubes = math.ceil(bead_vol*num_samp/1200)
        beads = reagent_rack.wells()[0]
        bead_tube = beads

    reagent_res = ctx.load_labware('nest_12_reservoir_15ml', 3)
    if not single_mode:
        beads = reagent_res.wells()[-1]  # A12

    tipracks = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                for slot in [7, 8, 9, 4, 5]]

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tipracks)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tipracks)

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

    def drop_tip(pip):
        nonlocal tips_dropped
        pip.drop_tip()
        if pip == m300:
            tips_dropped += 8
        else:
            tips_dropped += 1
        if tips_dropped == 288:
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

# Custom Functions

    def bead_mixing(well, pip, mvol, top=5, bottom=1,
                    asp_speed_mod=5, disp_speed_mod=5, reps=10):
        """bead_mixing."""
        """
        'bead_mixing ' will mix liquid that contains beads. This is done by
        aspirating from the middle of the well & dispensing from the bottom to
        mix the beads with the other liquids as much as possible. Aspiration &
        dispensing will also be reversed to ensure proper mixing.
        param well: The current well that the mixing will occur in.
        param pip: The pipet that is currently attached/ being used.
        param mvol: The volume that is transferred before the mixing steps.
        param asp/disp_speed_mod: The speed modulation for aspirations and
        dispenses. 0.5 will divide default volume in half, 2 will double it.
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
            pip.aspirate(vol, well.bottom(bottom))
            pip.dispense(vol, well.bottom(top))
            pip.aspirate(vol, well.bottom(top))
            pip.dispense(vol, well.bottom(bottom))
        pip.flow_rate.aspirate /= asp_speed_mod
        pip.flow_rate.dispense /= disp_speed_mod
        ctx.comment('\n\n')

    def bead_spray_down(pipette, vol, src, well, reps, pip_rate=2):
        """Bead spray down."""
        """This function helps in resuspending beads that have pelleted to the
        sides of the wells. Elution liquid is added to the wells. The liquid is
        then re-aspirated and dispensed down the pelleted bead sides for a
        specified number of repetitions set by 'reps'.
        Pipette, specifies which pipette will be used
        Vol, volume to be aspirated and dispensed
        Src, where the initial liquid will be aspirated from
        Well, destination well for liquid
        Reps, how many times the robot will spray down the sides, reusing the
        initial volume aspirated from the source
        Pip_rate, multiplier of pipette dispense rate. 2 will double default
        dispense rate
        """
        pipette.aspirate(vol, src)
        pipette.move_to(well.top(-1))
        pipette.dispense(vol,
                         well.top().move(types.Point(x=-side*width_multiplier,
                                                     y=0, z=z_disp_height)),
                         rate=pip_rate)
        for _ in range(reps):
            pipette.aspirate(vol*0.9, well)
            pipette.dispense(vol,
                             well.top().move(types.Point(x=-side, y=0,
                                                         z=z_disp_height)),
                             rate=pip_rate)

    # ~~~~~~~~~~~~~~~~~~~~~ MAPPING ~~~~~~~~~~~~~~~~~~~~~
    num_ethanol_wells = math.ceil(num_samp*400/12000)  # /1200 to leave 300ul headroom in tube  # noqa: E501
    ethanol = reagent_res.wells()[:num_ethanol_wells]*num_samp
    waste = waste_labware.wells()[0].top()
    water = reagent_res.wells()[4]

    num_full_col = math.floor(num_samp/8)
    left_over_in_unfilled_col = num_samp % 8
    if left_over_in_unfilled_col > 0 and not single_mode:
        leftover = True
    else:
        leftover = False
    if not single_mode:
        working_cols = mag_plate.rows()[0][:num_full_col]
    else:
        working_cols = mag_plate.rows()[0][:1]

    # ~~~~~~~~~~~~~~~~~~~~~ TIP PARKING LOGIC ~~~~~~~~~~~~~~~~~~
    parking_box = ctx.load_labware('opentrons_96_tiprack_300ul', 2,
                                   'EMPTY TIP RACK')

    park_spots_m = [column for column in parking_box.rows()[0][:park_cols]]
    park_spots_s = [wells for wells in
                    parking_box.columns()[-8][:left_over_in_unfilled_col]]

    # ~~~~~~~~~~~~~~~~~~~~~ ADD BEADS ~~~~~~~~~~~~~~~~~~~~~
    ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING BEADS~~~~~~~~~~~~~~~~\n')
    airgap = 10
    ctx.max_speeds['Z'] = 400
    ctx.max_speeds['A'] = 400
    m300.flow_rate.aspirate = 96
    m300.flow_rate.dispense = 96
    p300.flow_rate.aspirate = 96
    p300.flow_rate.dispense = 96
    supernatant_headspeed_modulator = 10
    bead_rate = 0.2  # bead rate and mix rate will have to be played with
    mix_rate = 0.5  # flow rate for bead_mixing() during bead addition
    magnet_rate = 0.2  # will have to adjust this

    if single_mode:
        for i, well in enumerate(mag_plate.wells()[:num_samp]):
            pick_up(p300)
            if i % 3 == 0:
                bead_mixing(bead_tube, p300, 200, mix_rate, mix_rate, 5)
            # p300.mix(5, 200, bead_tube, rate=mix_rate)
            p300.aspirate(airgap, bead_tube.top())
            p300.aspirate(bead_vol, bead_tube, rate=bead_rate)
            ctx.delay(3)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator*2
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator*2
            p300.move_to(bead_tube.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator*2
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator*2
            p300.aspirate(airgap, bead_tube.top(), rate=bead_rate)
            p300.dispense(airgap, well.top(), rate=bead_rate)
            p300.dispense(bead_vol+airgap, well, rate=bead_rate)
            p300.mix(5, bead_vol+rxn_vol, well, rate=mix_rate)
            # p300.mix(3, bead_vol+rxn_vol, well, rate=mix_rate)
            p300.move_to(well.top())
            p300.blow_out()
            drop_tip(p300)
    else:
        for i, col in enumerate(working_cols):
            pick_up(m300)
            if i % 3 == 0:
                bead_mixing(beads, m300, 200, mix_rate, mix_rate, 5)
            m300.aspirate(airgap, beads.top())
        #     m300.mix(5, 200, beads, rate=mix_rate)
            m300.aspirate(bead_vol, beads, rate=bead_rate)
            ctx.delay(3)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator*2
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator*2
            m300.move_to(beads.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator*2
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator*2
            m300.aspirate(airgap, beads.top(), rate=bead_rate)
            m300.dispense(airgap, col.top(), rate=bead_rate)
            m300.dispense(bead_vol+airgap, col, rate=bead_rate)
        #     bead_mixing(col, m300, bead_vol+rxn_vol, mix_rate, mix_rate, 5)
            m300.mix(5, bead_vol+rxn_vol, col, rate=mix_rate)
            m300.move_to(col.top())
            m300.blow_out()
            drop_tip(m300)
            ctx.comment('\n')

        if leftover:
            ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')
            for well in mag_plate.columns()[num_full_col][:left_over_in_unfilled_col]:  # noqa: E501
                pick_up(p300)
                if i % 3 == 0:
                    bead_mixing(beads, p300, 200, mix_rate, mix_rate, 5)
                # p300.mix(5, 200, bead_tube, rate=mix_rate)
                p300.aspirate(bead_vol, beads, rate=bead_rate)
                ctx.delay(3)
                ctx.max_speeds['Z'] /= supernatant_headspeed_modulator*2
                ctx.max_speeds['A'] /= supernatant_headspeed_modulator*2
                p300.move_to(beads.top())
                ctx.max_speeds['Z'] *= supernatant_headspeed_modulator*2
                ctx.max_speeds['A'] *= supernatant_headspeed_modulator*2
                p300.aspirate(airgap, beads.top(), rate=bead_rate)
                p300.dispense(airgap, well.top(), rate=bead_rate)
                p300.dispense(bead_vol+airgap, well, rate=bead_rate)
                p300.mix(5, bead_vol+rxn_vol, well, rate=mix_rate)
                # p300.mix(3, bead_vol+rxn_vol, well, rate=mix_rate)
                p300.move_to(well.top())
                p300.blow_out()
                drop_tip(p300)

        ctx.comment('\n\n')

    # ~~~~~~~~~~~~~~~~~~~ ENGAGE MAGNETS REMOVE WASTE ~~~~~~~~~~~~~~~~~~~
    ctx.comment('\n\n~~~~~~~~~~~~~~~REMOVING WASTE~~~~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(seconds=bead_incubate_time)
    else:
        ctx.delay(minutes=bead_incubate_time)

    mag_mod.engage(height_from_base=engage_height)

    if TEST_MODE:
        ctx.delay(seconds=bead_mag_time)
    else:
        ctx.delay(minutes=bead_mag_time)

    for i, (col, park_loc_m) in enumerate(zip(working_cols, park_spots_m)):
        side = -x_abs_move_super if i % 2 == 0 else x_abs_move_super
        pick_up(m300)
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(bead_vol+rxn_vol, col.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
        ctx.delay(3)
        m300.move_to(col.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.dispense(bead_vol+rxn_vol, waste)
        m300.blow_out()
        m300.drop_tip(park_loc_m)
        ctx.comment('\n')
    if leftover:
        ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')
        for i, (well, park_loc_s) in enumerate(zip(mag_plate.columns()[num_full_col][:left_over_in_unfilled_col], park_spots_s)):  # noqa: E501
            side = -x_abs_move_super if num_full_col % 2 == 0 else x_abs_move_super  # noqa: E501
            pick_up(p300)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            p300.aspirate(bead_vol+rxn_vol, well.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
            ctx.delay(3)
            p300.move_to(well.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            p300.dispense(bead_vol+rxn_vol, waste)
            p300.blow_out()
            p300.drop_tip(park_loc_s)
            ctx.comment('\n')

    ctx.comment('\n')

    # ~~~~~~~~~~~~~~~~~~~~~ WASH STEPS ~~~~~~~~~~~~~~~~~~~~~
    m300.flow_rate.dispense = 200
    for _ in range(2):

        ctx.comment('\n\n~~~~~~~~~~~~~~~ADDING ETHANOL~~~~~~~~~~~~~~~~\n')
        pick_up(m300)
        for i, col in enumerate(working_cols):
            if i == 0:
                m300.aspirate(20, ethanol[i].top())
            m300.aspirate(etoh_wash_vol, ethanol[i])
            m300.move_to(ethanol[i].top())
            m300.aspirate(20, ethanol[i].top())
            m300.dispense(m300.current_volume, col.top())
            m300.aspirate(20, col.top())
        drop_tip(m300)
        ctx.comment('\n')

        if leftover:
            for park_loc_s in park_spots_s:
                ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')
                pick_up(p300)
                for i, well in enumerate(mag_plate.columns()[num_full_col][:left_over_in_unfilled_col]):  # noqa: E501
                    if i == 0:
                        p300.aspirate(20, ethanol[i].top())
                    p300.aspirate(etoh_wash_vol, ethanol[i+1])
                    p300.move_to(ethanol[i].top())
                    p300.aspirate(20, ethanol[i].top())
                    p300.dispense(p300.current_volume, well.top())
                    p300.aspirate(20, well.top(3))
                drop_tip(p300)
                ctx.comment('\n')
        if TEST_MODE:
            ctx.delay(seconds=2)
        else:
            ctx.delay(minutes=2)  # allows beads to re-pellet to sides
        ctx.comment('\n\n~~~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~~~\n')
        for i, (col, park_loc_m) in enumerate(zip(working_cols, park_spots_m)):
            side = -x_abs_move_super if i % 2 == 0 else x_abs_move_super
            m300.pick_up_tip(park_loc_m)
            m300.move_to(col.top(3))
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(etoh_wash_vol, col.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
            ctx.delay(seconds=3)
            m300.move_to(col.top())
            m300.aspirate(20, col.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.move_to(waste)
            m300.dispense(m300.current_volume, waste)
            m300.aspirate(20, waste)
            m300.move_to(col.top(3))
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(50, col.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
            m300.move_to(col.top(3))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste)
            m300.blow_out()
            if _ == 0:
                m300.drop_tip(park_loc_m)
            else:
                drop_tip(m300)

        if leftover:
            ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')

            for i, (well, park_loc_s) in enumerate(zip(mag_plate.columns()[num_full_col][:left_over_in_unfilled_col], park_spots_s)):  # noqa: E501
                side = -x_abs_move_super if num_full_col % 2 == 0 else x_abs_move_super  # noqa: E501
                p300.pick_up_tip(park_loc_s)
                p300.move_to(well.top(3))
                ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
                ctx.max_speeds['A'] /= supernatant_headspeed_modulator
                p300.aspirate(etoh_wash_vol, well.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
                ctx.delay(seconds=3)
                p300.move_to(well.top(3))
                ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
                ctx.max_speeds['A'] *= supernatant_headspeed_modulator
                p300.dispense(etoh_wash_vol, waste)
                p300.move_to(well.top(3))
                ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
                ctx.max_speeds['A'] /= supernatant_headspeed_modulator
                p300.aspirate(50, well.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
                ctx.delay(seconds=3)
                p300.move_to(well.top(3))
                ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
                ctx.max_speeds['A'] *= supernatant_headspeed_modulator
                p300.dispense(50, waste)
                p300.blow_out()
                if _ == 0:
                    p300.drop_tip(park_loc_s)
                else:
                    drop_tip(p300)
                ctx.comment('\n')

    if TEST_MODE:
        ctx.delay(seconds=etoh_dry_time)
    else:
        ctx.delay(minutes=etoh_dry_time)

    mag_mod.disengage()

    m300.flow_rate.dispense = 94

    ctx.comment('\n\n~~~~~~~~~~~~~~ADDING WATER~~~~~~~~~~~~~~~\n')
    for i, col in enumerate(working_cols):
        side = x_abs_move_super if i % 2 == 0 else -x_abs_move_super
        pick_up(m300)
        bead_spray_down(m300, elute_vol, water, col, 5, pip_rate=elute_rate)
        """m300.aspirate(elute_vol, water)
        m300.dispense(elute_vol, col.top().move(types.Point(x=side, y=0,
                                                z=z_disp_height)),
                      rate=elute_rate)"""
        bead_mixing(col, m300, elute_vol, top=2, bottom=1,
                    asp_speed_mod=5, disp_speed_mod=5, reps=5)
        # m300.mix(10, elute_vol*0.9, col, rate=2)
        m300.blow_out()
        drop_tip(m300)
    ctx.comment('\n')

    if leftover:
        ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')
        for well in mag_plate.columns()[num_full_col][:left_over_in_unfilled_col]:  # noqa: E501
            pick_up(p300)
            bead_spray_down(p300, elute_vol, water, well, 5,
                            pip_rate=elute_rate)
            bead_mixing(well, p300, elute_vol, top=2, bottom=1,
                        asp_speed_mod=5, disp_speed_mod=5, reps=5)
            """p300.mix(10, elute_vol*0.9, well, rate=2)"""
            p300.blow_out()
            ctx.comment('\n')
            drop_tip(p300)

    if TEST_MODE:
        ctx.delay(seconds=elute_time)
    else:
        ctx.delay(minutes=elute_time)

    mag_mod.engage(height_from_base=engage_height)

    if TEST_MODE:
        ctx.delay(seconds=bead_mag_time_elute)
    else:
        ctx.delay(minutes=bead_mag_time_elute)

    ctx.pause('\n~~~~~~PLEASE VISUALLY INSPECT THE MAGNETIC'
              ' MODULE PLATE SEPARATION~~~~~~~~~~~~\n')

    ctx.comment('\n\n~~~~~~~~~~~~~~REMOVING ELUTE~~~~~~~~~~~~~~~\n')
    for i, (s, d) in enumerate(zip(working_cols, elution_plate.rows()[0])):
        side = -x_abs_move_super if i % 2 == 0 else x_abs_move_super
        pick_up(m300)
        m300.move_to(s.top())
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(elute_vol, s.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa: E501
        m300.move_to(s.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.dispense(elute_vol, d)
        m300.blow_out()
        drop_tip(m300)
        ctx.comment('\n')

    if leftover:
        ctx.comment('USING SINGLE CHANNEL FOR UNFILLED COLUMN\n')

        for i, (s, d) in enumerate(zip(mag_plate.columns()[num_full_col][:left_over_in_unfilled_col],  # noqa: E501
                                   elution_plate.columns()[num_full_col][:left_over_in_unfilled_col])):  # noqa: E501
            side = -x_abs_move_super if num_full_col % 2 == 0 else x_abs_move_super  # noqa:E501
            pick_up(p300)
            p300.move_to(s.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            p300.aspirate(elute_vol, s.bottom().move(types.Point(x=side, y=0, z=z_asp_height)), rate=magnet_rate)  # noqa:E501
            p300.move_to(s.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            p300.dispense(elute_vol, d)
            p300.blow_out()
            drop_tip(p300)
            ctx.comment('\n')

    mag_mod.disengage()

    for c in ctx.commands():
        print(c)
    # NOTES:
    """1. aspirating from opposite side of magnetically engaged wells?
            (single vs. multi)
       2. "Wait 10 minutes for beads to completely dry" step??
       3. Four cases: single mode, unfilled columns (num_samp/8 != 0) with
            single mode, unfilled columns (num_samp/8 != 0) in regular mode,
            full columns regular mode"""
