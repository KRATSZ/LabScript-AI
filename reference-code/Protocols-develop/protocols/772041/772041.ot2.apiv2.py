from opentrons import protocol_api
import math

metadata = {
    'protocolName': 'Distribution of PCR mastermix to MicroAmp 384 optical well plate or other plate',  # noqa: E501
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):
    [n_wells,
     mastermix_volume,
     is_reusing_tips,
     dest_plate_lname] = get_values(  # noqa: F821
     "n_wells",
     "mastermix_volume",
     "is_reusing_tips",
     "dest_plate_lname")
    # define all custom variables above here with descriptions:
    source_resv_lname = 'nest_12_reservoir_15ml'
    tips_loadname = 'opentrons_96_filtertiprack_20ul'

    if n_wells < 0 or n_wells > 384:
        raise Exception("Number of wells parameter is invalid: {}".
                        format(n_wells))
    if mastermix_volume < 1:
        raise Exception("Mastermix volume is too small to pipette")
    if dest_plate_lname == "x":
        raise Exception("Mic tube plate is not yet implemented")

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
    source_reservoir = ctx.load_labware(source_resv_lname, '1')
    destination_plate = ctx.load_labware(dest_plate_lname, '4')
    plate_max_vol = destination_plate.wells()[0].max_volume
    if plate_max_vol < mastermix_volume:
        raise Exception(("Mastermix volume {} uL is too large for "
                        + "the destination plate wells with max volume of "
                        + "{} uL").format(mastermix_volume, plate_max_vol))

    if n_wells < 0 or n_wells > len(destination_plate.wells()):
        raise Exception(("Number of wells parameter is invalid: {}, the "
                         + "maximal number of wells is {} for {}").
                        format(n_wells, len(destination_plate.wells()),
                               destination_plate))

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
    tipracks = [ctx.load_labware(tips_loadname, slot)
                for slot in ['2', '3', '5', '6']]

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
    m20 = ctx.load_instrument(
                        'p20_multi_gen2',
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
    mastermix = source_reservoir.wells()[0]
    waste = source_reservoir.wells()[1]
    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''
    n_columns = math.ceil(n_wells/len(destination_plate.columns()[0]))
    dispenses_per_column = len(destination_plate.columns()[0])//8
    dest_cols = destination_plate.columns()[:n_columns]

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

    ctx.comment('\n\nDistributing mastermix to the target plate\n')
    if is_reusing_tips:
        m20.pick_up_tip()
    for col in dest_cols:
        for well in col[:dispenses_per_column]:
            if not is_reusing_tips:
                m20.pick_up_tip()
            else:
                m20.blow_out(waste)
            m20.aspirate(mastermix_volume, mastermix)
            m20.dispense(mastermix_volume, well)
            m20.touch_tip()
            if not is_reusing_tips:
                m20.drop_tip()

    if m20.has_tip:
        m20.drop_tip()
    ctx.comment('\n\n~~~~ Protocol Finished ~~~~\n')
