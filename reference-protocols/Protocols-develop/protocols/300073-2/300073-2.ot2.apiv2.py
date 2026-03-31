from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Saliva sample transfer from source to target well plate',
    'author': 'Eskil <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    [
      n_samples,
      aspirate_flow_rate,
      dispense_flow_rate,
      aspiration_height_mm,
      dispension_height_mm,
      temp_mod,
      temperature,
      post_aspiration_wait
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
                  "n_samples",
                  "aspirate_flow_rate",
                  "dispense_flow_rate",
                  "aspiration_height_mm",
                  "dispension_height_mm",
                  "temp_mod",
                  "temperature",
                  "post_aspiration_wait"
        )

    if not 1 <= n_samples <= 96:
        raise Exception(
            "Enter a number of samples between 1-96")

    if not 4 <= temperature <= 95:
        raise Exception(
            "Temperature module must be set to a temperature between " +
            "4 and 95 degrees Celsius")

    right_pipette_lname = 'p20_multi_gen2'
    filtered_20_lname = "opentrons_96_filtertiprack_20ul"

    well_plate_on_alum_lname = \
        "stellarscientific_96_aluminumblock_100ul"
    well_plate_lname = "stellarscientific_96_wellplate_100ul"

    sample_volume = 5  # 5 uL sample volume to transfer betw. plates
    # load modules
    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''
    temp_mod = None
    if temp_mod:
        temp_mod = ctx.load_module("temperature module gen2", '3')

    # load labware

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    source_plate = None
    source_plate_label = "source plate"
    if temp_mod:
        source_plate = temp_mod.load_labware(well_plate_on_alum_lname,
                                             label=source_plate_label)
    else:
        source_plate = ctx.load_labware(well_plate_lname,
                                        '3', label=source_plate_label)

    dest_plate = ctx.load_labware(well_plate_lname,
                                  '6', label="destination plate")
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
    tiprack = ctx.load_labware(filtered_20_lname, '9')

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
    pipette = ctx.load_instrument(
                        right_pipette_lname,
                        "right",
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

    # Transfer the first set of tube samples
    ctx.comment("\n\nTransferring samples from source plate " +
                "to destination plate\n")
    n_columns = math.ceil(n_samples/8)
    for s_col, d_col in zip(source_plate.columns()[0:n_columns],
                            dest_plate.columns()[0:n_columns]):
        pick_up(pipette)
        pipette.aspirate(sample_volume, s_col[0].bottom(aspiration_height_mm))
        ctx.delay(post_aspiration_wait)
        pipette.dispense(sample_volume,
                         d_col[0].bottom(dispension_height_mm))
        pipette.drop_tip()

    ctx.comment("\n\n~~~~ Protocol finished ~~~~")
