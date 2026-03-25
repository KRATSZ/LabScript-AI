from opentrons import protocol_api
from opentrons import types
import math

metadata = {
    'protocolName': 'Automated GenFind V3 Blood/serum DNA extraction',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    [
     n_samples,
     is_blood_cells,
     is_lwaste,
     x_offset,
     mag_height,
     is_protk_tube,
     is_eb_tube
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "n_samples",
        "is_blood_cells",
        "is_lwaste",
        "x_offset",
        "mag_height",
        "is_protk_tube",
        "is_eb_tube"
        )

    sample_vol = 200 if is_blood_cells else 400

    # Defining the max volume of each reservoir either for reagents or trash
    twelve_well_max_vol = 14*10**3
    one_well_max_vol = 194*10**3
    two_ml_tube_max_vol = 1990
    trash_max_vol = 195*10**3

    pip_left_lname = 'p300_multi_gen2'
    pip_right_lname = 'p300_single_gen2'
    tips_lname = 'opentrons_96_filtertiprack_200ul'
    one_well_resv_lname = 'nest_1_reservoir_195ml'
    twelve_well_resv_lname = 'nest_12_reservoir_15ml'
    mag_mod_lname = 'magnetic module gen2'
    mag_plate_lname = 'usascientific_96_wellplate_2ml_deep'
    dest_plate_lname = 'abgene_96_wellplate_800ul'
    tuberack_lname = 'opentrons_24_tuberack_generic_2ml_screwcap'

    n_sample_columns = math.floor(n_samples/8)

    # Volumes of each buffer to use per sample
    lysis_buf_lbb_vol = 2*sample_vol+100
    prot_k_vol = 0.15*sample_vol
    bind_bbb_vol = 1.5*sample_vol
    wash_wbb_vol = 4*sample_vol
    wash_wbc_vol = 1600
    elution_buffer_vol = sample_vol if is_blood_cells else 40

    # Labware and tiprack slots
    twelve_well_resv_slot = 4
    wash_wbb_resv_slot = 1
    wash_wbc_resv_slot = 2
    mag_mod_slot = 3
    liq_trash_resv_slot = 6
    dest_plate_slot = 9
    tuberack_slot = 7
    tiprack_slots = [5, 8, 10, 11]

    # Offsets to pipette away from the magnetic beads in the x direction
    sides = [-x_offset, x_offset] * (n_sample_columns // 2)

    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''
    mag_mod = ctx.load_module(mag_mod_lname, mag_mod_slot)

    # load labware

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    wash_wbb_resv = ctx.load_labware(one_well_resv_lname, wash_wbb_resv_slot,
                                     label="Wash WBB reservoir")
    wash_wbc_resv = ctx.load_labware(one_well_resv_lname, wash_wbc_resv_slot,
                                     label="Wash WBC reservoir")
    sample_plate = mag_mod.load_labware(mag_plate_lname,
                                        label="sample plate",
                                        namespace='custom_beta')
    twelve_well_resv = ctx.load_labware(twelve_well_resv_lname,
                                        twelve_well_resv_slot,
                                        label="multi-reagent reservoir")
    trash_resv_1 = ctx.load_labware(one_well_resv_lname, liq_trash_resv_slot,
                                    label="liquid waste reservoir")
    destination_plate = ctx.load_labware(dest_plate_lname, dest_plate_slot,
                                         label="destination plate",
                                         namespace='custom_beta')
    tuberack = ctx.load_labware(tuberack_lname, tuberack_slot,
                                label="Reagent tuberack")

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
    tipracks = [ctx.load_labware(tips_lname, slot)
                for slot in tiprack_slots]

    # load instrument

    '''
    Nomenclature for pipette:

    use 'p'  for single-channel, 'm' for multi-channel,
    followed by number of microliters.

    p20, m300, p1000 (single channel pipettes)
    m20, m300 (multi-channel pipettes)

    If loading pipette, load with:

    ctx.load_instrument(
                        '{pipette api load name}',
                        pipette_mount ("left", or "right"),
                        tip_racks=tiprack
                        )
    '''
    m300 = ctx.load_instrument(
                              pip_left_lname,
                              'left',
                              tip_racks=tipracks
                              )

    p300 = ctx.load_instrument(
                              pip_right_lname,
                              'right',
                              tip_racks=tipracks
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

    For any functions in your ctx, describe the function as well as
    describe the parameters which are to be passed in as a docstring below
    the function (see below).

    def pick_up(pipette):
        """`pick_up()` will pause the ctx when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the ctx will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the ctx (e.g. m300, m20).
        """
        try:
            pipette.pick_up_tip()
        except ctx_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    '''
    def pick_up(pipette):
        """`pick_up()` will pause the ctx when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the ctx will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the ctx (e.g. m300, m20).
        """
        nonlocal ctx

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
    '''

    def remove_supernatant(volume):
        '''
        Remove supernatant from the source columns and dispense it in the trash
        (the user may remove the waste to liquid waste reservoir if they so
        choose)

        :param volume: The volume of supernatant to remove to the trash
        '''
        nonlocal is_lwaste, trash, m300, sides, sample_columns, \
            liq_trash_tracker

        # Determine where the liquid trash goes: general trash or
        # liq. trash reservoir
        trash_target = trash
        if is_lwaste:
            trash_target = liq_trash_tracker.track(volume)

        for col, side in zip(sample_columns, sides):
            remainining_volume = volume
            pick_up(m300)
            while remainining_volume > 0:
                trash_vol = (200 if remainining_volume > 200 else
                             remainining_volume)
                m300.aspirate(trash_vol,
                              col[0].bottom().move(
                                types.Point(x=side, y=0, z=1)))

                m300.dispense(trash_vol, trash_target.top())
                m300.blow_out()  # blow out at trash_target.top()
                remainining_volume -= trash_vol
            m300.drop_tip()

    def wash(wash_vol, wash_vol_tracker, mag_engage_time,
             n_mixes, buffer_name='wash buffer', reuse_tips=True):
        nonlocal is_lwaste, m300, sides, sample_columns, mag_mod, \
                 ctx, mag_height
        '''
        This function repeats a washing procedure two times.
        Washing procedure:
        1. Disengage the magnets
        2. Add wash buffer
        3. Mix n_mixes times
        4. Engage the magnets for mag_engage_time minutes
        5. Remove the supernatant
        6. Repeat from step 1, one time

        :param wash_vol: The volume of wash buffer to use in microliters
        :param wash_vol_tracker: VolumeTracker for the wash buffer wells
        :param mag_engage_time: Amount of time in minutes to delay after
        engaging the magnets
        :param n_mixes: How many times to mix the samples after adding wash
        :param buffer_name: Name of the buffer to display to the user in
        messaging
        :param reuse_tips: Intended as a variable for tip parking, not used.
        '''
        for i in range(0, 2):
            mag_mod.disengage()

            ctx.comment("\n\nAdding {} to sample wells\n".format(buffer_name))
            for col in sample_columns:
                remainining_volume = wash_vol
                pick_up(m300)
                while remainining_volume > 0:
                    vol = 200 if remainining_volume >= 200 else \
                        remainining_volume
                    m300.aspirate(vol, wash_vol_tracker.track(vol))
                    m300.dispense(vol, col[0])
                    remainining_volume -= vol
                mix_vol = 200 if wash_vol - 20 > 200 else wash_vol - 20
                m300.mix(10, mix_vol)
                m300.touch_tip()
                m300.drop_tip()

            mag_mod.engage(height_from_base=mag_height)
            ctx.delay(minutes=mag_engage_time)
            ctx.comment("\n\nRemoving {} supernatant from sample wells\n"
                        .format(buffer_name))
            remove_supernatant(wash_vol)

    def get_well_index_by_name(well_name):
        letter_to_row_num_dict = \
            {"A": 0, "B": 1, "C": 2, "D": 3,
             "E": 4, "F": 5, "G": 6, "H": 7}
        well_row_letter = well_name[0:1]
        row_num = letter_to_row_num_dict[well_row_letter]
        col_num = int(well_name[1:])
        index = (col_num-1)*8 + row_num
        return index

    def get_tip_columns(n_columns):
        '''
        Returns a list of wells to pick up from and to park tips to
        for multi-channel pipettes (i.e. the function returns tip wells
        from the 1st row (A row)). The function returns a list of wells in
        the top row that contains 8 tips. The purpose of this function is to
        facilitate tip parking.

        :param n_columns: How many tip columns to use for tip parking
        '''
        nonlocal tipracks, ctx, m300
        columns_left = n_columns
        tip_list = []
        for rack in tipracks:
            next_tip = rack.next_tip(8)
            if next_tip is not None:
                col_num = int(next_tip.well_name[1:])
                end_col = columns_left if columns_left + col_num < 12 else 12
                for col in rack.columns()[col_num-1:end_col]:
                    if not col[0].has_tip:
                        # Not enough tips left?:
                        # Refill tipracks and call the function recursively
                        # and return tips from the start of the racks
                        ctx.pause("Please refill all tipracks")
                        m300.reset_tipracks()
                        return get_tip_columns(n_columns)
                    tip_list.append(col[0])
                columns_left -= 12-col_num
        return tip_list

    def get_tip_wells(n_tips):
        '''
        Returns a list of wells to pick up from and to park tips to
        for single-channel pipettes. The function returns a list of well
        locations that have tips.
        The purpose of this function is to facilitate tip parking

        :param n_tips: How many tips to use for tip parking
        '''

        nonlocal tipracks, ctx, p300
        wells_left = n_tips
        tip_list = []
        for rack in tipracks:
            next_tip = rack.next_tip(1)
            if next_tip is not None:
                well_index = get_well_index_by_name(next_tip.well_name)
                tips = rack.wells()[well_index:]
                for tip in tips:
                    if tip.has_tip:
                        tip_list.append(next_tip)
                        wells_left -= 1
                        if wells_left < 1:
                            break
                if wells_left < 1:
                    break
        if wells_left < 1:
            return tip_list
        else:
            ctx.pause("Please refill all tipracks")
            p300.reset_tipracks()
            return get_tip_wells(n_tips)

    # Volume Tracking
    class VolTracker:
        def __init__(self, labware, well_vol,
                     start=0, end=8,
                     mode='reagent',
                     pip_type='single',
                     msg='Reset labware volumes'):
            """
            Voltracker tracks the volume(s) used in a piece of labware

            :param labware: The labware to track
            :param well_vol: The volume of the liquid in the wells
            :param pip_type: The pipette type used 'single' or 'multi'
            :param mode: 'reagent' or 'waste'
            :param start: The starting well
            :param end: The ending well
            :param msg: Message to send to the user when all wells are empty

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

        def track(self, vol):
            '''track() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the reservoir.'''
            well = next(iter(self.labware_wells))
            vol = vol * 8 if self.pip_type == 'multi' else vol
            if self.labware_wells[well] + vol >= self.well_vol:
                del self.labware_wells[well]
                if len(self.labware_wells) < 1:
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
    # reagents

    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''
    trash = m300.trash_container.wells()[0].top()  # trash container

    # 32 samples at 400 uL requires almost one full 2 mL tube
    if is_protk_tube:
        prot_k_tracker = VolTracker(tuberack, two_ml_tube_max_vol,
                                    pip_type='single', start=1, end=1,
                                    msg='Replenish proteinase K buffer in ' +
                                    'the tuberack on deck slot 7, tube 1')
    else:
        prot_k_tracker = VolTracker(twelve_well_resv, twelve_well_max_vol,
                                    pip_type='multi', start=1, end=1,
                                    msg='Replenish proteinase K buffer in '
                                    '12 well reservoir on deck slot 2, well 1')

    lysis_lbb_tracker = VolTracker(twelve_well_resv, twelve_well_max_vol,
                                   pip_type='multi', start=2, end=3,
                                   msg='Replenish Lysis LBB buffer in \
                                   12 well reservoir on deck slot 4, \
                                   well 2 and 3')

    bind_bbb_tracker = VolTracker(twelve_well_resv, twelve_well_max_vol,
                                  pip_type='multi', start=4, end=5,
                                  msg='Replenish Bind BBB buffer in \
                                  12 well reservoir on deck slot 4 \
                                  in well 4 and 5')
    if is_eb_tube:
        elution_buf_tracker = VolTracker(twelve_well_resv, twelve_well_max_vol,
                                         pip_type='single', start=2, end=8,
                                         msg='Replenish elution buffer in' +
                                         'the tuberack on deck slot 7 ' +
                                         'in well 2 to 8')
    else:
        elution_buf_tracker = VolTracker(twelve_well_resv, twelve_well_max_vol,
                                         pip_type='multi', start=6, end=7,
                                         msg='Replenish elution buffer in \
                                         12 well reservoir on deck slot 4 \
                                         in well 6 and 7')

    wash_wbb_tracker = VolTracker(wash_wbb_resv, one_well_max_vol,
                                  pip_type='multi', start=1, end=1,
                                  msg='Replenish Wash WBB buffer in \
                                  reservoir on deck slot 2')

    wash_wbc_tracker = VolTracker(wash_wbc_resv, one_well_max_vol,
                                  pip_type='multi', start=1, end=1,
                                  msg='Replenish Wash WBB buffer in \
                                  reservoir on deck slot 2')

    liq_trash_tracker = VolTracker(trash_resv_1, trash_max_vol,
                                   pip_type='multi', mode='waste',
                                   start=1, end=1, msg='Empty liquid waste')
    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''
    sample_columns = sample_plate.columns()[0:n_sample_columns]
    destination_columns = destination_plate.columns()[0:n_sample_columns]
    sample_wells = sample_plate.wells()[0:n_samples]
    # Protocol

    '''

    Include header sections as follows for each "section" of your ctx.

    Section can be defined as a step in a bench ctx.

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

    # step 1 - Add 2 samples volumes + 100 uL of lysis buffer BBB
    ctx.comment("\n\nStep 1: Adding Lysis BBB to samples\n")
    for col in sample_columns:
        m300.transfer(lysis_buf_lbb_vol,
                      lysis_lbb_tracker.track(lysis_buf_lbb_vol), col[0])

    # step 2 - Add proteinase K to samples and mix 10 times gently to
    # prevent bubble formation
    ctx.comment("\n\nStep 2: Adding Proteinase K and mixing\n")
    total_well_vol = sample_vol + lysis_buf_lbb_vol + prot_k_vol
    mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
    if is_protk_tube:
        for well in sample_wells:
            pick_up(p300)
            p300.transfer(prot_k_vol, prot_k_tracker.track(prot_k_vol),
                          well, new_tip='never')
            p300.mix(10, mix_vol, col[0], 1/2)
            p300.drop_tip()
    else:
        for col in sample_columns:
            pick_up(m300)
            m300.transfer(prot_k_vol, prot_k_tracker.track(prot_k_vol),
                          col[0], new_tip='never')
            # Mix slowly to prevent bubble formation
            m300.mix(10, mix_vol, col[0], 1/2)
            m300.drop_tip()

    # Step 3 - Incubate the samples with the buffer and enzyme
    ctx.comment("\n\nStep 3: Incubating samples\n")
    ctx.comment("Incubation step: Seal the sample plate and incubate " +
                "samples for 10 minutes at 37 C or 30 minutes at room " +
                "temperature (see bench protocol step 3)")

    ctx.pause("Resume when the sample plate has been reinserted " +
              "on the mag deck and the Bind BBB buffer has been vortexed " +
              "or inverted 20 times and added to the 12 well reservoir")

    # Step 4 - Add Bind BBB buffer and mix gently
    ctx.comment("\n\nStep 4: Adding Bind BBB and mixing\n")
    total_well_vol += bind_bbb_vol
    mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
    bbb_vol_used = 0
    for col in sample_columns:
        pick_up(m300)
        m300.transfer(bind_bbb_vol, bind_bbb_tracker.track(bind_bbb_vol),
                      col[0], new_tip='never')
        bbb_vol_used += bind_bbb_vol
        m300.mix(10, mix_vol, col[0], 1/3)
        m300.drop_tip()

    # Step 5 - Incubate samples for 5 minutes
    ctx.comment("\n\nStep 5: Incubating samples with Bind BBB\n")
    ctx.comment('Beginning 5 minutes incubation at room temperature')
    ctx.delay(minutes=5)

    # Step 6 - Engage magnets for 15 minutes
    ctx.comment("\n\nStep 6: Engaging magnets for 15 minutes\n")
    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=15)

    # step 7 - Aspirate off the supernatant and dump it in the waste
    ctx.comment("\n\nStep 7: Transferring supernantant to waste\n")
    remove_supernatant(total_well_vol)
    total_well_vol = 0

    # Step 8 through 11: Wash the beads two times using Wash WBB buffer
    ctx.comment("\n\nStep 8-11: Washing beads with Wash WBB\n")
    wash(wash_wbb_vol, wash_wbb_tracker, 10, 20, "Wash WBB")

    # Steps 12-15 - Disengage magnets and wash with buffer "Wash WBC"
    # Engage magnets, and discard supernatant - repeat 2x
    ctx.comment("\n\nStep 12-15: Washing beads with Wash WBC\n")
    wash(wash_wbc_vol, wash_wbc_tracker, 10, 20, "Wash WBC")

    # Step 16 - Add elution buffer and mix
    ctx.comment("\n\nStep 16: Adding elution buffer to samples and mixing\n")
    total_well_vol = elution_buffer_vol
    if is_eb_tube:
        tips = get_tip_wells(len(sample_wells))
        for well, tip_well in zip(sample_wells, tips):
            p300.pick_up_tip(tip_well)
            p300.transfer(elution_buffer_vol,
                          elution_buf_tracker.track(elution_buffer_vol), well,
                          new_tip='never')
            mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
            p300.mix(10, mix_vol)
            p300.touch_tip()
            p300.drop_tip(tip_well)

        # Step 17 - Incubate samples for two minutes and mix with parked tips
        ctx.comment("\n\nStep 17: Incubating samples and mixing 2nd time\n")
        ctx.delay(minutes=2)
        for well, tip_well in zip(sample_wells, tips):
            p300.pick_up_tip(tip_well)
            mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
            p300.mix(10, mix_vol, well)
            p300.touch_tip()
            p300.drop_tip()
    else:
        tips = get_tip_columns(len(sample_columns))
        for col, tip_well in zip(sample_columns, tips):
            m300.pick_up_tip(tip_well)
            m300.transfer(elution_buffer_vol,
                          elution_buf_tracker.
                          track(elution_buffer_vol), col[0],
                          new_tip='never')
            mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
            m300.mix(10, mix_vol)
            m300.touch_tip()
            m300.drop_tip(tip_well)

        # Step 17 - Incubate samples for two minutes and mix with parked tips
        ctx.comment("\n\nStep 17: Incubating samples and mixing 2nd time\n")
        ctx.delay(minutes=2)
        for col, tip_well in zip(sample_columns, tips):
            m300.pick_up_tip(tip_well)
            mix_vol = 200 if total_well_vol - 10 > 200 else total_well_vol - 10
            m300.mix(10, mix_vol, col[0])
            m300.touch_tip()
            m300.drop_tip()

    # Step 18 - Engage magnets (5 min) and transfer
    # the eluted material from the sample plate to the destination plate
    ctx.comment('\n\nStep 18: Engaging magnets and transferring eluted ' +
                'samples to the destination plate\n')
    mag_mod.engage(height_from_base=mag_height)
    ctx.delay(minutes=5)
    for s_col, d_col, side in zip(sample_columns, destination_columns, sides):
        remainining_volume = elution_buffer_vol
        pick_up(m300)
        while remainining_volume > 0:
            vol = (200 if remainining_volume > 200 else
                   remainining_volume)
            m300.aspirate(vol,
                          s_col[0].bottom().move(
                            types.Point(x=side, y=0, z=1)))

            m300.dispense(vol, d_col[0])
            remainining_volume -= vol
        m300.touch_tip()
        m300.drop_tip()
    ctx.comment("\n\n ~~~~ End of protocol ~~~~\n")
