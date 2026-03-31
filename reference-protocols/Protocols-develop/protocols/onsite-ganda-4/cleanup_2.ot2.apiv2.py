"""OPENTRONS."""
import math
from opentrons import types
import threading
from time import sleep

metadata = {
    'protocolName': 'rhAmpSeq Library Prep Part 4 - Cleanup 2',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}

TEST_MODE = False

# Definitions for deck light flashing


class CancellationToken:
    """flash_setup."""

    def __init__(self):
        """init."""
        self.is_continued = False

    def set_true(self):
        """set_true."""
        self.is_continued = True

    def set_false(self):
        """set_false."""
        self.is_continued = False


def turn_on_blinking_notification(hardware, pause):
    """Turn on blinking."""
    while pause.is_continued:
        hardware.set_lights(rails=True)
        sleep(1)
        hardware.set_lights(rails=False)
        sleep(1)


def create_thread(ctx, cancel_token):
    """Create thread."""
    t1 = threading.Thread(target=turn_on_blinking_notification,
                          args=(ctx._hw_manager.hardware, cancel_token))
    t1.start()
    return t1


def run(ctx):
    """PROTOCOL."""
    [
     num_samples, m20_mount, flash
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples", "m20_mount", "flash")

    # define all custo m variables above here with descriptions:
    cancellationToken = CancellationToken()
    # flash = True
    # num_samples, m20_mount = 8, 'right'
    if m20_mount == 'right':
        m300_mount = 'left'
    else:
        m300_mount = 'right'
    num_cols = math.ceil(num_samples/8)
    # num_etoh_wells = math.ceil((0.4*num_samples)/15)
    # m20_speed_mod = 4
    # airgap_library = 5
    etoh_res_vol = 15000
    # load modules
    mag_module = ctx.load_module('magnetic module gen2', '1')

    # load labware
    sample_plate = mag_module.load_labware('nest_96_wellplate'
                                           '_100ul_pcr_full_skirt')
    reagent_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                     '2', 'reagent plate')
    elution_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt',
                                     '5', 'elution plate')
    reagent_resv = ctx.load_labware('nest_12_reservoir_15ml', '4')
    # load tipracks
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul',
                                  str(slot))
                 for slot in [3]]
    tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul',
                                   str(slot))
                  for slot in [7, 8, 10, 11, 9][:math.ceil(num_samples/20)]]
    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', m20_mount, tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', m300_mount,
                               tip_racks=tiprack300)
    # reagents
    sample_plate_dest = sample_plate.rows()[0][:num_cols]
    elution_dest = elution_plate.rows()[0][:num_cols]
    # library_mix = reagent_plate.rows()[0][0]
    # pcr_forward = reagent_plate.rows()[0][1]
    # pcr_reverse = reagent_plate.rows()[0][2]
    beads = reagent_plate.rows()[0][3:6]
    idte = reagent_plate.rows()[0][6:8]
    # well volume tracking is better solution for this
    etoh_1 = reagent_resv.wells()[0]
    etoh_2 = reagent_resv.wells()[1]
    etoh_3 = reagent_resv.wells()[2]
    etoh_4 = reagent_resv.wells()[3]
    liquid_trash_1 = reagent_resv.wells()[8]
    liquid_trash_2 = reagent_resv.wells()[9]
    liquid_trash_3 = reagent_resv.wells()[10]
    liquid_trash_4 = reagent_resv.wells()[11]

    etoh_total = [etoh_1, etoh_2, etoh_3, etoh_4]
    trash_total = [liquid_trash_1, liquid_trash_2, liquid_trash_3,
                   liquid_trash_4]
    etoh_volumes = dict.fromkeys(reagent_resv.wells()[:4], 0)
    # etoh_wash_vol = 200
    supernatant_headspeed_modulator = 5

    def liquid_tracker(vol):
        """liquid_tracker."""
        '''liquid_tracker() will track how much liquid
        was used up per well. If the volume of
        a given well is greater than 'liquid'_res_vol
        it will remove it from the dictionary and iterate
        to the next well which will act as the reservoir.'''
        well = next(iter(etoh_volumes))
        if etoh_volumes[well] > etoh_res_vol:
            del etoh_volumes[well]
            well = next(iter(etoh_volumes))
        etoh_volumes[well] = etoh_volumes[well] + vol
        ctx.comment(f'{int(etoh_volumes[well])} uL of water used from {well}')
        return well

    def bead_mixing(well, pip, mvol, reps=8):
        """bead_mix."""
        """
        'bead_mixing' will mix liquid that contains beads. This will be done by
        aspirating from the bottom of the well and dispensing from the top to
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
            pip.aspirate(vol, well.bottom(1))
            pip.dispense(vol, well.bottom(5))

    # PROTOCOL
    for i, dest in enumerate(sample_plate_dest):
        m300.flow_rate.aspirate /= 4
        m300.flow_rate.dispense /= 4
        m300.pick_up_tip()
        m300.aspirate(20, beads[i//4])
        m300.dispense(20, dest)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        bead_mixing(dest, m300, 20, reps=10)
        m300.flow_rate.aspirate *= 2
        m300.flow_rate.dispense *= 2
        m300.drop_tip()

    if not TEST_MODE:
        ctx.delay(minutes=10, msg='Incubating off magnet')
    mag_module.engage()
    if not TEST_MODE:
        ctx.delay(minutes=5, msg='Incubating on magnet')

    ctx.comment('''discarding supernatant''')
    ctx.max_speeds['Z'] = 50
    ctx.max_speeds['A'] = 50
    for i, source in enumerate(sample_plate_dest):
        side = -1 if i % 2 == 0 else 1
        m300.pick_up_tip()
        m300.flow_rate.aspirate /= 10
        m300.move_to(source.top())
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m300.aspirate(
            40, source.bottom().move(types.Point(x=side*2,
                                                 y=0, z=0.2)))
        m300.move_to(source.top())
        m300.air_gap(20)
        m300.flow_rate.aspirate *= 10
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m300.dispense(m300.current_volume, trash_total[0])
        m300.drop_tip()

    # etoh wash needs the multi-source well function to work!
    ctx.comment("Ethanol Wash")
    num_times = 0
    for _ in range(2):
        m300.pick_up_tip()
        for i, dest in enumerate(sample_plate_dest):
            etoh_source = etoh_total[i//4]
            m300.aspirate(200, etoh_source)
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            m300.move_to(etoh_source.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(200, dest.top(1))
        m300.move_to(etoh_1.top())
        if not TEST_MODE:
            ctx.delay(minutes=1)
        if num_times == 0:
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            m300.home()
            ctx.pause('Please Empty Trash')
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            ctx.pause()
        for i, source in enumerate(sample_plate_dest):
            side = -1 if i % 2 == 0 else 1
            if not m300.has_tip:
                m300.pick_up_tip()
            m300.flow_rate.aspirate /= 5
            m300.move_to(source.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            for asp_num in reversed(range(4)):
                asp_height = source.depth/4*asp_num+0.2
                m300.aspirate(
                    50, source.bottom(asp_height))
            m300.move_to(source.top())
            m300.flow_rate.aspirate *= 5
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            m300.dispense(m300.current_volume, trash_total[i//3])
            m300.drop_tip()
        if num_times == 0:
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            m300.home()
            ctx.pause('Please Empty Trash')
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            ctx.pause()
        num_times += 1

    if not TEST_MODE:
        ctx.delay(minutes=3, msg='Air drying.')
    mag_module.disengage()
    ctx.comment('Adding IDTE')
    for i, dest in enumerate(sample_plate_dest):
        side = 1 if i % 2 == 0 else -1
        bead_loc = dest.bottom().move(types.Point(x=side*2, z=5))
        m300.pick_up_tip()
        m300.aspirate(22, idte[i//6])
        m300.move_to(dest.center())
        m300.dispense(22, bead_loc)
        m300.mix(10, 10, dest.bottom(1))
        m300.move_to(dest.bottom().move(types.Point(x=-2, z=3)))
        m300.drop_tip()

    # ctx.pause("Please vortex and centrifuge sample plate, return to slot 1")

    if not TEST_MODE:
        ctx.delay(minutes=3, msg='Incubating off magnet')
    mag_module.engage()
    if not TEST_MODE:
        ctx.delay(minutes=3, msg='Incubating on magnet')

    m20.flow_rate.aspirate /= 5
    for s, d in zip(sample_plate_dest, elution_dest):
        m20.pick_up_tip()
        m20.move_to(s.top())
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        m20.aspirate(20, s.bottom(0.2))
        m20.move_to(s.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        m20.dispense(m20.current_volume, d.bottom(0.5))
        m20.move_to(d.bottom().move(types.Point(x=-2, z=3)))
        m20.drop_tip()

    mag_module.disengage()
    if flash:
        if not ctx._hw_manager.hardware.is_simulator:
            cancellationToken.set_true()
        thread = create_thread(ctx, cancellationToken)
    m300.home()
    ctx.pause('Protocol Complete.')
    ctx.home()  # home before continuing with protocol
    if flash:
        cancellationToken.set_false()  # stop light flashing after home
        thread.join()
    ctx.pause()

    for c in ctx.commands():
        print(c)
