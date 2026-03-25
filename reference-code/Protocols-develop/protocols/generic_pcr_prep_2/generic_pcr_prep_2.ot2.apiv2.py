import math
from opentrons import protocol_api
from opentrons.protocol_api.contexts import InstrumentContext

metadata = {
    'protocolName': 'Generic PCR Prep Part 2 - Mastermix and DNA Distribution',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.11'
    }


def run(ctx: protocol_api.ProtocolContext):

    [n_samples,
     n_mixes,
     aspiration_rate_multiplier,
     dispensation_rate_multiplier,
     left_pipette_lname,
     right_pipette_lname,
     use_filter_tips_left,
     use_filter_tips_right,
     mastermix_volume,
     DNA_volume,
     mastermix_reservoir_lname,
     DNA_well_plate_lname,
     destination_well_plate_lname,
     DNA_well_plate_tmod,
     dest_well_plate_tmod] = get_values(  # noqa: F821
     "n_samples",
     "n_mixes",
     "aspiration_rate_multiplier",
     "dispensation_rate_multiplier",
     "left_pipette_lname",
     "right_pipette_lname",
     "use_filter_tips_left",
     "use_filter_tips_right",
     "mastermix_volume",
     "DNA_volume",
     "mastermix_reservoir_lname",
     "DNA_well_plate_lname",
     "destination_well_plate_lname",
     "DNA_well_plate_tmod",
     "dest_well_plate_tmod")

    # Error checking --------------------------------------------------------
    if not left_pipette_lname and not right_pipette_lname:
        raise Exception('You have to select at least 1 pipette.')

    if not (DNA_volume > 0 or mastermix_volume > 0):
        raise Exception("DNA or mastermix volume is 0 or less µL, please "
                        "re-examine your volume parameters")

    if "aluminum" not in destination_well_plate_lname and dest_well_plate_tmod:
        raise Exception("The destination plate must be loaded on an "
                        "aluminum block in order to be used with a "
                        "temperature module")

    if "aluminum" not in DNA_well_plate_lname and DNA_well_plate_tmod:
        raise Exception("The DNA template plate must be loaded on an "
                        "aluminum block in order to be used with a "
                        "temperature module")

    assert aspiration_rate_multiplier > 0, \
        "The aspiration flow-rate multiplier must be greater than zero"

    assert dispensation_rate_multiplier > 0, \
        "The dispensation flow-rate multiplier must be greater than zero"

    assert n_samples > 0, "There must be at least one sample"
    # Error checking on n_samples <= number of wells on destination plate
    # is at the beginning of the protocol code because it requires loading
    # the plates.
    # The code is copied here for reference:
    """
    if n_wells_dest < n_samples:
        raise Exception("The destination plate does not have enough wells ({})"
                        "for all the samples ({}). Check your number of "
                        "samples parameter".
                        format(n_wells_dest, n_samples))
    """

    assert left_pipette_lname or right_pipette_lname, \
        "Load at least one pipette"

    # End error checking ---------------------------------------------------

    mastermix_resv_slot = '3'
    dest_plate_slot = '6'
    tiprack_l_slots = ['4', '7', '10']
    tiprack_r_slots = ['5', '8']
    DNA_plate_slots = ['9', '1', '2', '11']
    n_plates = math.ceil(n_samples/96)

    # load modules
    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note : if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''

    tmod_list = []
    for tmod_lname, slot in zip([DNA_well_plate_tmod, dest_well_plate_tmod],
                                [DNA_plate_slots[0], dest_plate_slot]):
        if tmod_lname:
            tmod = ctx.load_module(tmod_lname, slot)
            tmod_list.append(tmod)
        else:
            tmod_list.append(None)
    tmod_dna_plate, tmod_dest_plate = tmod_list
    '''


    Add your labware here with:
    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''

    # labware setup
    plate_list = []
    for labware_lname, tmod, slot, name in \
        zip([DNA_well_plate_lname, destination_well_plate_lname],
            [tmod_dna_plate, tmod_dest_plate],
            [DNA_plate_slots[0], dest_plate_slot],
            ["DNA plate 1", "destination plate"]):
        if tmod:
            plate_list.append(tmod.load_labware(labware_lname, name))
        else:
            plate_list.append(ctx.load_labware(labware_lname, slot, name))

    DNA_well_plate_1, destination_well_plate = plate_list
    DNA_well_plates = [DNA_well_plate_1]
    for i, slot in enumerate(DNA_plate_slots[1:n_plates]):
        DNA_well_plates.append(ctx.load_labware(DNA_well_plate_lname, slot,
                                                "DNA plate {}".format(i+2)))

    mastermix_reservoir = ctx.load_labware(mastermix_reservoir_lname,
                                           mastermix_resv_slot,
                                           'mastermix reservoir')
    # load tipracks
    '''


    Add your tipracks here as a list:

    For
    a single tip rack:
    tiprack_name = [ctx.load_labware('{loadname}', '{slot number}')]

    For multiple tip racks of the same type:

    tiprack_name = [ctx.load_labware('{loadname}', 'slot')
                     for slot in ['1', '2', '3']]

    If two different tipracks are on the deck, use convention:
    tiprack[ number of microliters]
    e. g. tiprack10, tiprack20, tiprack200, tiprack300, tiprack1000
    '''

    tiprack_lnames = {
        "p20s_filtered": "opentrons_96_filtertiprack_20ul",
        "p20s_nonfiltered": "opentrons_96_tiprack_20ul",
        "p300s_filtered": "opentrons_96_filtertiprack_200ul",
        "p300s_nonfiltered": "opentrons_96_tiprack_300ul",
        "p1000s_filtered": "opentrons_96_filtertiprack_1000ul",
        "p1000s_nonfiltered": "opentrons_96_tiprack_1000ul"
    }

    # Helper function for loading tipracks
    def load_tipracks(tiprack_list, filtered_tips, non_filtered_tips,
                      is_filtered, slot):
        tip_type = filtered_tips if is_filtered else non_filtered_tips
        tiprack_list.append(ctx.load_labware(tip_type, slot))

    def process_tipracks(pip_lname, is_filtered, slot, tiprack_list):
        if "20_" in pip_lname or "10_" in pip_lname:
            load_tipracks(tiprack_list, tiprack_lnames["p20s_filtered"],
                          tiprack_lnames["p20s_nonfiltered"], is_filtered,
                          slot)
        elif "300_" in pip_lname or "50_" in pip_lname:
            load_tipracks(tiprack_list, tiprack_lnames["p300s_filtered"],
                          tiprack_lnames["p300s_nonfiltered"], is_filtered,
                          slot)
        elif "1000_" in pip_lname:
            load_tipracks(tiprack_list, tiprack_lnames["p1000s_filtered"],
                          tiprack_lnames["p1000s_nonfiltered"], is_filtered,
                          slot)
        else:
            raise Exception("The pipette loadname does not match any tipracks "
                            "the loadname was {}".format(pip_lname))

    tiprack_list = []
    tipracks_l, tipracks_r = None, None

    if left_pipette_lname and not right_pipette_lname:
        tiprack_slots = tiprack_l_slots + tiprack_r_slots
        for slot in tiprack_slots:
            process_tipracks(left_pipette_lname, use_filter_tips_left,
                             slot, tiprack_list)
            tipracks_l = tiprack_list
    elif not left_pipette_lname and right_pipette_lname:
        tiprack_slots = tiprack_l_slots + tiprack_r_slots
        for slot in tiprack_slots:
            process_tipracks(right_pipette_lname, use_filter_tips_left,
                             slot, tiprack_list)
            tipracks_r = tiprack_list
    else:
        for pip_lname, is_filtered, slots \
            in zip([left_pipette_lname, right_pipette_lname],
                   [use_filter_tips_left, use_filter_tips_right],
                   [tiprack_l_slots, tiprack_r_slots]):
            for i in range(len(slots)):
                process_tipracks(pip_lname, is_filtered,
                                 slots[i], tiprack_list)
        tipracks_l = tiprack_list[0:len(tiprack_l_slots)]
        tipracks_r = tiprack_list[len(tiprack_l_slots):len(tiprack_l_slots)
                                  + len(tiprack_r_slots)]
    # load instrument
    '''
    Nomenclature for pipette:

    use 'p' for single-channel, 'm' for multi-channel,
    followed by number of microliters.

    p20, p300, p1000 (single channel pipettes)
    m20, m300 (multi-channel pipettes)

    If loading pipette, load with:
    ctx.load_instrument('{pipette api load name}',
                        pipette_mount("left", or "right"),
                        tip_racks= tiprack )
    '''

    pipettes = []
    for pip, mount, tiprack in zip([left_pipette_lname,
                                    right_pipette_lname],
                                   ["left", "right"],
                                   [tipracks_l, tipracks_r]):
        if pip:
            pipettes.append(ctx.load_instrument(
                pip, mount, tip_racks=tiprack))
        else:
            pipettes.append(None)

    for pip in pipettes:
        if pip is not None:
            pip.flow_rate.aspirate *= aspiration_rate_multiplier
            pip.flow_rate.dispense *= dispensation_rate_multiplier
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
    the function.
    '''
    def is_multi_channel(pip): return True if pip.channels == 8 else False

    def mix(pipette: InstrumentContext, n_mixes, vol, location):
        if n_mixes == 0:
            return
        else:
            pipette.mix(n_mixes, vol, location)

    def pick_up_tip(pipette):
        """
        Safe function for picking up tips in that it checks for tip
        availability and asks user to replace tips if the tipracks
        have run empty.

        :param pipette: Pipette to pick up tip with
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    def rank_pipettes(pipettes):
        """
        Given a list of 1 to 2 pipettes this fn will return them in the order
        of smallest to largest. This function assumes that error checking for
        cases where no pipettes were loaded was already done.
        """
        if pipettes[1] is None:
            return [pipettes[0], pipettes[0]]
        elif pipettes[0] is None:
            return [pipettes[1], pipettes[1]]
        elif len(pipettes) == 2:
            if pipettes[0].max_volume <= pipettes[1].max_volume:
                return [pipettes[0], pipettes[1]]
            else:
                return [pipettes[1], pipettes[0]]
        else:
            raise Exception("Unexpected number of pipettes loaded: {}".
                            format(len(pipettes)))

    def pipette_selector(small_pipette, large_pipette, volume):
        """
        This function will try to return a multi-channel pipette that
        can handle the given volume, and failing that a single channel pip.
        """
        assert small_pipette.max_volume \
            <= large_pipette.max_volume, ("Pipette argument error, small pip's"
                                          " max volume should be less than or "
                                          "equal to the large pip's")
        if small_pipette.min_volume <= volume <= small_pipette.max_volume \
                and is_multi_channel(small_pipette):
            return small_pipette
        elif large_pipette.min_volume <= volume \
                and is_multi_channel(large_pipette):
            return large_pipette
        elif small_pipette.min_volume <= volume <= small_pipette.max_volume:
            return small_pipette
        elif large_pipette.min_volume <= volume:
            return large_pipette
        else:
            raise Exception("No suitable pipette for a volume of {} loaded".
                            format(volume))

    # helper functions
    ''' Define any custom helper functions outside of the pipette scope here,
    using the convention seen above.
    e.g.
    def
        remove_supernatant(vol, index):
        """
        function description
        : param vol:
        : param index:
        """

    '''

    def single_channel_resv_transfer(pipette, vol, source_well, dest_plate,
                                     n_samples, drop_tips=False):
        """
        This function transfers a volume of liquid from a single source well
        (e.g. a reservoir) to a destination plate using a single channel
        pipette
        :param pipette: The pipette to use for transferring liquid
        :param vol: The volume for each liquid transfer
        :param source_well: The source well to aspirate from, i.e. the
        reservoir well containing mastermix
        :param dest_plate: well plate to transfer to
        :param n_samples: How many transfers to perform
        :param drop_tips: Whether to drop tips after each transfer and pick
        up new ones, or reuse the same tips
        """
        if not drop_tips:
            pick_up_tip(pipette)
        for well in dest_plate.wells()[:n_samples]:
            if drop_tips:
                pick_up_tip(pipette)
            pipette.aspirate(vol, source_well)
            pipette.dispense(vol, well)
            if drop_tips:
                pipette.drop_tip()
        if not drop_tips:
            pipette.drop_tip()

    def single_channel_plate_transfer(pipette, vol, source_plate, dest_plate,
                                      n_mixes, mix_vol, n_transfers, offset=0):
        for s_well, d_well in zip(source_plate.wells()[:n_transfers],
                                  dest_plate.wells()
                                  [offset:n_transfers+offset]):
            """ This function transfers a volume of liquid from a source plate
            to a destination plate using a single channel pipette
            :param offset: Dispense in the well on the target plate starting
            at the offset from the 1st well.
            :param pipette: The (single channel) pipette to use for
            transferring liquid
            :param vol: The volume for each liquid transfer
            :param source_plate: well plate to transfer from
            :param dest_plate: well plate to transfer to
            :param n_mixes: how many times to mix the solution after the
            transfer
            :param mix_vol: The mixing volume for the mixing actions
            :param n_transfers: How many samples to transfer to the target
            plate from the source plate
            :param offset: Offset defines how many wells to skip on the target
            plate before transferring e.g. if the offset is 96, the transfers
            begin in well 97 on the target plate
            """
            pick_up_tip(pipette)
            pipette.aspirate(vol, s_well)
            pipette.dispense(vol, d_well)
            mix(pipette, n_mixes, mix_vol, d_well)
            pipette.drop_tip()

    def resv_to_plate384_transfer(pipette, vol, source_well, dest_plate,
                                  n_samples, drop_tips=False):
        """
        Transfer from a reservoir to a plate. If the pipette is multi channel
        the transfers will be column to column.

        :param pipette: Pipette for the pipetting actions (aspirate/dispense)
        :param vol: The volume per tip to transfer
        :param source_well: The reservoir well to transfer from
        :param dest_plate: The plate to transfer to
        :param drop_tips: Whether to drop tips after each transfer or use the
        same tips throughout. Defaults to false
        """
        if not len(dest_plate.columns()[0]) == 16:
            raise Exception("The 384(?) well destination plate should have 16 "
                            "wells in in each row but it has {} wells instead".
                            format(len(dest_plate.columns())))
        # If the pip is multi-channel transfer from the resv well to the A
        # row well of the column and then the B row well, filling all 16
        # wells of the 384 well plate
        if is_multi_channel(pipette):
            n_columns = math.ceil(n_samples/16)
            target_columns = dest_plate.columns()[:n_columns]
            if not drop_tips:
                pick_up_tip(pipette)
            for col in target_columns:
                for i in range(2):
                    # col[0] = A row, col[1] = B row of the column
                    d_well = col[i]
                    if drop_tips:
                        pick_up_tip(pipette)
                    pipette.aspirate(vol, source_well)
                    pipette.dispense(vol, d_well)
                    if drop_tips:
                        pipette.drop_tip()
            if not drop_tips:
                pipette.drop_tip()
        # Single channel pip: well to well
        else:
            single_channel_resv_transfer(
                pipette, vol, source_well, dest_plate, n_samples, drop_tips)

    def resv_to_plate96_transfer(pipette, vol, source_well, dest_plate,
                                 n_samples, drop_tips=False):
        """
        Transfer from a reservoir to a 96 well plate. If the pipette is multi
        channel the transfers will be reservoir to column (well A of each col).
        This function can also use a single channel pipette to transfer to
        each well

        :param pipette: Pipette for the pipetting actions
        :param vol: The volume per tip to transfer
        :param source_well: The reservoir well to transfer from
        :param dest_plate: The plate to transfer to
        :param n_samples: How many (mastermix) samples to transfer
        :param drop_tips: Whether to drop tips after each transfer or use the
        same tips throughout. Defaults to False
        """
        # If the pip is multi-channel transfer to the a row well of each col
        if is_multi_channel(pipette):
            n_columns = math.ceil(n_samples/8)
            print(n_columns, n_samples)
            target_columns = dest_plate.columns()[:n_columns]
            if not drop_tips:
                pick_up_tip(pipette)
            for col in target_columns:
                if drop_tips:
                    pick_up_tip(pipette)
                pipette.aspirate(vol, source_well)
                pipette.dispense(vol, col[0])
                if drop_tips:
                    pipette.drop_tip()
            if not drop_tips:
                pipette.drop_tip()
        # Single channel pip: well to well
        else:
            single_channel_resv_transfer(
                pipette, vol, source_well, dest_plate, n_samples, drop_tips)

    def plate96_to_plate96_transfer(pipette, vol, source_plate, dest_plate,
                                    n_samples, n_mixes, mix_vol):
        """
        Transfer from a 96 well plate to a 96 well plate.
        This function can use either a multi-channel pipette or a single
        channel pipette.

        :param pipette: Pipette for the pipetting actions
        :param vol: The volume per tip to transfer
        :param source_plate: The well plate to transfer from
        :param dest_plate: The well plate to transfer to
        :param n_mixes: How many times to mix after dispensing
        :param mix_vol: Mixing volume
        """
        # Multi-channel pip: column by column transfer
        if is_multi_channel(pipette):
            n_columns = math.ceil(n_samples/8)
            source_columns = source_plate.columns()[:n_columns]
            target_columns = dest_plate.columns()[:n_columns]
            for s_col, d_col in zip(source_columns, target_columns):
                pick_up_tip(pipette)
                pipette.aspirate(vol, s_col[0])
                pipette.dispense(vol, d_col[0])
                mix(pipette, n_mixes, mix_vol, d_col[0])
                pipette.drop_tip()
        # SCP: well by well transfer
        else:
            single_channel_plate_transfer(pipette, vol, source_plate,
                                          dest_plate, n_mixes,
                                          mix_vol, n_samples)

    def plate96_to_plate384_transfer(pipette, vol, source_plate, dest_plate,
                                     n_samples, offset_samples, n_mixes,
                                     mix_vol):
        """
        Transfer from a well plate to a well plate.
        If the pipette is multi channel the transfers will be column to column.

        :param pipette: Pipette for the pipetting actions
        :param vol: The volume per tip to transfer
        :param source_plate: The 96 well plate to transfer from
        :param dest_plate: The 384 well plate to transfer to
        :param n_samples: How many samples to transfer from the 96 well plate
        :param offset_samples: Used to compute the offset column on the 384
        well plate, for example if 96 samples have been added then 6 columns
        on the 384 well plate have been filled so the next column should be
        no. 7
        :param n_mixes: How many times to mix after dispensing
        :param mix_vol: Mixing volume
        """

        # Error check
        s_len = len(source_plate.wells())
        d_len = len(dest_plate.wells())
        if s_len != 96 or d_len != 384:
            raise Exception(("Source plate should have 96 wells if the "
                             "destination plate has 384, but they "
                             "have {} and {} wells").format(s_len, d_len))
        # Multi-channel pip: column by column transfer
        if is_multi_channel(pipette):
            # Number of columns in the 96 well plate to pick samples from
            n_columns_96 = math.ceil(n_samples/8)
            offset_columns_384 = math.ceil(offset_samples/16)

            source_wells = [column[0] for column
                            in source_plate.columns()[:n_columns_96]]
            target_wells = []
            for i in range(n_columns_96):
                i_col_384 = i//2 + offset_columns_384
                if i % 2 == 0:
                    target_wells.append(dest_plate.columns()[i_col_384][0])
                else:
                    target_wells.append(dest_plate.columns()[i_col_384][1])

            for s_well, d_well in zip(source_wells, target_wells):
                pick_up_tip(pipette)
                pipette.aspirate(vol, s_well)
                pipette.dispense(vol, d_well)
                mix(pipette, n_mixes, mix_vol, d_well)
                pipette.drop_tip()
        # SCP: well by well transfer
        else:
            single_channel_plate_transfer(pipette, vol, source_plate,
                                          dest_plate, n_mixes,
                                          mix_vol, n_samples, offset=offset)

    def plate384_to_plate384_transfer(pipette, vol, source_plate, dest_plate,
                                      n_samples, n_mixes, mix_vol):
        """
        Transfer from a 384 well plate to a 384 well plate.
        If the pipette is multi channel the transfers will be column to column.

        :param pipette: Pipette for the pipetting actions
        :param vol: The volume per tip to transfer
        :param source_plate: The 96 well plate to transfer from
        :param dest_plate: The 384 well plate to transfer to
        :n_samples: How many samples to transfer, 384 for the whole plate
        :param n_mixes: How many times to mix after dispensing
        :param mix_vol: Mixing volume
        """
        # Error check
        s_len = len(source_plate.wells())
        d_len = len(dest_plate.wells())
        if not s_len == 384 and d_len == 384:
            raise Exception(("The source and destination plate should have "
                             "384 wells, but they have {} and {} wells").
                            format(s_len, d_len))
        # Multi-channel pip: column by column transfer
        if is_multi_channel(pipette):
            n_8chl_transfers = math.ceil(n_samples/8)
            source_wells = []
            target_wells = []
            for i in range(n_8chl_transfers):
                if i % 2 == 0:
                    source_wells.append(source_plate.columns()[i//2][0])
                    target_wells.append(dest_plate.columns()[i//2][0])
                else:
                    source_wells.append(source_plate.columns()[i//2][1])
                    target_wells.append(dest_plate.columns()[i//2][1])
            for s_well, d_well in zip(source_wells, target_wells):
                pick_up_tip(pipette)
                pipette.aspirate(vol, s_well)
                pipette.dispense(vol, d_well)
                mix(pipette, n_mixes, mix_vol, d_well)
                pipette.drop_tip()
        # SCP: well by well transfer
        else:
            single_channel_plate_transfer(pipette, vol, source_plate,
                                          dest_plate, n_mixes,
                                          mix_vol, n_samples)
    # reagents
    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''
    mastermix = mastermix_reservoir.wells()[0]

    '''

    Include header sections as follows for each "section" of your protocol.

    Section can be defined as a step in a bench protocol.

    e.g.

    ctx.comment('\n\nMOVING MASTERMIX TO SAMPLES IN COLUMNS 1-6\n')

    for .... in ...:
        ...
        ...

    ctx.comment('\n\nRUNNING THERMOCYCLER PROFILE\n')
    '''

    n_wells_source = len(DNA_well_plates[0].wells())
    n_wells_dest = len(destination_well_plate.wells())
    if n_wells_dest < n_samples:
        raise Exception("The destination plate does not have enough wells ({})"
                        "for all the samples ({}). Check your number of "
                        "samples parameter".
                        format(n_wells_dest, n_samples))

    # determine which pipette has the smaller volume range
    pip_s, pip_l = rank_pipettes(pipettes)
    # Make sure we have a pipette that can handle the volume of mastermix
    # Ideally the smaller one
    pipette = pipette_selector(pip_s, pip_l, mastermix_volume)
    ctx.comment("\n\nTransferring master mix to target plate\n")
    if n_wells_dest == 96:
        resv_to_plate96_transfer(pipette, mastermix_volume, mastermix,
                                 destination_well_plate, n_samples)
    elif n_wells_dest == 384:
        resv_to_plate384_transfer(pipette, mastermix_volume, mastermix,
                                  destination_well_plate, n_samples)
    else:
        raise Exception("Transferring to a {} well plate is unsupported".
                        format(n_wells_dest))

    # Transfer DNA to the destination plate
    pipette = pipette_selector(pip_s, pip_l, DNA_volume)
    ctx.comment("\n\nTransferring DNA to target plate\n")
    mixing_volume = DNA_volume + mastermix_volume - 1
    if n_wells_source == 96:
        if n_wells_dest == 96:
            # 96 well to 96 well plate transfer
            plate96_to_plate96_transfer(pipette, DNA_volume,
                                        DNA_well_plate_1,
                                        destination_well_plate, n_samples,
                                        n_mixes, mixing_volume,)
        # DNA transfer from 1 up to 4 96 well plates to 384 well plate
        elif n_wells_dest == 384:
            offset = 0
            i = 0
            while offset < n_samples:
                remaining_samples = n_samples - offset
                samples = remaining_samples if remaining_samples < 96 else 96
                plate96_to_plate384_transfer(
                    pipette, DNA_volume, DNA_well_plates[i],
                    destination_well_plate, samples, offset,
                    n_mixes, mixing_volume)
                offset += samples
                i += 1
        else:
            raise Exception(
                "The destination plate has an unexpected number of wells: {}".
                format(n_wells_dest))
    elif n_wells_source == 384 and n_wells_dest == 384:
        plate384_to_plate384_transfer(pipette, DNA_volume, DNA_well_plate_1,
                                      destination_well_plate, n_samples,
                                      n_mixes, mixing_volume)
    else:
        raise Exception(
            ("The protocol has not implemnted transfers from a {} to a {} "
             "well plate").format(n_wells_source, n_wells_dest))
    ctx.comment("\n\n~~~~ Protocol complete ~~~~\n")
