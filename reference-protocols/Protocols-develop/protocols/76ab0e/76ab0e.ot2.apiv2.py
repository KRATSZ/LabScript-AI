from opentrons import protocol_api
import re

metadata = {
    'protocolName': '76ab0e: Temperature controlled normalization from .csv',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):
    [input_csv,
     p20_mount,
     p300_mount,
     aspiration_height_plate,
     dispensing_height_plate,
     aspiration_height_resv,
     flow_rate_multiplier] = get_values(  # noqa: F821
     "input_csv",
     "p20_mount",
     "p300_mount",
     "aspiration_height_plate",
     "dispensing_height_plate",
     "aspiration_height_resv",
     "flow_rate_multiplier")

    if 0.1 > aspiration_height_plate:
        raise Exception("Enter a higher source plate aspiration height")

    if 0.1 > dispensing_height_plate:
        raise Exception("Enter a higher destination plate dispensing height")

    if 0.1 > aspiration_height_resv:
        raise Exception("Enter a higher reservoir aspiration height")

    if p20_mount == p300_mount:
        raise Exception("Both pipettes cannot be mounted in the same mount")

    # define all custom variables above here with descriptions:
    sample_plate_lname = 'opentrons_96_aluminumblock_biorad_wellplate_200ul'
    dest_plate_lname = 'opentrons_96_aluminumblock_biorad_wellplate_200ul'
    small_tips_loadname = 'opentrons_96_filtertiprack_20ul'
    large_tips_loadname = 'opentrons_96_filtertiprack_200ul'
    res_loadname = 'nest_12_reservoir_15ml'

    # For validating that wells have the format of <A-H><0-12>
    well_name_validation_regex = re.compile(r'[A-H][0-9][0-2]?')
    # Check that the volumes look like numbers e.g. 12, or 5.25
    volume_validation_regex = re.compile(r'[0-9]+(\.[0-9]+)?')

    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''

    # load labware
    temp_mod_samples = ctx.load_module('temperature module gen2', '1')
    temp_mod_destination = ctx.load_module('temperature module gen2', '4')

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    sample_plate = temp_mod_samples.load_labware(sample_plate_lname)
    destination_plate = temp_mod_destination.load_labware(dest_plate_lname)
    reservoir_12 = ctx.load_labware(res_loadname, '2',
                                    label="diluent reservoir")

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
    small_tipracks = [ctx.load_labware(small_tips_loadname, slot)
                      for slot in ['7', '10']]

    large_tipracks = [ctx.load_labware(large_tips_loadname, slot)
                      for slot in ['5', '8']]

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
    p20 = ctx.load_instrument(
                        'p20_single_gen2',
                        p20_mount,
                        tip_racks=small_tipracks
                        )

    p300 = ctx.load_instrument(
                        'p300_single_gen2',
                        p300_mount,
                        tip_racks=large_tipracks
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
    diluent = VolTracker(reservoir_12, 14*10**3,  start=1, end=4,
                         mode='reagent', pip_type='single',
                         msg='Refill diluent wells')

    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''
    sample_wells = sample_plate.wells_by_name()
    dest_wells = destination_plate.wells_by_name()

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
    # parse
    data = [
        [val.strip().upper() for val in line.split(',')]
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]

    # Validate csv input
    i = 1
    for line in data:
        i += 1
        if not len(line) == 4:
            raise Exception("Line #{} \"{}\" has the wrong number of entries".
                            format(i, line))
        # check well formatting
        if well_name_validation_regex.fullmatch(line[0]) is None:
            raise Exception(("Line #{}: The source plate well name \"{}\" "
                             "has the wrong format").
                            format(i, line[0]))

        if well_name_validation_regex.fullmatch(line[1]) is None:
            raise Exception(("Line #{}: The dest. plate well name \"{}\" "
                             "has the wrong format").
                            format(i, line[1]))

        if volume_validation_regex.fullmatch(line[2]) is None:
            raise Exception(("Line #{}: The sample volume \"{}\" "
                             + "has the wrong format").
                            format(i, line[2]))

        if volume_validation_regex.fullmatch(line[3]) is None:
            raise Exception(("Line #{}: The diluent volume \"{}\" "
                             + "has the wrong format").
                            format(i, line[3]))

    # perform normalization - Transfer all the diluent first before
    # transferring any sample: use the same pipette tip
    # Steps 1-4
    # d - dest well,  vol_d - diluent volume
    ctx.comment("\n\nTransferring diluent to the target plate\n")
    for _, d, _, vol_d in data:
        vol_d = float(vol_d)
        d_well = dest_wells[d]

        pip = p300 if vol_d > 20 else p20
        if not pip.has_tip:
            pip.pick_up_tip()
        pip.transfer(vol_d,
                     diluent.track(vol_d).bottom(aspiration_height_resv),
                     d_well.bottom(dispensing_height_plate), new_tip='never')
        pip.blow_out(d_well.top(-2))
        # Debugging info
        # print("diluent reservoir position {}".
        #       format(diluent.track(0).bottom(aspiration_height_resv)))

    # Step 5: drop tips
    ctx.comment("\n\nDiluent transfer complete: Droppping tips")
    for pip in [p20, p300]:
        if pip.has_tip:
            pip.drop_tip()

    # Step 7-10: Transfer samples from the sample plate to the dest. plate
    ctx.comment("\n\nTransferring samples to the target plate\n")
    for s, d, vol_s, _ in data:
        vol_s = float(vol_s)
        s_well = sample_wells[s].bottom(aspiration_height_plate)
        d_well = dest_wells[d].bottom(dispensing_height_plate)
        blow_out_loc = dest_wells[d].top(-2)
        # Debugging info
        # print("Aspiration height s_well: {}".format(s_well))
        # print("Dispensing height d_well: {}".format(d_well))

        # Transfer sample
        pip = p300 if vol_s > 20 else p20
        pip.pick_up_tip()
        pip.aspirate(vol_s, s_well, flow_rate_multiplier)
        pip.dispense(vol_s, d_well, flow_rate_multiplier)
        pip.blow_out(blow_out_loc)
        pip.drop_tip()
