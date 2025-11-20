export interface CodeEditingExample {
  id: string;
  label: string;
  description: string;
  initialCode: string;
  suggestedInstruction: string;
  category: 'migration' | 'basic' | 'optimization' | 'troubleshooting';
}

export const codeEditingExamples: CodeEditingExample[] = [
  {
    id: 'ot2_to_flex_migration',
    label: 'OT-2 to Flex Migration',
    description: 'Basic OT-2 protocol ready for migration to Flex',
    category: 'migration',
    initialCode: `from opentrons import protocol_api

metadata = {
    'protocolName': 'Simple Transfer - OT-2',
    'author': 'Lab User',
    'description': 'Basic liquid transfer protocol for OT-2',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    
    # Transfer 100ul from source A1 to destination A1
    pipette.transfer(100, source_plate['A1'], dest_plate['A1'])`,
    suggestedInstruction: 'Please migrate this OT-2 protocol to work on the Opentrons Flex robot'
  },
  
  {
    id: 'flex_to_ot2_migration',
    label: 'Flex to OT-2 Migration',
    description: 'Flex protocol that needs to run on OT-2',
    category: 'migration',
    initialCode: `from opentrons import protocol_api

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.19"
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'D1')
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'C1')
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'C2')
    trash = protocol.load_trash_bin('A3')
    
    # Load pipette
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])
    
    # Transfer 200ul from source A1 to destination A1
    pipette.pick_up_tip()
    pipette.aspirate(200, source_plate['A1'])
    pipette.dispense(200, dest_plate['A1'])
    pipette.drop_tip()`,
    suggestedInstruction: 'Please convert this Flex protocol to work on OT-2 robot'
  },
  
  {
    id: 'serial_dilution_basic',
    label: 'Serial Dilution Protocol',
    description: 'Basic serial dilution that can be optimized',
    category: 'basic',
    initialCode: `from opentrons import protocol_api

metadata = {
    'protocolName': 'Serial Dilution',
    'author': 'Lab User',
    'description': 'Basic serial dilution protocol',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    dilution_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    
    # Add diluent to all wells first
    for i in range(1, 12):
        pipette.transfer(90, reservoir['A1'], dilution_plate[f'A{i+1}'])
    
    # Add sample to first well
    pipette.transfer(100, reservoir['A2'], dilution_plate['A1'])
    
    # Perform serial dilution
    for i in range(11):
        pipette.transfer(10, dilution_plate[f'A{i+1}'], dilution_plate[f'A{i+2}'], mix_after=(3, 50))`,
    suggestedInstruction: 'Optimize this serial dilution protocol for better efficiency and add proper mixing'
  },
  
  {
    id: 'pcr_setup',
    label: 'PCR Setup Protocol',
    description: 'Basic PCR reaction setup protocol',
    category: 'basic',
    initialCode: `from opentrons import protocol_api

metadata = {
    'protocolName': 'PCR Setup',
    'author': 'Lab User',
    'description': 'Set up PCR reactions',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack_20 = protocol.load_labware('opentrons_96_tiprack_20ul', '1')
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', '2')
    pcr_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '3')
    reagent_rack = protocol.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '4')
    
    # Load pipettes
    p20 = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[tiprack_20])
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack_300])
    
    # Define reagents
    master_mix = reagent_rack['A1']
    primer_f = reagent_rack['A2']
    primer_r = reagent_rack['A3']
    template = reagent_rack['B1']
    
    # Add master mix to all wells
    for well in pcr_plate.wells()[:8]:
        p20.transfer(15, master_mix, well)
    
    # Add primers
    for well in pcr_plate.wells()[:8]:
        p20.transfer(1, primer_f, well)
        p20.transfer(1, primer_r, well)
    
    # Add template DNA
    for well in pcr_plate.wells()[:8]:
        p20.transfer(3, template, well, mix_after=(3, 10))`,
    suggestedInstruction: 'Add volume calculations and improve the mixing strategy for this PCR setup'
  },
  
  {
    id: 'problematic_protocol',
    label: 'Protocol with Common Errors',
    description: 'Protocol containing typical mistakes for troubleshooting practice',
    category: 'troubleshooting',
    initialCode: `from opentrons import protocol_api

metadata = {
    'protocolName': 'Problematic Protocol',
    'author': 'Lab User',
    'description': 'Protocol with some issues to fix',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '1')  # Slot conflict!
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    
    # Missing tip pickup
    pipette.aspirate(100, source_plate['A1'])
    pipette.dispense(100, dest_plate['A1'])
    pipette.drop_tip()  # Will error - no tip to drop
    
    # Transfer without proper tip handling
    pipette.transfer(50, source_plate['B1'], dest_plate['B1'])`,
    suggestedInstruction: 'Please identify and fix all the errors in this protocol'
  },
  
  {
    id: 'optimization_candidate',
    label: 'Protocol Needing Optimization',
    description: 'Inefficient protocol that can be optimized for speed',
    category: 'optimization',
    initialCode: `from opentrons import protocol_api

metadata = {
    'protocolName': 'Inefficient Protocol',
    'author': 'Lab User',
    'description': 'Protocol that needs optimization',
    'apiLevel': '2.19'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])
    
    # Inefficient: picking up and dropping tips for each transfer
    for i in range(8):
        for j in range(12):
            well_id = chr(65 + i) + str(j + 1)
            pipette.pick_up_tip()
            pipette.aspirate(50, source_plate[well_id])
            pipette.dispense(50, dest_plate[well_id])
            pipette.drop_tip()`,
    suggestedInstruction: 'Optimize this protocol to reduce tip usage and improve execution speed'
  }
];

export const getExamplesByCategory = (category: CodeEditingExample['category']) => {
  return codeEditingExamples.filter(example => example.category === category);
};

export const getExampleById = (id: string) => {
  return codeEditingExamples.find(example => example.id === id);
}; 