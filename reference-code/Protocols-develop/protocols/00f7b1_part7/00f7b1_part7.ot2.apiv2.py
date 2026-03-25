"""OPENTRONS."""
from opentrons import protocol_api
import math
import threading
from time import sleep

metadata = {
    'protocolName': 'NEBNext Ultra II Directional RNA Library Prep Kit for \
Illumina Part 7: Adaptor Ligation',
    'author': 'John C. Lynch <john.lynch@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
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


def run(ctx: protocol_api.ProtocolContext):
    """PROTOCOLS."""
    [
     num_samples,
     m300_mount, flash
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples", "m300_mount", "flash")

    TEST_MODE = False
    bead_delay_time = 2
    wash_delay_time = 2
    supernatant_headspeed_modulator = 10
    mag_height = 3.5
    print(bead_delay_time, wash_delay_time, supernatant_headspeed_modulator,
          mag_height)
    ctx.max_speeds['Z'] = 125
    ctx.max_speeds['A'] = 125
    # Setup for flashing lights notification to empty trash
    cancellationToken = CancellationToken()

    # define all custom variables above here with descriptions:
    num_columns = math.ceil(num_samples/8)
    if m300_mount == 'right':
        m20_mount = 'left'
    else:
        m20_mount = 'right'
    # load modules
    mag_deck = ctx.load_module('magnetic module gen2', '1')
    temp_deck = ctx.load_module('temperature module gen2', '3')
    print(num_columns)

    if not TEST_MODE:
        temp_deck.set_temperature(4)

    # load labware
    mag_plate = mag_deck.load_labware('thermofisher_96_wellplate_200ul')
    temp_plate = temp_deck.load_labware('opentrons_96_aluminumblock_generic_'
                                        'pcr_strip_200ul')
    # dwp = ctx.load_labware('nest_96_wellplate_2ml_deep', '4')
    # final_plate = ctx.load_labware('thermofisher_96_wellplate_200ul', '2')
    trash = ctx.load_labware('nest_1_reservoir_195ml', '9').wells()[0].top()
    print(trash)
    # load tipracks

    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
               for slot in ['10', '7', '6']]
    tips20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['11']]
    # load instrument

    m300 = ctx.load_instrument(
        'p300_multi_gen2', m300_mount, tip_racks=tips300)

    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tips20)

    # pipette functions   # INCLUDE ANY BINDING TO CLASS

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
            tips_dropped += 3
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
        for _ in range(reps):
            pip.aspirate(vol, well.bottom(1), rate=2)
            pip.dispense(vol, well.bottom(5), rate=2)
            pip.aspirate(vol, well.bottom(5), rate=2)
            pip.dispense(vol, well.bottom(1), rate=2)
    # reagents

    samples = mag_plate.rows()[0][:num_columns]
    dil_adapter = temp_plate.rows()[0][0]
    mm_ligation = temp_plate.rows()[0][2:2+math.ceil(num_columns/6)]*12
    user_enzyme = temp_plate.rows()[0][5]

    # protocol
    ctx.comment('\n~~~~~~~~~~~ADDING DILUTED ADAPTER~~~~~~~~~~~\n')
    for dest in samples:
        pick_up(m20)
        m20.aspirate(2.5, dil_adapter, rate=0.2)
        m20.dispense(2.5, dest, rate=0.2)
        drop_tip(m20)

    ctx.comment('\n~~~~~~~~~~ADDING LIGATION ENHANCER/MASTER MIX~~~~~~~~~~~\n')
    for src, dest in zip(mm_ligation, samples):
        pick_up(m300)
        m300.aspirate(31, src, rate=0.2)
        ctx.delay(seconds=2)
        m300.dispense(31, dest, rate=0.2)
        ctx.delay(seconds=2)
        m300.mix(8, 70, dest)
        ctx.delay(seconds=2)
        m300.move_to(dest.top())
        m300.aspirate(20, dest.top(2))
        drop_tip(m300)

    if flash:
        if not ctx._hw_manager.hardware.is_simulator:
            cancellationToken.set_true()
        thread = create_thread(ctx, cancellationToken)
    m300.home()
    ctx.pause('\n\nMOVE PLATE IN SLOT 1 TO OFF-DECK THERMOCYCLER\n'
              'REFER TO 1.7.4 FOR SPECIFIC HEATING/COOLING CYCLE\n'
              'SPIN PLATE DOWN BEFORE RETURNING TO DECK\n'
              'RETURN PLATE TO SLOT 1 WHEN FINISHED\n\n')
    ctx.home()  # home before continuing with protocol
    if flash:
        cancellationToken.set_false()  # stop light flashing after home
        thread.join()
    ctx.set_rail_lights(True)

    ctx.comment('\n~~~~~~~~~~~ADDING USER ENZYME~~~~~~~~~~~\n')
    for dest in samples:
        pick_up(m20)
        pick_up(m300)
        m20.aspirate(3, user_enzyme, rate=0.2)
        ctx.delay(seconds=1)
        m20.dispense(3, dest, rate=0.2)
        m300.mix(6, 70, dest)
        drop_tip(m300)
        drop_tip(m20)

    if flash:
        if not ctx._hw_manager.hardware.is_simulator:
            cancellationToken.set_true()
        thread = create_thread(ctx, cancellationToken)
    m300.home()
    ctx.pause('\n\n~~~~~~~~~~~~~~PROTOCOL  COMPLETE~~~~~~~~~~~~~~~\n')
    ctx.home()  # home before continuing with protocol
    if flash:
        cancellationToken.set_false()  # stop light flashing after home
        thread.join()
    ctx.set_rail_lights(True)

    for c in ctx.commands():
        print(c)
