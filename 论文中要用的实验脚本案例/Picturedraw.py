from opentrons import protocol_api
requirements = {'robotType': 'Flex', 'apiLevel': '2.19'}
def run(protocol_context):
    """
    Protocol to draw a lion on an ELISA plate using ink from a reservoir.
    Loads various modules as specified in the SOP.
    """
    trash_bin = protocol_context.load_trash_bin('A3')
    tiprack_200ul = protocol_context.load_labware('opentrons_flex_96_tiprack_200ul', 'C2', '200uL Tips')
    pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2', 'ELISA Plate for Drawing')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'B3', 'Ink Reservoir')
    ink_well = reservoir.wells_by_name()['A1']
    liquid_ink = protocol_context.define_liquid(
        name='ink',
        description='Drawing ink for lion',
        display_color='#DAA520'
    )
    ink_well.load_liquid(liquid=liquid_ink, volume=10000)
    p1000_1ch = protocol_context.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack_200ul])
    draw_volume = 150
    ears_coords = [('A', 3), ('A', 9), ('B', 2), ('B', 4), ('B', 8), ('B', 10)]
    head_coords = [
        ('B', 5), ('B', 6), ('B', 7), ('C', 1), ('C', 11), ('D', 1), ('D', 11), ('E', 1),
        ('E', 11), ('F', 2), ('F', 3), ('F', 9), ('F', 10), ('G', 4), ('G', 5), ('G', 7), ('G', 8)
    ]
    eyes_coords = [('C', 4), ('C', 8)]
    nose_coords = [('D', 6)]
    mouth_coords = [('E', 5), ('E', 6), ('E', 7), ('F', 6)]
    mane_coords = [
        ('A', 1), ('A', 11), ('B', 1), ('B', 11), ('C', 2), ('C', 3), ('C', 9), ('C', 10),
        ('D', 2), ('D', 10), ('E', 2), ('E', 10), ('F', 1), ('F', 11), ('G', 1), ('G', 2),
        ('G', 10), ('G', 11), ('H', 3), ('H', 4), ('H', 8), ('H', 9)
    ]
    
    all_coords = ears_coords + head_coords + eyes_coords + nose_coords + mouth_coords + mane_coords
    target_wells = [pcr_plate.wells_by_name()[f'{row}{col}'] for row, col in all_coords]
    protocol_context.comment("Starting to draw a lion")
    p1000_1ch.transfer(
        draw_volume,
        ink_well,
        target_wells,
        new_tip='once'
    )
    protocol_context.comment("Finished drawing the lion")
    protocol_context.comment("Protocol complete. Lion drawing finished.")