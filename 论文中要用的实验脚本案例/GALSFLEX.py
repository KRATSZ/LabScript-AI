from opentrons import protocol_api

metadata = {
    'protocolName': 'Assay Buffer Preparation and Reaction Setup - Flex',
    'author': 'OpentronsAI',
    'description': 'Adapted from OT-2 to Flex - Assay buffer formulation and sample preparation',
    'source': 'OpentronsAI'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.22'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load trash bin
    trash = protocol.load_trash_bin('A3')
    
    # Load labware according to your specifications
    # 储液的配置槽放在甲板的D2位置 (Reagent rack in D2)
    reagent_rack = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 'D2')
    
    # 1000µL 的枪头放在 C3的位置 (1000µL tips in C3)
    tip_rack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'C3')
    
    # 96孔板放在夹板C2的位置 (96-well plate in C2)
    sample_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', 'C2')
    
    # Load pipette - using Flex 1-Channel 1000µL
    p1000 = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tip_rack])
    
    # Reagent Locations (same as original)
    pbs = reagent_rack.wells_by_name()['A1']
    fald = reagent_rack.wells_by_name()['B1']
    mgso4 = reagent_rack.wells_by_name()['C1']
    tpp = reagent_rack.wells_by_name()['A2']
    reagent_d = reagent_rack.wells_by_name()['B2']
    assay_buffer = reagent_rack.wells_by_name()['A3']  # Empty mixing tube
    water = reagent_rack.wells_by_name()['B3']         # Water source
    
    # Phase 1: Assay Buffer Formulation
    protocol.comment("Starting Phase 1: Assay Buffer Formulation")
    
    # 1.1 Prepare Assay Buffer
    # Water - 39mL total
    p1000.pick_up_tip()
    for _ in range(39):
        p1000.aspirate(1000, water)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # PBS - 5mL total
    p1000.pick_up_tip()
    for _ in range(5):
        p1000.aspirate(1000, pbs)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # FALD - 5mL total
    p1000.pick_up_tip()
    for _ in range(5):
        p1000.aspirate(1000, fald)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # MgSO4 - 0.5mL
    p1000.pick_up_tip()
    p1000.aspirate(500, mgso4)
    p1000.dispense(500, assay_buffer)
    p1000.drop_tip()
    
    # TPP - 0.5mL and mix
    p1000.pick_up_tip()
    p1000.aspirate(500, tpp)
    p1000.dispense(500, assay_buffer)
    
    # 1.2 Mix Assay Buffer
    protocol.comment("Mixing assay buffer")
    p1000.mix(15, 800, assay_buffer)
    p1000.drop_tip()
    
    # Phase 2: Reaction Setup (without heater-shaker as requested)
    protocol.comment("Starting Phase 2: Distributing Assay Buffer to Sample Plate")
    
    # 2.1 Distribute Assay Buffer to all wells in sample plate
    for col in sample_plate.columns():
        p1000.pick_up_tip()
        for well in col:
            p1000.aspirate(500, assay_buffer)
            p1000.dispense(500, well)
        p1000.drop_tip()
    
    protocol.comment("Protocol complete. Assay buffer has been distributed to all wells in the sample plate.")
    protocol.comment("Note: Heater-shaker functionality has been removed as requested.")