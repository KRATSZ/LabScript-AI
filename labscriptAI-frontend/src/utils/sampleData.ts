// Sample Python code for Opentrons protocol
export const pythonCodeSample = `from opentrons import protocol_api

# metadata
metadata = {
    'protocolName': 'Sample Protocol',
    'author': 'LabScript AI',
    'description': 'A sample protocol for demonstration purposes',
    'apiLevel': '2.20'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Load pipettes
    pipette = protocol.load_instrument(
        'p300_single_gen2', 
        'right', 
        tip_racks=[tiprack]
    )
    
    # Define wells
    sample_wells = plate.wells()[:12]  # First row of wells
    reagent_well = reservoir.wells()[0]  # First well of reservoir
    
    # Protocol steps
    protocol.comment('Starting sample protocol')
    
    for i, well in enumerate(sample_wells):
        # Pick up a tip
        pipette.pick_up_tip()
        
        # Aspirate from reagent well
        pipette.aspirate(100, reagent_well)
        
        # Dispense into sample well
        pipette.dispense(100, well)
        
        # Mix 3 times with 90µL volume
        pipette.mix(3, 90, well)
        
        # Drop the tip
        pipette.drop_tip()
        
        # Add a comment to track progress
        protocol.comment(f'Completed transfer to well {i+1}')
    
    protocol.comment('Protocol complete')
`;