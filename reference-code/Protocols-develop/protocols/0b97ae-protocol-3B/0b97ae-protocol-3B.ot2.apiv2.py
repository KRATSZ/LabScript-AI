# flake8: noqa


"""OPENTRONS."""
from opentrons import protocol_api
import math
import threading
from time import sleep
from opentrons import types

metadata = {
    'protocolName': 'QIAseq FastSelect Extraction',
    'author': 'Trevor <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.13'  # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
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
     num_samples, vol_dna , flash, bead_timer, reservoir, F_Plate, D_Plate, R_Plate] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples","vol_dna","flash","bead_timer","reservoir","final_plate","dilution_plate","reagent_plate")
    num_samples = int(num_samples)
    if reservoir == 'perkinelmer':
        res_labware = 'perkinelmer_12_reservoir_21000ul'
    else:
        res_labware = 'nest_12_reservoir_15ml'

    if F_Plate == 'Biorad':
        F_labware = 'opentrons_96_aluminumblock_biorad_wellplate_200ul'
    else:
        F_labware = 'appliedbiosystemsenduraplate_96_aluminumblock_220ul'

    if D_Plate == 'Biorad':
        D_labware = 'opentrons_96_aluminumblock_biorad_wellplate_200ul'
    else:
        D_labware = 'appliedbiosystemsenduraplate_96_aluminumblock_220ul'
    
    if R_Plate == 'Biorad':
        R_labware = 'biorad_96_wellplate_200ul_pcr'
    else:
        R_labware = 'appliedbiosystemsenduraplate_96_aluminumblock_220ul'

    'Global variables'
    TEST_MODE = False
    bead_delay_time_1 = 2
    bead_delay_time = 5
    wash_delay_time = 10
    supernatant_headspeed_modulator = 10
    mag_height = 3.5
    air_dry_time = bead_timer
    ctx.max_speeds['Z'] = 125
    ctx.max_speeds['A'] = 125
    # Setup for flashing lights notification to empty trash
    cancellationToken = CancellationToken()

    # define all custom variables above here with descriptions:
    num_columns = math.ceil(num_samples/8)

    # load modules
    tempdeck_1 = ctx.load_module('temperature module gen2', '10')
    tempdeck_1.set_temperature(4)
    tempdeck_2 = ctx.load_module('temperature module gen2', '7')
    tempdeck_2.set_temperature(4)
    Mag_mod = ctx.load_module('magnetic module gen2', '4')
    Mag_mod.disengage()

    # load labware
    mag_plate = Mag_mod.load_labware('nest_96_wellplate_2ml_deep','Extraction Plate')
    final_plate = tempdeck_1.load_labware(F_labware, #noqa: E501
                                       'Reagent Plate')
    Diluted_plate = tempdeck_2.load_labware(D_labware,  # noqa: E501
                                            'Diluted RNA plate')
    water_res = ctx.load_labware(res_labware, 2,
                                 'Water reservoir')
    Reagent_plate = ctx.load_labware(R_labware, '1')

    # load tipracks
    tips3 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
               for slot in ['8', '9', '11']]
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
              for slot in ['3', '5', '6']]
    # load instrument

    p20 = ctx.load_instrument('p20_multi_gen2', 'left',
                                  tip_racks=tips)
    p300 = ctx.load_instrument('p300_multi_gen2', 'right',
                                   tip_racks=tips3)

    # reagents
    samples_start = Diluted_plate.rows()[0][:num_columns]
    samples_mag = mag_plate.rows()[0][:num_columns]
    etoh = water_res.rows()[0][2]
    etoh_1 = water_res.rows()[0][3]
    final_dest = final_plate.rows()[0][:num_columns]
    water_1 = water_res.rows()[0][0]
    bb = water_res.rows()[0][1]
    bb = water_res.rows()[0][1]
    Removal_Trash_1 = water_res.rows()[0][9]
    Removal_Trash_2 = water_res.rows()[0][10]
    Removal_Trash_3 = water_res.rows()[0][11]
    mm_1 = Reagent_plate.rows()[0][0]
    beads = Reagent_plate.rows()[0][0]

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
        if pip == p300:
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

    # protocol
    ctx.comment('\n~~~~~~~~~~~~~~ADDING SAMPLES TO MAG PLATE~~~~~~~~~~~~~~\n')
    for s, d in zip(samples_start, samples_mag):
        pick_up(p20)
        p20.aspirate(vol_dna, s)
        p20.dispense(vol_dna, d)
        drop_tip(p20)

    ctx.comment('\n~~~~~~~~~~~~~~ADDING BEADS TO SAMPLES~~~~~~~~~~~~~~\n')
    for i, dest in enumerate(samples_mag):
        pick_up(p20)
        if i % 3 == 0:
            bead_mixing(beads, p20, 15)
        p20.aspirate(19.5, beads, rate=0.5)
        ctx.delay(seconds=1)
        ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
        ctx.max_speeds['A'] /= supernatant_headspeed_modulator
        p20.move_to(beads.top())
        ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
        ctx.max_speeds['A'] *= supernatant_headspeed_modulator
        p20.dispense(19.5, dest, rate=0.5)
        bead_mixing(dest, p20, 15, reps=6)
        p20.blow_out(dest.bottom(20))
        p20.aspirate(1, dest.top())
        ctx.delay(seconds=10)
        p20.aspirate(1, dest.top())
        drop_tip(p20)

    ctx.pause('Remove Plate and Centrifuge, place back on deck at site 4, on the magnetic module')
    ctx.comment('\n~~~~~~~~~~~~~~INCUBATING SAMPLES WITH BEADS~~~~~~~~~~~~~\n')

    Mag_mod.engage(height_from_base=mag_height)
    ctx.comment('\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(minutes=bead_delay_time_1)
    else:
        ctx.delay(minutes=bead_delay_time_1)

    ctx.comment('\n~~~~~~~~~~~~~~REMOVING SUPERNATANT~~~~~~~~~~~~~\n')
    for i, dest in enumerate(samples_mag):
        side = -1 if i % 2 == 0 else 1
        pick_up(p20)
        for _ in range(2):

            p20.move_to(dest.top())
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            p20.aspirate(9.75, dest.bottom().move(types.Point(x=side,
                                                              y=0, z=1)),
                         rate=0.1)
            ctx.delay(seconds=1)
            p20.move_to(dest.top())
            p20.aspirate(1.5, dest.top())
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            p20.dispense(p20.current_volume, Removal_Trash_1)
            p20.blow_out()
            p20.air_gap(1)
            ctx.delay(seconds=10)
            p20.air_gap(1)
        drop_tip(p20)

    ctx.comment('\n~~~~~~~~~~~~~~ADDING Water TO SAMPLES~~~~~~~~~~~~~~\n')
    pick_up(p20)
    for i, dest in enumerate(samples_mag):
        p20.aspirate(15, water_1)
        p20.dispense(15, dest.top())
    drop_tip(p20)

    ctx.comment('\n~~~ADDING QIAseq Bead Binding Buffer TO SAMPLES~~~~~~~\n')
    for i, dest in enumerate(samples_mag):
        pick_up(p20)
        p20.aspirate(19.5, bb)
        p20.dispense(19.5, dest)
        p20.mix(3, 17, dest)
        drop_tip(p20)

    ctx.pause('''
                Remove Plate and Centrifuge, place back on deck at site 4,
                on the magnetic module''')
    ctx.comment('\n~~~~~~~~~~~~~~INCUBATING SAMPLES~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(seconds=5)
    else:
        ctx.delay(minutes=5)

    Mag_mod.engage(height_from_base=mag_height)
    ctx.comment('\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(minutes=bead_delay_time_1)
    else:
        ctx.delay(minutes=bead_delay_time_1)

    ctx.comment('\n~~~~~~~~~~~~~~WASHING TWICE WITH ETHANOL~~~~~~~~~~~~~\n')
    for _ in range(2):
        pick_up(p300)
        ctx.comment('\n~~~~~~~~~~~~~~ADDING ETHANOL~~~~~~~~~~~~~\n')
        if _ > 0:
            for i, dest in enumerate(samples_mag):
                p300.mix(1, 150, etoh_1)
                p300.aspirate(210, etoh_1)
                p300.dispense(200, dest.top())
                p300.aspirate(20, dest.top())
                p300.dispense(30, etoh_1.top())
        else:
            for i, dest in enumerate(samples_mag):
                p300.mix(1, 150, etoh)
                p300.aspirate(210, etoh)
                p300.dispense(200, dest.top())
                p300.aspirate(20, dest.top())
                p300.dispense(30, etoh.top())

        ctx.delay(seconds=30)
        ctx.comment('\n~~~~~~~~~~~~~~REMOVING ETHANOL~~~~~~~~~~~~~\n')
        for i, dest in enumerate(samples_mag):
            side = -1 if i % 2 == 0 else 1
            if i > 0:
                pick_up(p300)
            p300.move_to(dest.top(2))
            ctx.max_speeds['Z'] /= supernatant_headspeed_modulator
            ctx.max_speeds['A'] /= supernatant_headspeed_modulator
            p300.aspirate(200, dest.bottom().move(types.Point(x=side,
                                                              y=0, z=1)),
                          rate=0.1)
            p300.move_to(dest.top(2))
            ctx.max_speeds['Z'] *= supernatant_headspeed_modulator
            ctx.max_speeds['A'] *= supernatant_headspeed_modulator
            if i > 5:
                p300.dispense(200, Removal_Trash_3)
            else:
                p300.dispense(200, Removal_Trash_2)
            drop_tip(p300)
        if _ == 1:
            for i, dest in enumerate(samples_mag):
                pick_up(p20)
                p20.aspirate(10, dest.bottom(0.25), rate=.1)
                p20.aspirate(2, dest.top())
                if i > 5:
                    p20.dispense(p20.current_volume, Removal_Trash_3)
                    p20.aspirate(10, Removal_Trash_3)
                else:
                    p20.dispense(p20.current_volume, Removal_Trash_2)
                    p20.aspirate(10, Removal_Trash_2)
                p20.drop_tip()

    ctx.comment('\n~~~~~~~~~~~~~~AIR DRY BEADS FOR 5 MINUTES~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(minutes=air_dry_time)
    else:
        ctx.delay(minutes=air_dry_time)

    Mag_mod.disengage()

    ctx.pause('''
                Remove Plate and inspect pellet to confirm it is completely
                 dry, place back on deck at site 4, on the magnetic module
                 ''')

    ctx.comment('\n~~~~~~~~~~~~~ELUTING WITH Nucleas-free Water~~~~~~~~~~~\n')
    for i, dest in enumerate(samples_mag):
        pick_up(p20)
        p20.aspirate(16, water_1)
        p20.dispense(16, dest)
        bead_mixing(dest, p20, 17)
        p20.blow_out(dest.top())
        p20.air_gap(1)
        drop_tip(p20)

    ctx.comment('\n~~~~~~~~~~~~~~ELUTING FOR 2 MINUTES~~~~~~~~~~~~~\n')
    if TEST_MODE:
        ctx.delay(seconds=2)
    else:
        ctx.delay(minutes=2)

    ctx.comment('\n~~~~~~~~~~~~~~SEPARATING BEADS~~~~~~~~~~~~~\n')
    Mag_mod.engage(height_from_base=mag_height)
    if TEST_MODE:
        ctx.delay(minutes=bead_delay_time)
    else:
        ctx.delay(minutes=bead_delay_time)

    ctx.comment('\n~~~~~~~~~~~~~~MOVING cDNA TO FINAL PLATE~~~~~~~~~~~~~\n')

    for s, d in zip(samples_mag, final_dest):
        pick_up(p20)
        p20.aspirate(14, s.bottom().move(types.Point(x=0, y=0, z=0.7)),
                     rate=0.1)
        p20.dispense(14, d)
        drop_tip(p20)

    # ctx.comment('\n~~~~~~~~~~~~~~FIRST STRAND SYNTHESIS SETUP~~~~~~~~~~~~~\n')
    # for i, dest in enumerate(final_dest):
    #     pick_up(p20)
    #     p20.aspirate(11, mm_1)
    #     p20.dispense(11, dest.top())
    #     bead_mixing(dest, p20, 19)
    #     p20.blow_out(dest.top())
    #     p20.air_gap(1)
    #     drop_tip(p20)

    if flash:
        if not ctx._hw_manager.hardware.is_simulator:
            cancellationToken.set_true()
        thread = create_thread(ctx, cancellationToken)
    p20.home()
    ctx.pause('\n\n~~~~~~~~~~~~~~PROTOCOL  COMPLETE~~~~~~~~~~~~~~~\n')
    ctx.home()  # home before continuing with protocol
    Mag_mod.disengage()
    tempdeck_1.deactivate()
    tempdeck_2.deactivate()
    if flash:
        cancellationToken.set_false()
        thread.join()
    ctx.set_rail_lights(True)
