from opentrons import protocol_api
from opentrons.protocol_api.contexts import InstrumentContext
from opentrons.protocol_api.labware import Well, Labware
from opentrons.types import Point
import math

metadata = {
    'protocolName': '357404: Slide sample antibody staining',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    [n_slots,
     n_last_samples,
     vol_reagent,
     dispense_steps,
     is_start_after_1st_incbn,
     is_stop_after_1st_incbn,
     tuberack_lname,
     pipette_offset,
     is_dry_run,
     t_per_block,
     is_multi_disp_reags,
     is_reuse_reag_tips,
     is_reuse_wash_tips,
     temp_mod_lname,
     p1000_slot,
     well_edge_offset,
     is_use_custom_block,
     custom_labware_lname] = get_values(  # noqa: F821
     "n_slots",
     "n_last_samples",
     "vol_reagent",
     "dispense_steps",
     "is_start_after_1st_incbn",
     "is_stop_after_1st_incbn",
     "tuberack_lname",
     "pipette_offset",
     "is_dry_run",
     "t_per_block",
     "is_multi_disp_reags",
     "is_reuse_reag_tips",
     "is_reuse_wash_tips",
     "temp_mod_lname",
     "p1000_slot",
     "well_edge_offset",
     "is_use_custom_block",
     "custom_labware_lname")

    # Definitions for loading labware, tipracks and pipettes.
    slide_block_lname = (custom_labware_lname if is_use_custom_block
                         else 'customslideblockv2_8_wellplate')
    slide_blocks_loader = {'lname': slide_block_lname,
                           'slots': [1, 4, 5, 7, 8, 9, 10, 11]}
    tuberack_slot = '3'
    temp_mod_loader = {'lname': temp_mod_lname, 'slot': tuberack_slot}
    reservoir_loader = {'lname': 'agilent_1_reservoir_290ml', 'slot': '2'}
    # The tuberack is loaded on temperature module
    tuberack_loader = {'lname': tuberack_lname, 'slot': tuberack_slot}

    tiprack_1000_loader = {'lname': 'opentrons_96_tiprack_1000ul',
                           'slots': ['6']}
    p1000_loader = {'lname': 'p1000_single_gen2', 'mount': p1000_slot}

    verbose = False

    if temp_mod_lname and 'Aluminum' not in tuberack_lname:
        raise Exception("You must select an aluminum block tuberack when "
                        "using the temperature module, you selected {}"
                        .format(tuberack_lname))

    if not 0 < n_slots < 9:
        raise Exception("The number of blocks have to be between 1 and 8")

    if not 0 < n_last_samples < 9:
        raise Exception("The number of samples on the last block have to be"
                        + "between 1 and 8")

    if is_start_after_1st_incbn and is_stop_after_1st_incbn:
        raise Exception("Incompatible parameters: Protocol cannot both stop "
                        + "after the first incubation and skip the first "
                        + "incubation")

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''
    # load modules
    temp_mod = None
    if temp_mod_loader['lname']:
        temp_mod = ctx.load_module(temp_mod_loader['lname'],
                                   temp_mod_loader['slot'])

    # load labware
    # Labware: 290 mL reservoir, Tuberack for reagents, slide blocks
    reservoir = ctx.load_labware(reservoir_loader['lname'],
                                 reservoir_loader['slot'])
    tuberack = None
    if temp_mod is not None:
        tuberack = temp_mod.load_labware(tuberack_loader['lname'])
    else:
        tuberack = ctx.load_labware(tuberack_loader['lname'],
                                    tuberack_loader['slot'])
    slide_blocks = []
    for slot in slide_blocks_loader['slots'][:n_slots]:
        slide_block = ctx.load_labware(slide_blocks_loader['lname'], slot)
        slide_blocks.append(slide_block)

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    # load tipracks

    '''

    Add your tipracks here as a list:

    For a single tip rack:

    tiprack_name = [ctx.load_labware('{loadname}', '{slot number}')]

    For multiple tip racks of the same type:

    tiprack_name = [ctx.load_labware('{loadname}', 'slot')
                     for slot in ['1', '2', '3']]

    If two different tipracks are on the deck, use convention:
    tiprack[number of microliters]
    e.g. tiprack10, tiprack20, tiprack200, tiprack300, tiprack1000

    '''
    # Load 1000 uL tips on 6 and 9
    tiprack_1000s = \
        [ctx.load_labware(tiprack_1000_loader['lname'], slot)
         for slot in tiprack_1000_loader['slots']]

    # load instrument

    '''
    Nomenclature for pipette:

    use 'p'  for single-channel, 'm' for multi-channel,
    followed by number of microliters.

    p20, p300, p1000 (single channel pipettes)
    m20, m300 (multi-channel pipettes)

    If loading pipette, load with:

    ctx.load_instrument(
                        '{pipette api load name}',
                        pipette_mount ("left", or "right"),
                        tip_racks=tiprack
                        )
    '''
    # Load p1000 gen2
    p1000 = ctx.load_instrument(
                              p1000_loader['lname'],
                              p1000_loader['mount'],
                              tip_racks=tiprack_1000s
                              )

    # pipette functions   # INCLUDE ANY BINDING TO CLASS

    '''

    Define all pipette functions, and class extensions here.
    These may include but are not limited to:

    - Custom pickup functions
    - Custom drop tip functions
    - Custom Tip tracking functions
    - Custom Trash tracking functions
    - Slow tip withdrawal

    For any functions in your protocol, describe the function as well as
    describe the parameters which are to be passed in as a docstring below
    the function (see below).

    def pick_up(pipette):
        """`pick_up()` will pause the protocol when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the protocol will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the protocol (e.g. p300, m20).
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    '''
    def pick_up(pipette):
        """`pick_up()` will pause the protocol when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the protocol will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the protocol (e.g. p300, m20).
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            flash_lights()
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()
    # helper functions
    '''
    Define any custom helper functions outside of the pipette scope here, using
    the convention seen above.

    e.g.

    def remove_supernatant(vol, index):
        """
        function description

        :param vol:

        :param index:
        """


    '''
    class VolTracker:
        def __init__(self, labware: Labware,
                     well_vol: float = 0,
                     start: int = 1, end: int = 8,
                     mode: str = 'reagent',
                     pip_type: str = 'single',
                     msg: str = 'Refill labware volumes'):
            """
            Voltracker tracks the volume(s) used in a piece of labware

            :param labware: The labware to track
            :param well_vol: The volume of the liquid in the wells, if using a
            multi-pipette with a well plate, treat the plate like a reservoir,
            i.e. start=1, end=1, well_vol = 8 * vol of each individual well.
            :param pip_type: The pipette type used 'single' or 'multi'
            :param mode: 'reagent' or 'waste'
            :param start: The starting well
            :param end: The ending well
            :param msg: Message to send to the user when all wells are empty
            (or full when in waste mode)

            """
            self.labware_wells = dict.fromkeys(
                labware.wells()[start-1:end], 0)
            self.labware_wells_backup = self.labware_wells.copy()
            self.well_vol = well_vol
            self.pip_type = pip_type
            self.mode = mode
            self.start = start
            self.end = end
            self.msg = msg

            # Parameter error checking
            if not (pip_type == 'single' or pip_type == 'multi'):
                raise Exception('Pipette type must be single or multi')

            if not (mode == 'reagent' or mode == 'waste'):
                raise Exception('mode must be reagent or waste')

        def flash_lights(self):
            """
            Flash the lights of the robot to grab the users attention
            """
            initial_light_state = ctx.rail_lights_on
            opposite_state = not initial_light_state
            for _ in range(5):
                ctx.set_rail_lights(opposite_state)
                ctx.delay(seconds=0.5)
                ctx.set_rail_lights(initial_light_state)
                ctx.delay(seconds=0.5)

        def get_current_vol(self):
            """
            Return the current well's volume in uL
            """
            well = next(iter(self.labware_wells))
            remaining_vol = self.well_vol - self.labware_wells[well]
            return remaining_vol

        def track(self, vol: float) -> Well:
            '''track() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the reservoir.'''
            well = next(iter(self.labware_wells))
            # Treat plates like reservoirs and add 8 well volumes together
            vol = vol * 8 if self.pip_type == 'multi' else vol
            if self.labware_wells[well] + vol >= self.well_vol:
                del self.labware_wells[well]
                if len(self.labware_wells) < 1:
                    flash_lights()
                    ctx.pause(self.msg)
                    self.labware_wells = self.labware_wells_backup.copy()
                well = next(iter(self.labware_wells))
            self.labware_wells[well] += vol

            if self.mode == 'waste':
                ctx.comment('{}: {} ul of total waste'
                            .format(well, int(self.labware_wells[well])))
            else:
                ctx.comment('{} uL of liquid used from {}'
                            .format(int(self.labware_wells[well]), well))
            return well

    def wash(pip: InstrumentContext,
             vol: float, source: VolTracker, dest: list,
             do_dry_run: bool = False, pip_offset: float = 0,
             steps: int = 5, do_reuse_tip: bool = False):
        """ This function is used to aspirate a washing buffer and then
        dispense it over a well using a moving dispense

        :param pip: The pipette to use for washing aspirations/dispenses
        :param vol: The volume to wash with, e.g. 4000 uL
        :param source: VolTracker tracking a labware source of wash buffer,
        e.g. a reservoir
        :param dest: A list of wells to dispense to
        :param do_dry_run: If this argument is true then pipette tips will be
        returned to the rack they come from.
        :param pip_offset: Millimeter offset from the bottom of the well
        (i.e. the Shandon coverplate mouth)
        :param do_reuse_tip: Use only one tip for aspirating PBS / Washing
        each slide well?
        """
        max_vol = pip.max_volume
        vol_backup = vol
        for well in dest:
            if not pip.has_tip:
                pick_up(pip)
            while vol > 0:
                aspiration_vol = vol if vol < max_vol else max_vol
                pip.aspirate(aspiration_vol, source.track(aspiration_vol))
                dispense_while_moving(pip, well, aspiration_vol, steps,
                                      verbose, pip_offset)
                vol -= aspiration_vol
            if do_dry_run and not do_reuse_tip:
                pip.return_tip()
            elif not do_reuse_tip:
                pip.drop_tip()
            vol = vol_backup
        if do_reuse_tip and not do_dry_run:
            pip.drop_tip()
        elif do_dry_run and pip.has_tip:
            pip.return_tip()

    def single_dispense_reagent_p1000(source: VolTracker, dest: list,
                                      do_dry_run: bool = False,
                                      pip_offset: float = 0,
                                      steps: int = 5,
                                      do_reuse_tip: bool = False):
        """ This function aspirates a single dose of a reagent and transfers
        it to a single well with each transfer. (As opposed to the multi
        version of this function which can pick up to 9 doses of reagents
        and then dispenses them to 9 wells in one go.)

        :param source: VolTracker object for the reagent's source.
        :param dest: A list of wells to dispense to
        :param do_dry_run: If this argument is true then pipette tips will be
        returned to the rack they come from.
        :param pip_offset: Millimeter offset from the bottom of the well
        (i.e. the Shandon coverplate mouth). positive numbers to raise,
        negative to lower the pipette.
        :param do_reuse_tip: Use only one tip for aspirating PBS / Washing
        each slide well?
        """
        nonlocal p1000
        for well in dest:
            aspiration_vol = 100
            if not p1000.has_tip:
                pick_up(p1000)
            p1000.aspirate(aspiration_vol, source.track(aspiration_vol))
            dispense_while_moving(p1000, well, aspiration_vol, steps)
            if do_dry_run and not do_reuse_tip:
                p1000.return_tip()
            elif not do_reuse_tip:
                p1000.drop_tip()
        # Drop the tip after all wells have been dispensed to if the tip is
        # being reused for this reagent dispense
        if do_reuse_tip and not do_dry_run:
            p1000.drop_tip()
        elif do_dry_run and p1000.has_tip:
            p1000.return_tip()

    def multi_dispense_reagent_p1000(source: VolTracker, dest: list,
                                     do_dry_run: bool = False,
                                     pip_offset: float = 0,
                                     steps: int = 5,
                                     do_reuse_tip: bool = False):
        """ The multi version of the reagent transfer function which can
        pick up to 9 doses of reagents and then dispenses them to 9 wells in
        one go.

        :param source: VolTracker object for the reagent's source.
        :param dest: A list of wells to dispense to
        :param do_dry_run: If this argument is true then pipette tips will be
        returned to the rack they come from.
        :param pip_offset: Millimeter offset from the bottom of the well
        (i.e. the Shandon coverplate mouth). positive numbers to raise,
        negative to lower the pipette.
        :param do_reuse_tip: Use only one tip for aspirating PBS / Washing
        each slide well?
        """
        nonlocal p1000
        n_wells = len(dest)
        track_vol = 0
        for i, d_well in enumerate(dest):
            remaining_wells = n_wells - i
            aspiration_vol = 0
            if track_vol < 100:
                aspiration_vol = 905 if remaining_wells > 9 else \
                    remaining_wells * 100 + 5
                if p1000.has_tip:
                    if do_reuse_tip:
                        p1000.blow_out(ctx.fixed_trash['A1'])
                    else:
                        if do_dry_run:
                            p1000.return_tip()
                        else:
                            p1000.drop_tip()
                        pick_up(p1000)
                else:
                    pick_up(p1000)
                # There's a chance that the remaining volume in the reagent
                # tube is less than the volume we want to aspirate. We don't
                # want the remaining volume to go to waste since it could be
                # a lot, so we aspirate it here and subtract it from the total
                tube_vol_asp = source.get_current_vol() - 5
                if aspiration_vol > tube_vol_asp:
                    p1000.aspirate(
                        tube_vol_asp, source.track(tube_vol_asp))
                    remaining_asp_vol = aspiration_vol - tube_vol_asp
                    p1000.aspirate(remaining_asp_vol,
                                   source.track(remaining_asp_vol))
                else:
                    p1000.aspirate(
                        aspiration_vol, source.track(aspiration_vol))
                track_vol = aspiration_vol
            dispense_while_moving(p1000, d_well, 100, steps)
            track_vol -= 100
        # Drop the tip after we're done
        if p1000.has_tip:
            if do_dry_run:
                p1000.return_tip()
            else:
                p1000.drop_tip()

    def flash_lights():
        """
        Flash the lights of the robot to grab the users attention
        """
        initial_light_state = ctx.rail_lights_on
        opposite_state = not initial_light_state
        for _ in range(5):
            ctx.set_rail_lights(opposite_state)
            ctx.delay(seconds=0.5)
            ctx.set_rail_lights(initial_light_state)
            ctx.delay(seconds=0.5)

    def pause(msg: str, time_elapsed_sec: float = 0,
              pause_period_minutes: int = 60, do_dry_run: bool = False):
        """ Pauses the protocol for an incubation period, but subtracts the
        time elapsed for some preparative process from the total pause period.
        Also tells the user what the slides are being incubated with.
        """
        msg_template = "Incubating slides with {}"
        dry_run_msg = "(Dry run): "
        if time_elapsed_sec > pause_period_minutes*60:
            ctx.comment(
                "Skipping pause for incubation, the pause period has already "
                + "elapsed during the reagent transfer of {}".format(msg))
            return
        min_elapsed = math.ceil(time_elapsed_sec/60)
        pause_period_secs = 60 - time_elapsed_sec % 60
        pause_period_minutes -= min_elapsed
        if not do_dry_run:
            ctx.delay(minutes=pause_period_minutes, seconds=pause_period_secs,
                      msg=msg_template.format(msg))
        else:
            ctx.comment(dry_run_msg + msg.format(msg))

    def dispense_while_moving(pip: InstrumentContext,
                              well: Well, vol: float, steps: int,
                              is_verbose: bool = False, pip_offset: float = 0):
        """
        This function dispenses a partial volume = vol/steps and then moves
        a distance/steps and repeats
        """
        well_diameter = float(well.diameter)
        dispense_distance = well_diameter - well_edge_offset
        dy = dispense_distance/steps  # Move a fraction (=steps) of well diatr.
        dv = vol/steps
        start_location = well.bottom().move(
            Point(0, well_diameter/2 - well_edge_offset, pip_offset))
        pip.move_to(start_location)
        for i in range(steps):
            loc = start_location.move(Point(0, i*dy, 0))
            if is_verbose:
                ctx.comment("Dispensing at: {}".format(loc))
            pip.dispense(dv, loc)

    # reagents
    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''
    # Each slide block has 8 "wells", each well uses up 100 uL of each
    # reagent: Block, antibody1, antibody2, nuclear counterstain
    block = VolTracker(tuberack, vol_reagent, start=1, end=4,
                       msg="Refill Block reagent tubes")
    antibody1 = VolTracker(tuberack, vol_reagent, start=5, end=8,
                           msg="Refill Antibody 1 reagent tubes")
    antibody2 = VolTracker(tuberack, vol_reagent, start=9, end=13,
                           msg="Refill Antibody 2 reagent tubes")
    # Nuclear counterstain
    nuc_cstn = VolTracker(tuberack, vol_reagent, start=14, end=17,
                          msg="Refill Nuclear counterstain reagent tubes")
    pbs = VolTracker(
        reservoir, 288*10**3, start=1, end=1, mode='reagent',
        pip_type='single', msg="Refill PBS reservoir")

    # plate, tube rack maps
    # Add all wells up to the block before the last block
    # Assume that they all have 8 samples
    target_wells = []
    for slide_block in slide_blocks[:-1]:
        for well in slide_block.wells():
            target_wells.append(well)

    # Add the wells of the last block, samples may be less than 8
    for i in range(n_last_samples):
        target_wells.append(slide_blocks[-1].wells()[i])

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''

    # protocol

    '''

    Include header sections as follows for each "section" of your protocol.

    Section can be defined as a step in a bench protocol.

    e.g.

    ctx.comment('\n\nMOVING MASTERMIX TO SAMPLES IN COLUMNS 1-6\n')

    for .... in ...:
        ...
        ...

    ctx.comment('\n\nRUNNING THERMOCYCLER PROFILE\n')

    ...
    ...
    ...


    '''
    # Set the temperature to 4 degrees on the temperature module.
    if temp_mod:
        temp_mod.set_temperature(4)
    dt = t_per_block * n_slots
    reag_transfer_fn = multi_dispense_reagent_p1000 if is_multi_disp_reags \
        else single_dispense_reagent_p1000

    # Transfer 100 µL of block from the tuberack to each destination well
    # (slide) (could be done as a multi-dispense with the P1000)
    # Measure time from the start of pipetting and subtract from 1 hr pause
    # so that the next pipetting step starts after 1 hour and not 1 hour +
    # the time it takes to finish the reagent transfer
    if not is_start_after_1st_incbn:  # Skip 1st incubation?
        ctx.comment("\n\nAdding block reagent\n")
        reag_transfer_fn(block, target_wells, do_dry_run=is_dry_run,
                         pip_offset=pipette_offset,
                         steps=dispense_steps, do_reuse_tip=is_reuse_reag_tips)
        # Pause/Incubate for 1 hour
        if is_stop_after_1st_incbn:
            ctx.comment("\n\nStopping protocol after 1st incubation")
            ctx.comment("Remove the slides, store them at 4C ON, "
                        + "then replace the slides in the morning and restart "
                        + "the protocol. (Remember to set the option to start "
                        + "the protocol after the 1st incubation step)")
            return
        pause("block", time_elapsed_sec=dt, do_dry_run=is_dry_run)
    else:
        ctx.comment(
            "Starting the protocol from the 2nd reagent step (antibody1)")
    # Transfer 100 µL of primary antibody to dest. wells (slide)
    ctx.comment("\n\nAdding Antibody 1 reagent\n")
    reag_transfer_fn(antibody1, target_wells, do_dry_run=is_dry_run,
                     pip_offset=pipette_offset,
                     steps=dispense_steps, do_reuse_tip=is_reuse_reag_tips)
    # Pause 1 hour
    pause("Antibody 1", time_elapsed_sec=dt, do_dry_run=is_dry_run)
    # Transfer 4 mL of PBS to each slide target well (i.e. 4 round trips)
    # with the P1000 (Slide wash)
    ctx.comment("\n\nWashing slides with PBS\n")
    wash(p1000, 4000, pbs, target_wells, do_dry_run=is_dry_run,
         pip_offset=pipette_offset, steps=dispense_steps,
         do_reuse_tip=is_reuse_wash_tips)
    # Transfer 100 µL of the second antibody
    ctx.comment("\n\nAdding Antibody 2 reagent\n")
    reag_transfer_fn(antibody2, target_wells, do_dry_run=is_dry_run,
                     pip_offset=pipette_offset,
                     steps=dispense_steps, do_reuse_tip=is_reuse_reag_tips)
    # Pause 1 hour
    pause("Antibody 2", time_elapsed_sec=dt, do_dry_run=is_dry_run)
    # Wash slides with 4 mL of PBS
    ctx.comment("\n\nWashing slides with PBS\n")
    wash(p1000, 4000, pbs, target_wells, do_dry_run=is_dry_run,
         pip_offset=pipette_offset, steps=dispense_steps,
         do_reuse_tip=is_reuse_wash_tips)
    # Transfer 100 µL nuclear counterstain to each well
    ctx.comment("\n\nAdding Nuclear counterstain reagent\n")
    reag_transfer_fn(nuc_cstn, target_wells, do_dry_run=is_dry_run,
                     pip_offset=pipette_offset,
                     steps=dispense_steps, do_reuse_tip=is_reuse_reag_tips)
    # Incubate 5 minutes
    pause("Nuclear counterstain", pause_period_minutes=5,
          do_dry_run=is_dry_run, time_elapsed_sec=dt)
    # Wash slides with 4 mL of PBS
    ctx.comment("\n\nWashing slides with PBS\n")
    wash(p1000, 4000, pbs, target_wells, do_dry_run=is_dry_run,
         pip_offset=pipette_offset, steps=dispense_steps,
         do_reuse_tip=is_reuse_wash_tips)
    ctx.comment("\n\n~~~~ End of protocol ~~~~\n")
