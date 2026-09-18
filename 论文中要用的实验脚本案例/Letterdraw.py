from opentrons import protocol_api

requirements = {'robotType': 'Flex', 'apiLevel': '2.19'}

def run(protocol_context):
    """
    Protocol to draw LYZ letters on an ELISA plate using black and red ink.
    """
    # Load Trash Bin
    trash_bin = protocol_context.load_trash_bin('A3')
    
    # Load Labware
    tiprack_50ul = protocol_context.load_labware('opentrons_flex_96_tiprack_200ul', 'C2', '200uL Tips')
    pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2', 'ELISA Plate for Drawing')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'B3', 'Ink Reservoir')
    
    # Get ink wells
    black_ink_well = reservoir.wells_by_name()['A1']
    red_ink_well = reservoir.wells_by_name()['A2']
    
    # Define liquids
    liquid_black_ink = protocol_context.define_liquid(
        name='black_ink',
        description='Black drawing ink',
        display_color='#000000'
    )
    
    liquid_red_ink = protocol_context.define_liquid(
        name='red_ink', 
        description='Red drawing ink',
        display_color='#FF0000'
    )
    
    # Load ink into reservoir wells
    black_ink_well.load_liquid(liquid=liquid_black_ink, volume=10000)
    red_ink_well.load_liquid(liquid=liquid_red_ink, volume=10000)
    
    # Load Pipettes
    p1000_1ch = protocol_context.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack_50ul])
    
    # Drawing parameters
    draw_volume = 150
    
    # LYZ letters coordinates - black ink for main letters
    lyz_black_coords = [
        # Letter L
        ('B', 1), ('C', 1), ('D', 1), ('E', 1), ('F', 1), ('G', 1),  # vertical line
        ('G', 2), ('G', 3),  # horizontal bottom line
        
        # Letter Y
        ('B', 5), ('C', 6), ('D', 7),  # left diagonal
        ('B', 9), ('C', 8), ('D', 7),  # right diagonal
        ('E', 7), ('F', 7), ('G', 7),  # vertical line down
        
        # Letter Z
        ('B', 11), ('B', 12),  # top horizontal
        ('C', 11), ('D', 10), ('E', 9),  # diagonal
        ('F', 11), ('G', 11), ('G', 12),  # bottom horizontal
    ]
    
    # LYZ letters coordinates - red ink for decorative dots
    lyz_red_coords = [
        # Decorative dots around letters
        ('A', 2), ('A', 6), ('A', 10),  # dots above letters
        ('H', 2), ('H', 7), ('H', 11),  # dots below letters
    ]
    
    # Convert coordinates to wells
    black_wells = [pcr_plate.wells_by_name()[f'{row}{col}'] for row, col in lyz_black_coords]
    red_wells = [pcr_plate.wells_by_name()[f'{row}{col}'] for row, col in lyz_red_coords]
    
    # Perform drawing
    protocol_context.comment("Starting to draw LYZ letters with black ink")
    
    # Draw black parts first
    p1000_1ch.transfer(
        draw_volume,
        black_ink_well,
        black_wells,
        new_tip='once'
    )
    
    protocol_context.comment("Adding red decorative dots")
    
    # Draw red parts
    p1000_1ch.transfer(
        draw_volume,
        red_ink_well,
        red_wells,
        new_tip='once'
    )
    
    protocol_context.comment("Finished drawing LYZ letters! 📝")
    protocol_context.comment("Protocol complete")