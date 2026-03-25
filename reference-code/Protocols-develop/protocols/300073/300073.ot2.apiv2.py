from opentrons import protocol_api

metadata = {
    'protocolName': 'Saliva sample transfer from tuberacks to 96 well plate',
    'author': 'Eskil <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    [has_first_tube_set,
     n_samples_set1,
     has_second_tube_set,
     n_samples_set2,
     sample_aspiration_vol_ul,
     aspirate_flow_rate,
     dispense_flow_rate,
     aspiration_height_mm,
     dispension_height_mm,
     temp_mod_lname,
     temperature,
     post_aspiration_wait] = get_values(  # noqa: F821
     "has_first_tube_set",
     "n_samples_set1",
     "has_second_tube_set",
     "n_samples_set2",
     "sample_aspiration_vol_ul",
     "aspirate_flow_rate",
     "dispense_flow_rate",
     "aspiration_height_mm",
     "dispension_height_mm",
     "temp_mod_lname",
     "temperature",
     "post_aspiration_wait")

    if (not 1 <= n_samples_set1 <= 45) and has_first_tube_set:
        raise Exception(
            "Enter a number of samples for tube set 1 between 1-45")

    if (not 1 <= n_samples_set2 <= 48) and has_second_tube_set:
        raise Exception(
            "Enter a number of samples for tube set 2 between 1-48")

    if not 4 <= temperature <= 95:
        raise Exception(
            "Temperature module must be set to a temperature between "
            + "4 and 95 degrees Celsius")

    p20_lname = 'p20_single_gen2'
    p300_lname = 'p300_single_gen2'

    filtered_20_lname = "opentrons_96_filtertiprack_20ul"
    filtered_200_lname = "opentrons_96_filtertiprack_200ul"
    tiprack_lname = (filtered_20_lname if sample_aspiration_vol_ul <= 20
                     else filtered_200_lname)

    tuberack_lname = 'opentrons_6_tuberack_stellarsci_25ml_conical'
    well_plate_on_alum_lname = \
        "stellarscientific_96_aluminumblock_100ul"
    well_plate_lname = "stellarscientific_96_wellplate_100ul"
    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''
    temp_mod = None
    if temp_mod_lname:
        temp_mod = ctx.load_module("temperature module gen2", '3')

    # load labware

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    tuberack_set_1 = [ctx.load_labware(tuberack_lname, slot)
                      for slot in ['10', '11',
                                   '7', '8']]
    tuberack_set_2 = [ctx.load_labware(tuberack_lname, slot)
                      for slot in ['4', '5',
                                   '1', '2']]

    plate = None
    if temp_mod:
        plate = temp_mod.load_labware(well_plate_on_alum_lname,
                                      label="target plate")
    else:
        plate = ctx.load_labware(well_plate_lname, '3', label="target plate")

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
    tiprack = ctx.load_labware(tiprack_lname, '9')

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
    pipette_condition = sample_aspiration_vol_ul <= 20
    pipette = ctx.load_instrument(
                    p20_lname if pipette_condition else p300_lname,
                    "right" if pipette_condition else "left",
                    tip_racks=[tiprack]
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
    def transfer_tube_samples(volume, source_tubes, dest_wells):
        nonlocal pipette, aspiration_height_mm, dispension_height_mm
        nonlocal post_aspiration_wait

        for s_well, d_well in zip(source_tubes, dest_wells):
            pick_up(pipette)
            pipette.aspirate(sample_aspiration_vol_ul,
                             s_well.bottom(aspiration_height_mm))
            ctx.delay(post_aspiration_wait)
            pipette.dispense(sample_aspiration_vol_ul,
                             d_well.bottom(dispension_height_mm))
            pipette.drop_tip()

    # reagents

    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''

    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''
    def add_quadrant_wells(rows, col_start_index, col_end_index):
        """
        Adds the wells in the given quadrant(rectangle) defined
        by the columns and the start and end indices of the rows
        col 1/row 1 ... col n/row 1
        .  .            .
        .       .       .
        .            .  .
        col 1/row n ... col n/row n
        :param list: The list to append the wells in the quadrant to
        :param colums: The columns that define the "x" interval of the quadrant
        :param row_start_index: defines the start "y" interval
        :param row_end_index: defines the end "y" interval
        """
        list = []
        for row in rows:
            for well in row[col_start_index:col_end_index]:
                list.append(well)
        return list

    # Map the target quadrants of the destination plate
    targ_well_rows = plate.rows()
    # Top left quadrant
    # The rectangle of A1-D1 to A6-D6
    target_quadrant_1 = add_quadrant_wells(targ_well_rows[0:4], 0, 6)

    # Top right quadrant: A7-D7 to A12-D12 rectangle
    target_quadrant_2 = add_quadrant_wells(targ_well_rows[0:4], 6, 12)

    # Bottom left quadrant: E1-H1 to E6-H6 rectangle
    target_quadrant_3 = add_quadrant_wells(targ_well_rows[4:8], 0, 6)

    # Bottom right quadrant: E7-H7 to E12-H12 rectangle
    target_quadrant_4 = add_quadrant_wells(targ_well_rows[4:8], 6, 12)

    def create_tube_list(tuberack_quadrant):
        """
        Take a quadrant of 4 tuberacks and return a list that goes in
        row order from the top left rack, top left well to bottom right
        rack, bottom right well.

        :param tuberack_quadrant: 4 tube-racks laid out in a quadrant on
        the deck, rack 1: top left, rack 2: top right, rack 3: bottom left,
        rack 4: bottom right.
        """
        well_list = []
        for top_left_row, top_right_row in zip(tuberack_quadrant[0].rows(),
                                               tuberack_quadrant[1].rows()):
            for well in top_left_row:
                well_list.append(well)
            for well in top_right_row:
                well_list.append(well)
        for bot_left_row, bot_right_row in zip(tuberack_quadrant[2].rows(),
                                               tuberack_quadrant[3].rows()):
            for well in bot_left_row:
                well_list.append(well)
            for well in bot_right_row:
                well_list.append(well)
        return well_list

    tuberack_quad_1_map = create_tube_list(tuberack_set_1)
    tuberack_quad_2_map = create_tube_list(tuberack_set_2)
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

    # Set the pipette aspirate/dispense flow rate
    pipette.flow_rate.aspirate = aspirate_flow_rate
    pipette.flow_rate.dispense = dispense_flow_rate

    # Set temperature module temperature
    if temp_mod:
        ctx.comment("\n\nSetting temperature module to {} degrees C\n".
                    format(temperature))
        temp_mod.set_temperature(temperature)

    if has_first_tube_set:
        # Transfer the first set of tube samples to quadrant 1 of the
        # 96 well plate, skipping the 3 first wells/tubes for controls
        ctx.comment("\n\nTransferring samples from Sample set 1:Tuberack "
                    "quad 1 to Destination quad 1\n")
        n_wells = len(target_quadrant_1) - 3
        n_quad_transfers = n_wells if n_wells < n_samples_set1 \
            else n_samples_set1
        transfer_tube_samples(sample_aspiration_vol_ul,
                              tuberack_quad_1_map[3:n_quad_transfers+3],
                              target_quadrant_1[3:n_quad_transfers+3])

        ctx.comment("\n\nTransferring samples from Sample set 1:Tuberack "
                    "quad 2 to Destination quad 2\n")
        n_wells = len(target_quadrant_2)

        n_quad_transfers = n_samples_set1 - n_quad_transfers
        transfer_tube_samples(sample_aspiration_vol_ul,
                              tuberack_quad_2_map[:n_quad_transfers],
                              target_quadrant_2[:n_quad_transfers])

    # If the first set of tuberacks has to be removed and the 2nd set inserted
    # then pause here
    if has_second_tube_set and has_first_tube_set:
        ctx.pause(
            "\n\nRemove the 1st set of tuberacks and insert the 2nd set\n")
        ctx.comment("\n\nTransferring samples from Sample set 2:Tuberack "
                    "quad 1 to Destination quad 3\n")

    # Transfer the second set of tube samples
    if has_second_tube_set:
        n_wells = len(target_quadrant_3)
        n_quad_transfers = n_wells if n_wells < n_samples_set2\
            else n_samples_set2
        transfer_tube_samples(sample_aspiration_vol_ul,
                              tuberack_quad_1_map[:n_quad_transfers],
                              target_quadrant_3[:n_quad_transfers])

        ctx.comment("\n\nTransferring samples from Sample set 2:Tuberack "
                    "quad 2 to Destination quad 4\n")
        n_quad_transfers = n_samples_set2 - n_quad_transfers
        transfer_tube_samples(sample_aspiration_vol_ul,
                              tuberack_quad_2_map[:n_quad_transfers],
                              target_quadrant_4[:n_quad_transfers])
    ctx.comment("\n\n~~~~ Protocol finished ~~~~")
