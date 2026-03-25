"""OPENTRONS."""
from opentrons import protocol_api
import math
import threading
from time import sleep
from opentrons import types


metadata = {
    'protocolName': '96 Mag-Bind® Blood & Tissue DNA HDQ 96 Kit',
    'author': 'Opentrons <protocols@opentrons.com>',
    'apiLevel': '2.11'
}

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

    [num_samples, sample_vol, elution_vol,
     flash, p300_mount] = get_values(  # noqa: F821
        'num_samples', 'sample_vol', 'elution_vol',
        'flash', 'p300_mount')

    """
    num_samples = 96
    sample_vol = 560
    elution_vol = 50
    flash = True
    p300_mount = 'left'
    """
    res_type = 'nest_12_reservoir_15ml'
    wash_vol = 600
    bead_delay_time = 5  # minutes real run, seconds for test run
    num_trans_super_1 = math.ceil((sample_vol+420)/180)
    num_trans_super_2 = math.ceil(wash_vol/150)
    """
    Here is where you can modify the magnetic module engage height:
    """
    TEST_MODE = False
    mag_height = 3.5  # From bottom of deep well plate! Default is too high
    supernatant_headspeed_modulator = 10

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck = ctx.load_module('magnetic module gen2', '7')
    magdeck.disengage()
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep',
                                    'deepwell plate')
#    tempdeck = ctx.load_module('Temperature Module Gen2', '1')
#   elutionplate will be random plate from Sanofi on Al block
    elutionplate = ctx.load_labware(
                'thermo_96_aluminumblock_200ul',
                '3')
    waste = ctx.load_labware('nest_1_reservoir_195ml', '4',
                             'Liquid Waste').wells()[0].top()
    res2 = ctx.load_labware(res_type, '2', 'reagent reservoir 2')
    res1 = ctx.load_labware(res_type, '5', 'reagent reservoir 1')
    num_cols = math.ceil(num_samples/8)
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                                '200µl filtertiprack')
               for slot in ['1', '6', '9', '8', '10', '11']]

    parking_spots = [column for column in tips300[0].rows()[0][:num_cols]]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', p300_mount, tip_racks=tips300)

    """
    Here is where you can define the locations of your reagents.
    """
    binding_buffer = res2.wells()[:4]
    elution_solution = res2.wells()[-1]
    wash1 = res1.wells()[:5]  # VHB, first time
    wash2 = res1.wells()[5:10]  # VHB second time
    wash3 = res2.wells()[4:9]  # SPM wash
    wash4 = res2.wells()[9:11] + res1.wells()[10:]  # NFW wash

    # Post-wash wastes
    waste2 = res2.wells()[:4]  # old binding buffer wash wells
    waste3 = res1.wells()[:5]  # Old VHB wash 1 wells
    waste4 = res1.wells()[5:10]  # Old VHB wash 2 wells

    vhb_2_trash = waste2 + waste3

    spm_trash = res1.wells()[2:5] + waste4
    nfw_trash = res1.wells()[8:]
    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]

#    magdeck.disengage()  # just in case
#    tempdeck.set_temperature(4)
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

    m300.flow_rate.aspirate = 150
    m300.flow_rate.dispense = 300
    m300.flow_rate.blow_out = 300

    def bead_mixing(well, pip, mvol, reps=10):
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
        pip.flow_rate.aspirate = 200
        pip.flow_rate.dispense = 300
        for _ in range(reps):
            pip.aspirate(vol, well.bottom(1))
            pip.dispense(vol, well.bottom(5))
            pip.aspirate(vol, well.bottom(5))
            pip.dispense(vol, well.bottom(1))
        pip.flow_rate.aspirate = 150
        pip.flow_rate.aspirate = 300

    # Begin Protocol
    # pre-mix bead/binding buffer mix

    # add binding buffer/bead mix
    ctx.comment('\n\n~~~~~~~~~~~~ADDING BINDING/BUFFER BEAD MIX~~~~~~~~~~~~~\n')  # noqa: E501
    m300.flow_rate.dispense = 60
    pick_up(m300)
    for i, dest in enumerate(mag_samples_m):
        if i % 3 == 0:
            bead_mixing(binding_buffer[i//3], m300, 150, reps=10)
        for _ in range(3):
            if _ == 0:
                m300.aspirate(20, binding_buffer[i//3].top())
            m300.aspirate(140, binding_buffer[i//3])
            m300.dispense(m300.current_volume, dest.top(-2))
            m300.aspirate(20, dest.top(-2))
            m300.move_to(dest.top(2))
    drop_tip(m300)
    m300.flow_rate.dispense = 96
    # Mix 30 seconds, move to next sample 30 seconds mix
    ctx.pause('\n\n~~~~~~~~~~~~MIXING 30 SECONDS~~~~~~~~~~~~~\n')
    for dest in mag_samples_m:
        pick_up(m300)
        bead_mixing(dest, m300, 200, reps=5)
        # for _ in range(8):
        #     m300.aspirate(200, dest)
        #     m300.dispense(200, dest.top(-5))
        drop_tip(m300, home=False)

    # Mag module engage
    ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
    magdeck.engage(height_from_base=mag_height)
    if TEST_MODE:
        ctx.delay(seconds=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    # discard supernatant, Bind buffer wash
    ctx.comment('\n\n~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~\n')
    ctx.max_speeds['Z'] = 400
    ctx.max_speeds['A'] = 400
    m300.flow_rate.aspirate /= 5
    for i, (source, park_loc) in enumerate(zip(mag_samples_m, parking_spots)):
        side = -1 if i % 2 == 0 else 1
        pick_up(m300)
        m300.move_to(source.top())
        for _ in range(num_trans_super_1):
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            if _ == 0:
                m300.aspirate(10, source.top())
            m300.aspirate(
                180, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.2)))
            m300.move_to(source.top())
            m300.air_gap(10)
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste)
            m300.aspirate(10, waste)  # waste defaults to waste.top()
        m300.drop_tip(park_loc)
    m300.flow_rate.aspirate *= 5
    magdeck.disengage()

    # 3 boxes out here? (WE ONLY TRASH 2 THROUGH HERE, MOVE WARNING LOWER)
    # if flash:
    #     if not ctx._hw_manager.hardware.is_simulator:
    #         cancellationToken.set_true()
    #     thread = create_thread(ctx, cancellationToken)
    # m300.home()
    # ctx.pause('Please Empty Trash')
    # ctx.home()  # home before continuing with protocol
    # if flash:
    #     cancellationToken.set_false()  # stop light flashing after home
    #     thread.join()
    # ctx.set_rail_lights(True)

    # Add 600uL VHB Buffer, mix well to resuspend beads
    ctx.comment('\n\n~~~~~~~~~~~~ADDING VHB BUFFER~~~~~~~~~~~~~\n')
    for i, dest in enumerate(mag_samples_m):
        pick_up(m300)
        for num, s in enumerate(wash1):
            if num == 0:
                m300.aspirate(20, s.top())
            m300.aspirate(120, s)
            m300.dispense(m300.current_volume, dest.top(-2))
            m300.aspirate(20, dest.top())
        bead_mixing(dest, m300, 200, reps=5)
        drop_tip(m300)

    # for i, dest in enumerate(mag_samples_m):
    #     m300.pick_up_tip()
    #     for _ in range(4):
    #         if _ == 0:
    #             m300.aspirate(20, wash1[i//3])
    #         m300.aspirate(150, wash1[i//3])
    #         m300.dispense(m300.current_volume, dest.top(-2))
    #         m300.aspirate(20, dest.top())
    #     bead_mixing(dest, m300, 200, reps=5)
    #     m300.drop_tip()

    # engage mag module
    ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
    magdeck.engage(height_from_base=mag_height)
    if TEST_MODE:
        ctx.delay(seconds=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    # discard supernatant, VFB Wash 1
    ctx.comment('\n\n~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~\n')
    m300.flow_rate.aspirate /= 5
    for i, (source, park_loc) in enumerate(zip(mag_samples_m, parking_spots)):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip(park_loc)
        m300.move_to(source.top())
        for _ in range(num_trans_super_2):
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            if _ == 0:
                m300.aspirate(20, source.top())
            m300.aspirate(
                150, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.2)))
            m300.move_to(source.top())
            m300.air_gap(20)
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste)
            m300.aspirate(20, waste)
        m300.drop_tip(park_loc)
    m300.flow_rate.aspirate *= 5
    magdeck.disengage()

    # Empty trash warning? Could possibly be after one more wash? We'll see
    # if flash:
    #     if not ctx._hw_manager.hardware.is_simulator:
    #         cancellationToken.set_true()
    #     thread = create_thread(ctx, cancellationToken)
    # m300.home()
    # ctx.pause('Please Empty Trash')
    # ctx.home()  # home before continuing with protocol
    # if flash:
    #     cancellationToken.set_false()  # stop light flashing after home
    #     thread.join()
    # ctx.set_rail_lights(True)

    # Wash 2, same as above

    # Add 600uL VHB Buffer, mix well to resuspend beads
    ctx.comment('\n\n~~~~~~~~~~~~SECOND VHB BUFFER ADDITION~~~~~~~~~~~~~\n')
    for i, dest in enumerate(mag_samples_m):
        pick_up(m300)
        for _, s in enumerate(wash2):
            if _ == 0:
                m300.aspirate(20, s.top())
            m300.aspirate(120, s)
            m300.dispense(m300.current_volume, dest.top(-2))
            m300.aspirate(20, dest.top())
        bead_mixing(dest, m300, 200, reps=5)
        drop_tip(m300)

    # engage mag module
    ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
    magdeck.engage(height_from_base=mag_height)
    if TEST_MODE:
        ctx.delay(seconds=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    # discard supernatant, VHB 2
    ctx.comment('\n\n~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~\n')
    m300.flow_rate.aspirate /= 5
    for i, (source, park_loc) in enumerate(zip(mag_samples_m, parking_spots)):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip(park_loc)
        m300.move_to(source.top())
        for _ in range(num_trans_super_2):
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            if _ == 0:
                m300.aspirate(20, source.top())
            m300.aspirate(
                150, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.2)))
            m300.move_to(source.top())
            m300.air_gap(20)
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, vhb_2_trash[i//2].top(-3))
            m300.aspirate(20, vhb_2_trash[i//2].top())
        m300.drop_tip(park_loc)
    m300.flow_rate.aspirate *= 5
    magdeck.disengage()

    # SPM Buffer Wash
    ctx.comment('\n\n~~~~~~~~~~~~ADDING SPM BUFFER~~~~~~~~~~~~~\n')
    for i, dest in enumerate(mag_samples_m):
        pick_up(m300)
        for _, s in enumerate(wash3):
            if _ == 0:
                m300.aspirate(20, s.top())
            m300.aspirate(120, s)
            m300.dispense(m300.current_volume, dest.top(-2))
            m300.aspirate(20, dest.top())
        bead_mixing(dest, m300, 200, reps=5)
        drop_tip(m300)

    # engage mag module
    ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
    magdeck.engage(height_from_base=mag_height)
    if TEST_MODE:
        ctx.delay(seconds=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    # discard supernatant, SPM Wash, N.B. Trash tips here
    ctx.comment('\n\n~~~~~~~~~~~~DISCARDING SUPERNATANT~~~~~~~~~~~~~\n')
    m300.flow_rate.aspirate /= 5
    for i, (source, park_loc) in enumerate(zip(mag_samples_m, parking_spots)):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip(park_loc)
        m300.move_to(source.top())
        for _ in range(num_trans_super_2):
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            if _ == 0:
                m300.aspirate(20, source.top())
            m300.aspirate(
                150, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.2)))
            m300.move_to(source.top())
            m300.air_gap(20)
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, spm_trash[i//2].top())
            m300.aspirate(20, spm_trash[i//2].top())
        drop_tip(m300)
    m300.flow_rate.aspirate *= 5

    # N.B. Tips run out here!
    # if flash:
    #     if not ctx._hw_manager.hardware.is_simulator:
    #         cancellationToken.set_true()
    #     thread = create_thread(ctx, cancellationToken)
    # m300.home()
    # ctx.pause('Please Refill Tip Boxes in Slots 1, 6, and 9 then Empty Trash'
    #           'Press Resume When Finished')
    # ctx.home()  # home before continuing with protocol
    # if flash:
    #     cancellationToken.set_false()  # stop light flashing after home
    #     thread.join()
    # ctx.set_rail_lights(True)
    # # ctx.pause()
    # m300.reset_tipracks()

    # NFW wash to remove EtOH twice
    ctx.comment('\n\n~~~~~~~~~~~~NFW WASH~~~~~~~~~~~~~\n')
    for i, dest in enumerate(mag_samples_m):
        side = -1 if i % 2 == 0 else 1
        pick_up(m300)
        ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
        magdeck.engage(height_from_base=mag_height)
        for _ in range(2):
            m300.aspirate(200, wash4[i//3])
            m300.dispense(200, dest.top(-2))
            m300.aspirate(20, dest.top())
            m300.dispense(20, wash4[i//3].top())
        ctx.delay(seconds=20)
        for _ in range(2):
            m300.aspirate(200, dest.bottom().move(types.Point(x=side,
                                                  y=0, z=0.2)))
            m300.dispense(200, nfw_trash[i//4].top())
            m300.aspirate(20, nfw_trash[i//4].top())
            m300.dispense(20, dest.top())
        magdeck.disengage()
        m300.aspirate(20, dest.top())
        m300.drop_tip()
        pick_up(m300)
        m300.aspirate(50, elution_solution)
        m300.dispense(50, dest)
        m300.mix(4, 50, dest)
        drop_tip(m300)

    ctx.comment('\n\n~~~~~~~~~~~~ELUTION INCUBATION~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(seconds=5)
    else:
        ctx.delay(minutes=5)

    # N.B. previous approach to NFW wash
    """for _ in range(2):
        if not m300.has_tip:
            m300.pick_up_tip()
        for i, dest in enumerate(mag_samples_m):
            src = wash3[i//6] if _ == 0 else wash3[(i//6)+2]
            m300.aspirate(200, src)
            m300.dispense(200, dest.top(-2))
        m300.drop_tip()

        for i, (source, park_loc) in enumerate(zip(mag_samples_m, parking_spots)):  # noqa: E501
            side = -1 if i % 2 == 0 else 1
            if not m300.has_tip:
                m300.pick_up_tip(park_loc) if _ == 1 else m300.pick_up_tip()
            m300.move_to(source.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.aspirate(
                200, source.bottom().move(types.Point(x=side,
                                                      y=0, z=0.2)))
            m300.move_to(source.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, waste)
            m300.drop_tip(park_loc, home_after=False)

    magdeck.disengage()

    # Elution buffer addition
    for dest in mag_samples_m:
        m300.pick_up_tip()
        m300.aspirate(50, elution_solution)
        m300.dispense(50, dest)
        bead_mixing(dest, m300, 50, reps=10)
        m300.drop_tip()"""
    ctx.comment('\n\n~~~~~~~~~~~~ENGAGE MAGNETS~~~~~~~~~~~~~\n')
    magdeck.engage(height_from_base=mag_height)

    if TEST_MODE:
        ctx.delay(seconds=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    # Transfer super to 96 well plate
    ctx.comment('\n\n~~~~~~~~~~~~TRANSFERING SUPERNATANT~~~~~~~~~~~~~\n')
    for i, (source, dest) in enumerate(zip(mag_samples_m, elution_samples_m)):
        side = -1 if i % 2 == 0 else 1
        pick_up(m300)
        m300.move_to(source.top())
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(
            elution_vol, source.bottom().move(types.Point(x=side,
                                                          y=0, z=0.2)))
        m300.move_to(source.top())
        m300.aspirate(20, source.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.dispense(20, dest.top())
        m300.dispense(m300.current_volume, dest)
        drop_tip(m300)
