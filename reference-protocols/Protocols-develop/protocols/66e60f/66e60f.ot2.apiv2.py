from opentrons import protocol_api
import re

metadata = {
    'protocolName': '66e60f: Normalization protocol from CSV',
    'author': 'Eskil Andersen <eskil.andersen@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    [input_csv,
     source_type,
     dest_type,
     tuberack_type,
     p300_type,
     air_gap_vol] = get_values(  # noqa: F821
     "input_csv",
     "source_type",
     "dest_type",
     "tuberack_type",
     "p300_type",
     "air_gap_vol")

    # define all custom variables above here with descriptions:
    left_pipette_loadname = 'p20_single_gen2'
    right_pipette_loadname = p300_type

    final_plate_loader_A = (dest_type, '6',
                            'Final plate A')
    final_plate_loader_B = (dest_type, '4',
                            'Final plate B')
    DNA_sample_plate_loader_A = (source_type, '9',
                                 'DNA plate A')
    DNA_sample_plate_loader_B = (source_type, '7',
                                 'DNA plate B')
    tuberack_loader = (tuberack_type, '5',
                       'tuberack')
    tiprack_300uL_loader = ('opentrons_96_filtertiprack_200ul', '10')
    tiprack_20uL_A_loader = ('opentrons_96_filtertiprack_20ul', '3')
    tiprack_20uL_B_loader = ('opentrons_96_filtertiprack_20ul', '1')

    reservoir_loader = ('nest_12_reservoir_15ml', '11', 'water reservoir')

    # Initial 40 uL water for each well of the target
    initial_water_volume = 40

    # Read CSV and format the inputs
    # csv format: Plate | Well | Sample ID | Concentration | Transfer volume
    #              [0]     [1]       [2]          [3]              [4]
    data = [
        [val.strip().upper() for val in line.split(',')
            if val != '']
        for line in input_csv.splitlines()[1:]
        if line and line.split(',')[0]]

    # Convert any well designation in column 1 from [A-H]0[1-9] to [A-H][1-9]
    # e.g. A01 -> A1 etc.
    pattern = re.compile('[A-H]0[1-9]')
    for row in data:
        if pattern.match(row[0]):
            row[0] = row[0].replace('0', '')

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
    reservoir = ctx.load_labware(reservoir_loader[0], reservoir_loader[1],
                                 reservoir_loader[2])
    dna_sample_plate_A = ctx.load_labware(DNA_sample_plate_loader_A[0],
                                          DNA_sample_plate_loader_A[1],
                                          DNA_sample_plate_loader_A[2])
    dna_sample_plate_B = ctx.load_labware(DNA_sample_plate_loader_B[0],
                                          DNA_sample_plate_loader_B[1],
                                          DNA_sample_plate_loader_B[2])

    final_plate_A = ctx.load_labware(final_plate_loader_A[0],
                                     final_plate_loader_A[1],
                                     final_plate_loader_A[2])
    final_plate_B = ctx.load_labware(final_plate_loader_B[0],
                                     final_plate_loader_B[1],
                                     final_plate_loader_B[2])
    tuberack = ctx.load_labware(tuberack_loader[0],
                                tuberack_loader[1],
                                tuberack_loader[2])

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
    # tipracks_20_filter = [ctx.load_labware(tiprack_20uL_loader[0], slot)
    #                      for slot in tiprack_20uL_loader[1]]
    tiprack_20_A = [ctx.load_labware(
        tiprack_20uL_A_loader[0], tiprack_20uL_A_loader[1])]
    tiprack_20_B = [ctx.load_labware(
        tiprack_20uL_B_loader[0], tiprack_20uL_B_loader[1])]
    tiprack_300 = [ctx.load_labware(tiprack_300uL_loader[0],
                                    tiprack_300uL_loader[1])]

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
    # Load m20 and p20, m20 switches out for p300 in step 2
    p20 = ctx.load_instrument(
                        left_pipette_loadname,
                        "left",
                        tip_racks=None
                        )
    p300 = ctx.load_instrument(
                        right_pipette_loadname,
                        "right",
                        tip_racks=tiprack_300
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
                     start=1, end=8,
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
    water_well = reservoir.wells_by_name()['A1']
    liquid_waste = reservoir.wells_by_name()['A2'].top(-2)

    water_waste_tube_tracker = VolTracker(
        tuberack, 1500, 1, 2, 'waste',
        'single', "\n\nWater waste tube full, please replace\n")
    dna_waste_tube_tracker = VolTracker(
        tuberack, 1500, 3, 4, 'waste',
        'single',
        "\n\nDNA waste tubes may be full, please replace even if not full\n")
    dna_pool_tube = tuberack.wells_by_name()['A2']

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
    # Find all wells and columns in the csv so that water dispension can
    # be limited to  those columns or wells

    # Lists of well names
    well_list_A = []
    well_list_B = []
    # Lists of well locations on the final plates for initial water transfer
    wells_A = []
    wells_B = []
    i = 2
    for plate, well, _, _, _ in data:
        if plate == 'A':
            well_list_A.append(well)
        elif plate == 'B':
            well_list_B.append(well)
        else:
            raise Exception(("The plate name on line {} in the csv "
                             + "seems malformed: {}").
                            format(i, plate))
        i += 1

    # If the set and the list are not the same length there must be duplicates
    if len(well_list_A) != len(list(set(well_list_A))):
        raise Exception('Duplicate wells found for plate A, check your csv')
    if len(well_list_B) != len(list(set(well_list_B))):
        raise Exception('Duplicate wells found for plate B, check your csv')

    if 'single' in p300_type:
        wells_A = [final_plate_A.wells_by_name()[well] for well in well_list_A]
        wells_B = [final_plate_B.wells_by_name()[well] for well in well_list_B]

    col_set_A = []
    col_set_B = []
    if 'multi' in p300_type:
        col_list_A = [well[1:] for well in well_list_A]
        col_list_B = [well[1:] for well in well_list_B]
        # Create a a list of the set of all unique column values
        # and sort from lowest to highest column
        col_set_A = list(set(col_list_A))
        col_set_B = list(set(col_list_B))
        # Chaining sort() doesn't work
        col_set_A.sort()
        col_set_B.sort()
        wells_A = [final_plate_A.columns()[int(col)-1][0] for col in col_set_A]
        wells_B = [final_plate_B.columns()[int(col)-1][0] for col in col_set_B]

    p300.pick_up_tip()
    for wells, plate_name in zip([wells_A, wells_B], ['A', 'B']):
        if len(wells) > 0:
            ctx.comment("\nTransferring water to final plate {}\n".
                        format(plate_name))
            for well in wells:
                if p300.current_volume < initial_water_volume:
                    p300.aspirate(200-p300.current_volume, water_well)
                p300.dispense(initial_water_volume, well)
            p300.blow_out(liquid_waste)
    p300.drop_tip()

    # Make sure the lines in data are ordered by plate so that we can
    # distribute as efficiently as possible
    sorted_data = sorted(data, key=lambda line: line[0])

    # Transfering DNA samples to target
    ctx.comment("\nTransferring DNA sample to target plate\n")
    for plate, well, sampleID, conc, vol in sorted_data:
        vol = float(vol)
        dna_source = dna_sample_plate_A[well] \
            if plate == 'A' else dna_sample_plate_B[well]
        dna_dest = final_plate_A[well] if plate == 'A' else final_plate_B[well]

        ctx.comment(("Normalizing sample \"{}\" on plate {} with "
                    + "concentration {}").format(sampleID, plate, conc))
        pip = p20

        if plate == 'A':
            pip.pick_up_tip(tiprack_20_A[0].next_tip())
        elif plate == 'B':
            pip.pick_up_tip(tiprack_20_B[0].next_tip())
        else:
            raise Exception("Invalid plate specified: {}".format(plate))
        # Remove water from the final plates and dispense into waste tubes
        remaining_water_vol = vol
        while remaining_water_vol > 0:
            aspiration_vol = remaining_water_vol \
                if remaining_water_vol < pip.max_volume else pip.max_volume
            pip.aspirate(aspiration_vol, dna_dest)
            pip.dispense(aspiration_vol, water_waste_tube_tracker.track(vol))
            remaining_water_vol -= aspiration_vol
        pip.blow_out()
        pip.touch_tip()
        # Aspirate DNA sample using the same tip
        remaining_dna_vol = vol
        max_asp_vol = pip.max_volume - air_gap_vol
        while remaining_dna_vol > 0:
            aspiration_vol = remaining_dna_vol \
                if remaining_dna_vol < max_asp_vol else max_asp_vol
            pip.aspirate(aspiration_vol, dna_source)
            pip.air_gap(air_gap_vol)
            # Dispense into final well
            pip.dispense(aspiration_vol + air_gap_vol, dna_dest)
            remaining_dna_vol -= aspiration_vol
        # Touch tip in the destination well
        pip.touch_tip()
        # Blow out DNA waste
        pip.blow_out(dna_waste_tube_tracker.track(5))
        pip.return_tip()

    pip = p20
    # Reset the tipracks so we can reuse the tips
    for rack in [tiprack_20_A[0], tiprack_20_B[0]]:
        rack.reset()

    ctx.pause(
        "[Off deck] Seal the plates, vortex the plates, brief spin, "
        + "remove seal, replace the plates back to the deck\n")
    ctx.comment("Transferring 5 uL diluted DNA samples to DNA pool tube\n\n")
    for plate, well, _, _, _ in sorted_data:
        well = final_plate_A.wells_by_name()[well] if plate == 'A' \
            else final_plate_B.wells_by_name()[well]
        if plate == 'A':
            pip.pick_up_tip(tiprack_20_A[0].next_tip())
        elif plate == 'B':
            pip.pick_up_tip(tiprack_20_B[0].next_tip())
        else:
            raise Exception("Invalid plate specified: {}".format(plate))
        pip.aspirate(5, well)
        pip.air_gap(air_gap_vol)
        pip.dispense(vol+air_gap_vol, dna_pool_tube)
        pip.blow_out()
        pip.touch_tip()
        pip.drop_tip()
    ctx.comment("\n\n~~~~ Protocol Finished! ~~~~\n")
