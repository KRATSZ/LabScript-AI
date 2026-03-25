from opentrons import protocol_api
from opentrons.protocol_api.labware import Well, Labware
import math
from typing import Sequence, Tuple
import re


metadata = {
    'protocolName': 'Sample transfer and bead mastermix addition',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def parse_range_string(range_string: str) -> Tuple[int, int]:
    """ Parses a range or a single number from the input string.
    the format for a number is n-m, where n and m are any positive
    integers.
    :param range_string: range string to decode
    :return value: A tuple of the start and end index of the range
    """
    single_num_pattern = re.compile('[0-9]+')
    range_pattern = re.compile('[0-9]+-[0-9]+')
    # Case when there's only one index (e.g. the string decodes to a single
    # well
    if single_num_pattern.fullmatch(range_string) is not None:
        index = int(range_string)
        return index, index
    if range_pattern.fullmatch(range_string):
        # Return both substrings that match numbers (i.e. the start and
        # end indices
        start, end = range_string.split('-')
        return int(start), int(end)
    # If neither regular expression matched then we assume that the string
    # is incorrectly formatted
    raise Exception(("Invalid range string: it was \"{}\" but should be a "
                     "natural number or a range in the format of "
                     "n-m where n and m are natural numbers, "
                     "e.g: 1-4").format(range_string))


def run(ctx: protocol_api.ProtocolContext):

    [n_samples_rack_1,
     n_samples_rack_2,
     n_samples_rack_3,
     master_mix_range,
     mastermix_max_vol,
     mastermix_mix_rate_multiplier,
     mm_aspiration_flowrate_multiplier,
     mm_dispense_flowrate_multiplier,
     p300_mount,
     m300_mount,
     do_mm_resusp_pause,
     is_debug_mode] = get_values(  # noqa: F821
     "n_samples_rack_1",
     "n_samples_rack_2",
     "n_samples_rack_3",
     "master_mix_range",
     "mastermix_max_vol",
     "mastermix_mix_rate_multiplier",
     "mm_aspiration_flowrate_multiplier",
     "mm_dispense_flowrate_multiplier",
     "p300_mount",
     "m300_mount",
     "do_mm_resusp_pause",
     "is_debug_mode")

    n_total_samples = 0
    for i, n in enumerate([n_samples_rack_1,
                           n_samples_rack_2,
                           n_samples_rack_3]):
        if n < 0 or n > 32:
            raise Exception(
                "Invalid number of samples (n={}) on tuberack #{}".format(
                    n, i+1)
                )
        n_total_samples += n

    # Check that there are enough mastermix wells

    # Todo: If tuberack: Error check that all tubes are 15 mL types

    # Define labware and slots
    sample_tuberack_loader = \
        ("nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml", ['10', '7', '4'])
    target_plate_loader = \
        ("thermofisherkingfisherdeepwell_96_wellplate_2000ul", '2')
    mastermix_labware_loader = ('nest_12_reservoir_15ml', '1')
    sample_200ul_filtertiprack_loader = \
        ('opentrons_96_filtertiprack_200ul', '9')

    mm_well_vol_ul = mastermix_max_vol * 1000
    # TODO: Remove dead volumes from the protocols - the dead-volume is
    # already defined by the 1.5 multiplier (1/3rd of the total vol)
    dead_vol = 1/3 * mm_well_vol_ul

    mm_start_index, mm_end_index = parse_range_string(master_mix_range)
    n_mm_wells = mm_end_index - mm_start_index + 1
    mm_vol_per_sample = 275
    total_mm_vol = mm_vol_per_sample * n_total_samples

    # No more than 5 wells should be required for the mastermix
    # maximum number of samples: 31*3=93, mm volume per sample = 275
    # excess volume factor: 1.5
    # 93*275*1.5=38,362.5 uL, max volume per mm well is 9540 uL
    # n_wells = 38262.5/9540 = 4.02 wells
    n_required_mm_wells = math.ceil(total_mm_vol/(mm_well_vol_ul-dead_vol))
    if is_debug_mode:
        msg = "\n\nNumber of required wells: {}\n"
        msg = msg.format(n_required_mm_wells)
        ctx.comment(msg)
    if n_required_mm_wells > n_mm_wells:
        msg = ("This protocol run requires {} wells of mastermix, but "
               "there are only {} wells available, please ensure that there "
               "is enough mastermix")
        msg = msg.format(n_required_mm_wells, n_mm_wells)
        raise Exception(msg)

    # define all custom variables above here with descriptions:

    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''

    # load labware

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    sample_tuberacks = [
        ctx.load_labware(sample_tuberack_loader[0], s)
        for s in sample_tuberack_loader[1]]
    mm_source = ctx.load_labware(
        mastermix_labware_loader[0], mastermix_labware_loader[1])
    target_plate = ctx.load_labware(
        target_plate_loader[0],
        target_plate_loader[1])
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
    tiprack_200 = ctx.load_labware(sample_200ul_filtertiprack_loader[0],
                                   sample_200ul_filtertiprack_loader[1])
    tiprack_300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                   for slot in [6, 3]]

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
    p300 = ctx.load_instrument(
                              'p300_single_gen2',
                              p300_mount,
                              tip_racks=[tiprack_200]
                              )
    m300 = ctx.load_instrument(
                              'p300_multi_gen2',
                              m300_mount,
                              tip_racks=tiprack_300
                              )
    num_samp = int(n_samples_rack_1) + int(n_samples_rack_2) + int(n_samples_rack_3)  # noqa: E501
    spill = num_samp % 8
    num_full_columns = math.floor(num_samp/8)
    num_channels_per_pickup = spill
    tip_count = 0
    if spill > 0:
        tips_ordered = [
            tip for rack in tiprack_300
            for row in rack.rows()[
                len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]  # noqa: E501
            for tip in row]

    def pick_up_multi():
        nonlocal tip_count
        m300.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

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
                     start: int = 1,
                     end: int = 8,
                     mode: str = 'reagent',
                     pip_type: str = 'single',
                     msg: str = 'Refill labware volumes',
                     reagent_name: str = 'nameless reagent',
                     is_verbose: bool = True,
                     is_strict_mode: bool = False,
                     threshhold_advancement_vol: float = 1,
                     dead_volume: float = 0):
            """
            Voltracker tracks the volume(s) used in a piece of labware.
            It's conceptually important to understand that in reagent
            mode the volumes tracked are how much volume has been removed from
            the VolTracker, but waste and target is how much has been added
            to it, and how much was there/have been taken out to begin with.
            This will have implications for how the class is initialized.

            :param labware: The labware to track
            :param well_vol: The volume of the liquid in the wells, if using a
            multi-pipette with a well plate, treat the plate like a reservoir,
            i.e. start=1, end=1, well_vol = 8 * vol of each individual well.
            :param pip_type: The pipette type used: 'single' or 'multi',
            when the type is 'multi' volumes are multiplied by 8 to reflect
            the true volumes used by the pipette.
            :param mode: 'reagent', 'target' or 'waste'
            :param start: The starting well
            :param end: The ending well
            :param msg: Message to send to the user when all wells are empty
            (or full when in waste mode)
            :param reagent_name: Name of the reagent tracked by the object
            :param is_verbose: Whether to have VolTracker send ProtocolContext
            messages about its actions or not.
            :param is_strict_mode: If set to True VolTracker will pause
            execution when its tracked wells are depleted (or filled), ask the
            user to replace the labware and reset the volumes. If it's False
            VolTracker will raise an exception if trying to use more volume
            than the VolTracker is set up for. strict_mode also forces the
            user to check if there's enough volume in the active well and
            to manually advance to the next well by calling advance_well()
            :param threshhold_advancement_vol: If using strict mode VolTr.
            will throw an exception if the user advances the well while there
            is more than the threshhold_advancement_vol of volume left in
            the well.
            """
            # Boolean value: True if the well has been filled
            # or has been depleted
            self.labware_wells = {}
            for well in labware.wells()[start-1:end]:
                self.labware_wells[well] = [0, False]
            self.labware_wells_backup = self.labware_wells.copy()
            self.well_vol = well_vol
            self.pip_type = pip_type
            self.mode = mode
            self.start = start
            self.end = end
            self.msg = msg
            self.is_verbose = is_verbose
            # Total vol changed - how much volume has been withdrawn or added
            # to this Voltracker
            self.total_vol_changed = 0
            # If true, then labware should raise an exception when full
            # rather than reset
            self.is_strict_mode = is_strict_mode
            self.reagent_name = reagent_name
            self.dead_volume = dead_volume

            valid_modes = ['reagent', 'waste', 'target']

            # Parameter error checking
            if not (pip_type == 'single' or pip_type == 'multi'):
                raise Exception('Pipette type must be single or multi')

            if mode not in valid_modes:
                msg = "Invalid mode, valid modes are {}"
                msg = msg.format(valid_modes)
                raise Exception(msg)

            if mode != 'reagent' and dead_volume > 0:
                raise Exception(("Setting a dead/min volume only makes sense "
                                 "for reagents"))

        def __str__(self):
            msg = (self.reagent_name + " " + self.mode
                   + " volume change: " + str(self.total_vol_changed),
                   + " well vol: " + str(self.well_vol) + " dead vol: "
                   + str(self.dead_volume))
            msg += "\nChanges in each well:\n"
            for i, well_tracker in enumerate(self.labware_wells.values()):
                msg += "well {}: Volume change: {}\n".format(
                    i+1, well_tracker[0])
            return msg

        @staticmethod
        def flash_lights():
            """
            Flash the lights of the robot to grab the users attention
            """
            nonlocal ctx
            initial_light_state = ctx.rail_lights_on
            opposite_state = not initial_light_state
            for _ in range(5):
                ctx.set_rail_lights(opposite_state)
                ctx.delay(seconds=0.5)
                ctx.set_rail_lights(initial_light_state)
                ctx.delay(seconds=0.5)

        def get_wells(self) -> Sequence:
            return list(self.labware_wells.keys())

        def to_list(self):
            return list(self.labware_wells.items())

        def get_total_initial_vol(self):
            """
            Return the total initial volume of the
            tracker = n_wells * well_vol
            """
            return len(self.labware_wells) * self.well_vol

        def get_total_dead_volume(self):
            """
            Returns the total dead volume of the tracker
            """
            return len(self.labware_wells) * self.dead_volume

        def get_total_remaining_vol(self):
            """
            Returns the total volume remaining in the tracker
            including the dead volume
            """
            return (self.get_total_initial_vol()
                    - self.total_vol_changed)

        def get_active_well_vol_change(self):
            """
            Return the volume either used up (reagents) or added
            (target or trash) in the currently active well
            """
            well = self.get_active_well()
            return self.labware_wells[well][0]

        def get_active_well_remaining_vol(self):
            """
            Returns how much volume is remaing to be used (reagents) or the
            space left to fill the well (waste and targets)
            """
            vol_change = self.get_active_well_vol_change()
            return self.well_vol - vol_change - self.dead_volume

        def get_active_well(self):
            for key in self.labware_wells:
                # Return the first well that is not full
                if self.labware_wells[key][1] is False:
                    return key

        def advance_well(self):
            curr_well = self.get_active_well()
            # Mark the current well as 'used up'
            self.labware_wells[curr_well][1] = True
            wells = self.to_list()
            all_depleted = True
            for tracked_well in wells:
                status = tracked_well[1][1]
                if status is False:
                    all_depleted = False
                    break
            if all_depleted:
                raise Exception("All tracker wells have been depleted")

        def reset_labware(self):
            VolTracker.flash_lights()
            ctx.pause(self.msg)
            self.labware_wells = self.labware_wells_backup.copy()

        def get_active_well_vol(self):
            well = self.get_active_well()
            return self.labware_wells[well][0]

        def get_current_vol_by_key(self, well_key):
            return self.labware_wells[well_key][0]

        def track(self, vol: float, **kwargs) -> Well:
            """track() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the active source well.
            :param vol: How much volume to track (per tip), i.e. if it's one
            tip track vol, but if it's multi-pipette, track 8 * vol.

            This implies that VolTracker will treat a column like a well,
            whether it's a plate or a reservoir.
            """
            well = self.get_active_well()
            # Treat plates like reservoirs and add 8 well volumes together
            # Total vol changed keeps track across labware resets, i.e.
            # when the user replaces filled/emptied wells
            if 'custom_num_tips' in kwargs.keys():
                vol = vol * kwargs['custom_num_tips']
            else:
                vol = vol * 8 if self.pip_type == 'multi' else vol

            # Track the total change in volume of this volume tracker
            # self.total_vol_changed += vol
            #
            # if (self.labware_wells[well][0] + vol
            #         > self.well_vol - self.dead_volume):
            #     if self.is_strict_mode:
            #         msg = ("Tracking a volume of {} uL would {} the "
            #                "current well: {} on the {} {} tracker. "
            #                "The max well volume is {}, and "
            #                "the current vol is {}. The dead volume is {}")
            #         mode_msg = ("over-deplete`" if self.mode == "reagent"
            #                     else "over-fill")
            #         msg = msg.format(
            #             vol, mode_msg, well, self.reagent_name, self.mode,
            #             self.well_vol, self.get_active_well_vol(),
            #             self.dead_volume)
            #         raise Exception(msg)
            #     self.labware_wells[well][1] = True
            #     is_all_used = True

                # Check if wells are completely full (or depleted)
                for w in self.labware_wells:
                    if self.labware_wells[w][1] is False:
                        is_all_used = False

                if is_all_used is True:
                    if self.is_strict_mode is False:
                        self.reset_labware()
                    else:
                        e_msg = ("{}: {} {} wells would be {} by this action "
                                 "this VolTracker is in strict mode, check why"
                                 "manual reset was not performed")

                        fill_status = \
                            ("over-depleted" if self.mode == "reagent" else
                             "over-filled")
                        e_msg = e_msg.format(str(self),
                                             self.reagent,
                                             self.mode, fill_status)
                        raise Exception(e_msg)

                well = self.get_active_well()
                if self.is_verbose:
                    ctx.comment(
                        "\n{} {} tracker switching to well {}\n".format(
                            self.reagent_name, self.mode, well))
            self.labware_wells[well][0] += vol

            if self.is_verbose:
                if self.mode == 'waste':
                    ctx.comment('{}: {} ul of total waste'
                                .format(well,
                                        int(self.labware_wells[well][0])))
                elif self.mode == 'target':
                    ctx.comment('{}: {} ul of reagent added to target well'
                                .format(well,
                                        int(self.labware_wells[well][0])))
                else:
                    ctx.comment('{} uL of liquid used from {}'
                                .format(int(self.labware_wells[well][0]),
                                        well))
            return well

    # reagents

    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''
    mm_tracker = VolTracker(
        labware=mm_source,
        well_vol=mm_well_vol_ul,
        start=mm_start_index,
        end=mm_end_index,
        pip_type='multi',
        reagent_name='Bead/binding buffer mastermix',
        dead_volume=dead_vol,
        is_verbose=is_debug_mode,
        is_strict_mode=True
        )
    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''

    total_samples = n_samples_rack_1 + n_samples_rack_2 + n_samples_rack_3
    sample_wells = []
    for num_s, rack in zip(
        [n_samples_rack_1, n_samples_rack_2, n_samples_rack_3],
            sample_tuberacks):
        for well in rack.wells()[0:num_s]:
            sample_wells.append(well)

    dest_cols = target_plate.columns()

    i = 0
    dest_wells = []
    for col in dest_cols:
        for well in col:
            dest_wells.append(well)
            i += 1
            if i == total_samples:
                break

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
    # Step 1 to 4 - Distribute samples from tubes to target plate
    """
    Step 1: Aspirate 200 uL of sample mixture from sample tube [Different
    Tips; 5 - 10 uL air gap if possible; Touch tip to side of tube]
    Step 2: Dispense sample into the one corresponding deep-well on 96
    deep-well plate in the order A1, A2... A12, B1, B2... B12, etc.
    [Different Tips; with blow out; Touch tip to side of deep-well]
    Step 3: Discard tip in waste
    Step 4: Repeat for all specified samples in rack for each specified rack
    """
    ctx.comment("\n\nDistributing samples from tubes to target plate wells\n")
    for s, d in zip(sample_wells, dest_wells):
        if not p300.has_tip:
            pick_up(p300)
        p300.aspirate(200, s)
        p300.touch_tip()
        p300.dispense(200, d)
        p300.blow_out()
        p300.drop_tip()

    # Mastermix steps (5-11) are performed in protocol 1 - mastermix creation
    # Step 11 to 14 - Distribute binding buffer/bead mastermix
    # 13: Use 300 uL non-filtered tips to mix bead mastermix
    # Mix seven times
    # blowout after mix, touch tips (if tube source)

    # Check if we're using the tuberack or reservoir
    """
    Step 12: All used tips from the prior steps are discarded
    Step 13: The 8-channel pipettor acquires 8x300 uL non-filtered pipette
    tips and then slowly (make speed variable) pipette-mixes the bead master
    mixture 7 times in each well of the 12-well reservoir [same tips; blowout
    used after the last mix in each well; tip touch on side of each well in
    reservoir]
    Step 14: Discard Tips
    """
    n_tips = 8
    m300.pick_up_tip()

    ctx.comment("\n\nMixing the mastermix\n")
    mm_wells = mm_tracker.get_wells()
    # TODO: Have to set a height offset for mixing tubes
    max_mix_vol = min(m300.max_volume*n_tips, mm_tracker.well_vol)
    per_tip_mix_vol = max_mix_vol/n_tips
    for i, well in enumerate(mm_wells):
        m300.mix(3, per_tip_mix_vol, well,
                 mastermix_mix_rate_multiplier)
        m300.blow_out(well)
        m300.touch_tip()
    m300.drop_tip()
    tip_count += 1

    ctx.comment("\n\nDistributing mastermix to samples on the target plate\n")

    if do_mm_resusp_pause:
        ctx.pause("\n\nPausing protocol for mastermix resuspension\n")

    # Transfer mastermix to samples
    air_gap_vol = 10
    dead_vol = 3000
    aspiration_vol = 8 * mm_vol_per_sample
    res_well = 0
    remaining_well_vol = mastermix_max_vol*1000
    ctx.comment("\n\nDistributing mastermix to samples on target plate\n")

    for well in target_plate.rows()[0][:num_full_columns]:

        m300.pick_up_tip()

        if remaining_well_vol > dead_vol:
            m300.aspirate(275, mm_source.wells()[res_well],
                          mm_aspiration_flowrate_multiplier)
            remaining_well_vol -= aspiration_vol
        else:
            res_well += 1
            remaining_well_vol = mastermix_max_vol*1000
            m300.aspirate(275, mm_source.wells()[res_well],
                          mm_aspiration_flowrate_multiplier)

        m300.air_gap(air_gap_vol)
        m300.dispense(
            mm_vol_per_sample+air_gap_vol, well,
            mm_dispense_flowrate_multiplier)
        m300.blow_out()
        m300.drop_tip()
        tip_count += 1
        ctx.comment('\n')

    if spill > 0:
        ctx.comment("\n\nDistributing mastermix to unfilled column\n")

        pick_up_multi()

        if remaining_well_vol > dead_vol:
            m300.aspirate(275, mm_source.wells()[res_well],
                          mm_aspiration_flowrate_multiplier)
            remaining_well_vol -= aspiration_vol
        else:
            res_well += 1
            remaining_well_vol = mastermix_max_vol*1000
            m300.aspirate(275, mm_source.wells()[res_well],
                          mm_aspiration_flowrate_multiplier)

        m300.air_gap(air_gap_vol)
        m300.dispense(
            mm_vol_per_sample+air_gap_vol,
            target_plate.rows()[0][num_full_columns],
            mm_dispense_flowrate_multiplier)
        m300.blow_out()
        m300.drop_tip()
        tip_count += 1
        ctx.comment('\n')

    ctx.comment("\n\n - Protocol finished! - \n")

    if is_debug_mode:
        msg = "\nExpected mastermix transfer volume: {}\n"
        msg = msg.format(total_mm_vol)
        ctx.comment(msg)
        msg = "\nActually transferred volume of mastermix: {}\n"
        msg = msg.format(mm_tracker.total_vol_changed)
        ctx.comment(msg)
