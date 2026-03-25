from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Generic protein purification protocol',
    'author': 'Opentrons <authoremail@company.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):
    [
        mag_engage_time,
        n_samples,
        left_pipette_lname,
        right_pipette_lname,
        left_pipette_tipracks_lname,
        right_pipette_tipracks_lname,
        reservoir_lname,
        destination_plate_lname,
        sample_plate_lname,
        mag_mod_lname,
        tube_rack_lname,
        dest_temp_mod_lname,
        do_vortex_pause,
        do_SDS_step,
        do_DNAse_step,
        use_NaCl,
        bead_volume,
        wash_buf_vol,
        elution_buf_vol,
        n_washes,
        n_wash_mixes,
        n_elution_mixes,
        incubation_time,
        n_bead_mixes,
        sds_buffer_vol,
        starting_volume
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "mag_engage_time",
        "n_samples",
        "left_pipette_lname",
        "right_pipette_lname",
        "left_pipette_tipracks_lname",
        "right_pipette_tipracks_lname",
        "reservoir_lname",
        "destination_plate_lname",
        "sample_plate_lname",
        "mag_mod_lname",
        "tube_rack_lname",
        "dest_temp_mod_lname",
        "do_vortex_pause",
        "do_SDS_step",
        "do_DNAse_step",
        "use_NaCl",
        "bead_volume",
        "wash_buf_vol",
        "elution_buf_vol",
        "n_washes",
        "n_wash_mixes",
        "n_elution_mixes",
        "incubation_time",
        "n_bead_mixes",
        "sds_buffer_vol",
        "starting_volume"
        )

    # define all custom variables above here with descriptions:

    # Calculate reagent volumes
    # See docs for calculations
    # 10:1, v_lysis = v_s/9, e.g. for v_s = 1000 uL, v_lysis = 1000/9=111 uL
    lysis_buffer_vol = starting_volume/9
    dnaseI_vol = starting_volume/1000  # 1 uL per mL
    total_lysis_vol = starting_volume + lysis_buffer_vol + dnaseI_vol

    nacl_first_step_vol = total_lysis_vol/7
    nacl_wash_buf_vol = wash_buf_vol/7

    total_vol_after_bead_adddn = round(total_lysis_vol + bead_volume, 1)
    if use_NaCl:
        total_vol_after_bead_adddn = round(total_vol_after_bead_adddn +
                                           nacl_first_step_vol, 1)

    n_columns = math.ceil(n_samples/8)

    # Error checking
    # If DNAse I is being added from a tube we need to make sure that
    # a) we have a single pipette loaded and b) that dnaseI_vol > pipette min.
    # volume
    if (("single" not in left_pipette_lname and
         "single" not in right_pipette_lname) and do_DNAse_step):
        raise Exception("No single channel pipette for DNAse I distribution " +
                        "selected")
    # More error checking on this in the pipette loading section

    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''
    # Load temperature modules (if any)
    dest_temp_mod = None
    if dest_temp_mod_lname:
        dest_temp_mod = ctx.load_module(dest_temp_mod_lname, '4')

    # Load the magnetic module
    mag_mod = ctx.load_module(mag_mod_lname, '1')

    # Load labware
    sample_plate = mag_mod.load_labware(sample_plate_lname)

    sample_well = sample_plate.wells()[0]
    if total_vol_after_bead_adddn > sample_well.max_volume:
        raise Exception("The sample wells are too small to handle the " +
                        "volumes of reagents")

    reservoir = ctx.load_labware(reservoir_lname, '7')

    dnaseI_tuberack = None
    if do_DNAse_step:
        dnaseI_tuberack = ctx.load_labware(tube_rack_lname, '10')

    dest_plate = None
    if dest_temp_mod_lname:
        dest_plate = dest_temp_mod.load_labware(destination_plate_lname)
    else:
        dest_plate = ctx.load_labware(destination_plate_lname, '4')

    # load tipracks
    tipracks_left, tipracks_right = [None] * 2
    if left_pipette_tipracks_lname:
        tipracks_left = [ctx.load_labware(left_pipette_tipracks_lname, slot)
                         for slot in ['5', '8', '11']]
    if right_pipette_tipracks_lname:
        tipracks_right = [ctx.load_labware(right_pipette_tipracks_lname, slot)
                          for slot in ['6', '9']]

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
    left_pip = None
    right_pip = None
    pipette = None  # Remains None if there are two pipettes loaded
    if left_pipette_lname:
        left_pip = ctx.load_instrument(
                                left_pipette_lname,
                                "left",
                                tip_racks=tipracks_left
                                )
    if right_pipette_lname:
        right_pip = ctx.load_instrument(
                                right_pipette_lname,
                                "right",
                                tip_racks=tipracks_right
                                )
    if not (right_pip and left_pip):
        if right_pip:
            pipette = right_pip
        else:
            pipette = left_pip

    # Rank the pipettes by minimum volume
    s_pip, l_pip = [None]*2
    if pipette:
        s_pip, l_pip = [pipette, pipette]
    else:
        if left_pip.min_volume < right_pip.min_volume:
            s_pip, l_pip = [left_pip, right_pip]
        else:
            s_pip, l_pip = [right_pip, left_pip]

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
    def choose_pipette(vol, multi_action=True):
        """
        Choose pipette selects an appropriate pipette based on
        the volume involved, and whether the pipette action involves all
        8 columns or a single well.

        :param vol: The volume to use this pipette with
        :param multi_action: True if the pipette action will be done with
        an 8-channel pipette, i.e. involving an 8-channel source and/or target

        """
        nonlocal s_pip, l_pip, pipette
        # Case when only one pipette has been loaded
        if pipette:
            if pipette.min_volume < vol:
                raise Exception(("\n\nThe loaded pipette has a minimum "
                                 "volume of {} which is greater than {}. " +
                                 "Consider adding a smaller volume pipette\n")
                                .format(pipette.min_volume, vol))
            if pipette.channels == 8:
                return pipette, True
            else:
                return pipette, False

        s_pip_is_multi = True if s_pip.channels == 8 else False
        l_pip_is_multi = True if l_pip.channels == 8 else False

        if s_pip.min_volume > vol:
            raise Exception(("The volume ({} uL)is too small to handle for " +
                             "either pipette, please re-examine your" +
                             "parameters").format(vol))

        # The preference is for the multi-channel pipette with the largest
        # volume capability while the least preferred is the smallest volume
        # single channel pipette.
        if multi_action:
            # Prefer the multi-channel pipettes if available
            if l_pip_is_multi and l_pip.min_volume < vol:
                return l_pip, True
            elif s_pip_is_multi:
                return s_pip, True
            # If they are not, let a single channel pipette do the job of a
            # multi-channel pipette
            elif not l_pip_is_multi and l_pip.min_volume < vol:
                return l_pip, False
            else:
                return s_pip, False
        else:
            if not l_pip_is_multi and l_pip.min_volume < vol:
                return l_pip, False
            elif not s_pip_is_multi:
                return s_pip, False
            else:
                raise Exception(("No approriate single channel pipette is " +
                                "loaded for the volume of {} uL".format(vol)))

    def transfer(pip, volume, source, dest, **kwargs):
        """
        A wrapper function for InstrumentContext.transfer that handles
        labware.OutOfTipsError by asking the user to refill empty tipracks.

        :param pip: The pipette to user for the transfer

        Other parameters: See class
        opentrons.protocol_api.contexts.InstrumentContext
        """
        try:
            pip.transfer(volume, source, dest, **kwargs)
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("\n\nReplace empty tip racks for {}\n".format(pip.name))
            pip.reset_tipracks()
            pip.transfer(volume, source, dest, **kwargs)

    def reag_to_wells_or_col_transfer(vol, reag_source_well, dest_plate,
                                      multi_transfer=True, **transfer_kwargs):
        """
        function description

        :param vol:

        :param index:
        """
        nonlocal n_columns, n_samples
        pip, pip_is_multi = choose_pipette(vol, multi_transfer)

        if pip_is_multi:
            dest_columns = dest_plate.columns()[0:n_columns]
            for col in dest_columns:
                transfer(pip, vol, reag_source_well, col[0],
                         **transfer_kwargs)
        else:  # Transfer to each well
            transfer(pip, vol, reag_source_well,
                     dest_plate.wells()[0:n_samples],
                     **transfer_kwargs)

    def remove_supernatant(vol, source_plate, multi_transfer=True,
                           **transfer_kwargs):
        """
        Removes a volume from each sample well of the source plate
        (well 0 to well n_samples) and transfers it to the liquid trash
        well of the reservoir.

        :param vol (float): The volume to transfer to the trash.

        :param source_plate (labware plate): The plate to aspirate from.

        :param multi_transfer (Boolean): Use 8-channel pipette and transfer
        a whole column at a time if true, otherwise use a single channel
        pipette and transfer well by well.

        :param **transfer_kwargs: Any keyword arguments that you may want
        to pass into the transfer method calls
        """
        nonlocal n_columns, n_samples
        pip, pip_is_multi = choose_pipette(vol, multi_transfer)

        if pip_is_multi:
            source_columns = source_plate.columns()[0:n_columns]
            for col in source_columns:
                transfer(pip, vol, col[0], waste_well, **transfer_kwargs)
        else:  # Transfer from each well
            transfer(pip, vol, source_plate.wells()[0:n_samples],
                     waste_well, **transfer_kwargs)

    def transfer_plate_to_plate(vol, source_plate, destination_plate):
        pip, is_multi = choose_pipette(vol, True)
        if is_multi:
            for s_col, d_col in zip(source_plate.columns(),
                                    destination_plate.columns()):
                transfer(pip, vol, s_col[0], d_col[0])
        else:
            transfer(pip, vol, sample_wells, dest_wells)

    # reagents

    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''

    lysis_buffer_well = reservoir.wells_by_name()['A1']
    wash_buffer_well = reservoir.wells_by_name()['A2']
    elution_buffer_well = reservoir.wells_by_name()['A3']
    nacl_well = reservoir.wells_by_name()['A4']
    bead_well = reservoir.wells_by_name()['A5']
    waste_well = reservoir.wells()[-1].top(-2)
    dnaseI_tube = None
    if dnaseI_tuberack:
        dnaseI_tube = dnaseI_tuberack.wells_by_name()['A1']
    sds_page_buf_well = None
    if do_SDS_step:
        sds_page_buf_well = reservoir.wells_by_name()['A6']

    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''
    sample_wells = sample_plate.wells()[0:n_samples]

    dest_columns = dest_plate.columns()[0:n_columns]
    dest_wells = dest_plate.wells()[0:n_samples]

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
    ctx.comment('\n\nAdding lysis buffer to samples\n')
    pip, pip_is_multi = choose_pipette(lysis_buffer_vol)

    reag_to_wells_or_col_transfer(lysis_buffer_vol, lysis_buffer_well,
                                  sample_plate, True)

    if do_DNAse_step:
        ctx.comment('\n\nAdding DNAse I to sample wells\n')
        # Must be single channel, protocol will raise exception otherwise
        reag_to_wells_or_col_transfer(dnaseI_vol, dnaseI_tube, sample_plate,
                                      False)

    ctx.pause("\n\nPlace sample plate on a shaker and shake for 10-20" +
              " minutes at room temperature for the lysis reaction" +
              " to complete\n")

    # Optional addition of NaCl for improved binding to beads
    if use_NaCl:
        ctx.comment("Adding NaCl to samples for a final conc. of 500 mM")
        reag_to_wells_or_col_transfer(nacl_first_step_vol, nacl_well,
                                      sample_plate, True)

    if do_vortex_pause:
        ctx.pause("Pause to vortex/resuspend your magnetic beads")

    # Mixing the beads in the bead well
    pick_up(l_pip)
    l_pip.mix(n_bead_mixes, l_pip.max_volume, bead_well)

    ctx.comment("\n\nTransferring bead solution to sample wells and mixing")
    pip, pip_is_multi = choose_pipette(bead_volume, True)
    if pip_is_multi:
        for col in dest_columns:
            if not pip.has_tip:
                pick_up(pip)
            pip.aspirate(bead_volume, bead_well)
            pip.dispense(bead_volume, col[0])
            mix_vol = (pip.max_volume if total_vol_after_bead_adddn/2 >
                       pip.max_volume else total_vol_after_bead_adddn/2)
            pip.mix(5, mix_vol, col[0])
            pip.drop_tip()
    else:
        for well in sample_wells:
            if not pip.has_tip:
                pick_up(pip)
            pip.aspirate(bead_volume, bead_well)
            pip.dispense(bead_volume, well)
            mix_vol = (pip.max_volume if total_vol_after_bead_adddn/2 >
                       pip.max_volume else total_vol_after_bead_adddn/2)
            pip.mix(5, mix_vol, well)
            pip.drop_tip()

    ctx.comment("\n\nIncubating beads\n")
    ctx.delay(0, incubation_time)
    ctx.comment("\n\nEngaging magnets\n")
    mag_mod.engage()
    ctx.delay(0, mag_engage_time)
    ctx.comment("\n\nRemoving supernatant\n")
    remove_supernatant(total_vol_after_bead_adddn, sample_plate)

    # Wash the beads n_washes times, the standard is 3 washes
    repetitions = 1 if do_SDS_step else n_washes
    for i in range(0, repetitions):
        ctx.comment("\n\nBead wash #{}".format(i + 1))
        mag_mod.disengage()
        # Transfer wash buffer to the sample wells
        supernatant_volume = (wash_buf_vol + nacl_wash_buf_vol if use_NaCl
                              else wash_buf_vol)
        half_supernatant_vol = supernatant_volume/2
        mix_vol = (half_supernatant_vol if half_supernatant_vol
                   < l_pip.max_volume else l_pip.max_volume)
        if use_NaCl:
            reag_to_wells_or_col_transfer(wash_buf_vol, wash_buffer_well,
                                          sample_plate, True)
            reag_to_wells_or_col_transfer(nacl_wash_buf_vol, nacl_well,
                                          sample_plate, True,
                                          mix_after=(n_wash_mixes, mix_vol))
        else:
            reag_to_wells_or_col_transfer(wash_buf_vol, wash_buffer_well,
                                          sample_plate, True,
                                          mix_after=(n_wash_mixes, mix_vol))
        mag_mod.engage()
        ctx.delay(0, mag_engage_time)
        # Remove supernatant
        remove_supernatant(supernatant_volume, sample_plate)

    mag_mod.disengage()

    if do_SDS_step:
        ctx.comment("\n\nAdding 1x SDS-PAGE buffer\n")
        reag_to_wells_or_col_transfer(sds_buffer_vol, sds_page_buf_well,
                                      sample_plate, True)
        mag_mod.engage()
        ctx.delay(0, mag_engage_time)
        # Transfer to target plate
        ctx.comment("\n\nTransferring protein in SDS-buffer to target plate\n")
        transfer_plate_to_plate(sds_buffer_vol, sample_plate, dest_plate)
    # Elute
    else:
        ctx.comment("\n\nAdding elution buffer and mixing\n")
        reag_to_wells_or_col_transfer(elution_buf_vol, elution_buffer_well,
                                      sample_plate, True,
                                      mix_after=(n_elution_mixes, mix_vol))
        ctx.comment("\n\nIncubating samples with elution buffer\n")
        ctx.delay(0, incubation_time)
        ctx.comment("\n\nAttracting beads to magnets\n")
        mag_mod.engage()
        ctx.delay(0, mag_engage_time)
        ctx.comment("\n\nTransferring protein elution supernatant to" +
                    "target plate\n")
        transfer_plate_to_plate(elution_buf_vol, sample_plate, dest_plate)
    ctx.comment("\n\n~~~~~ End of protocol ~~~~~\n")
