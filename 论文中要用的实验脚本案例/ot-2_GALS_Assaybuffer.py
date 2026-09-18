from opentrons import protocol_api

metadata = {"apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    # Robot: OT-2, API: 2.19
    
    # Labware
    heater_shaker = protocol.load_module('heaterShakerModuleV1', '1')
    sample_plate = protocol.load_labware('nest_96_wellplate_2ml_deep', '2')
    reagent_rack = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '4')
    tip_rack = protocol.load_labware('opentrons_96_tiprack_1000ul', '5')
    
    # Pipette
    p1000 = protocol.load_instrument('p1000_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Reagent Locations
    pbs = reagent_rack.wells_by_name()['A1']
    fald = reagent_rack.wells_by_name()['B1']
    mgso4 = reagent_rack.wells_by_name()['C1']
    tpp = reagent_rack.wells_by_name()['A2']
    reagent_d = reagent_rack.wells_by_name()['B2']
    assay_buffer = reagent_rack.wells_by_name()['A3'] # Empty mixing tube
    water = reagent_rack.wells_by_name()['B3']        # Water source
    
    # Phase 1: Assay Buffer Formulation
    # 1.1 Prepare Assay Buffer
    # Water
    p1000.pick_up_tip()
    for _ in range(39):
        p1000.aspirate(1000, water)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # PBS
    p1000.pick_up_tip()
    for _ in range(5):
        p1000.aspirate(1000, pbs)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # FALD
    p1000.pick_up_tip()
    for _ in range(5):
        p1000.aspirate(1000, fald)
        p1000.dispense(1000, assay_buffer)
    p1000.drop_tip()
    
    # MgSO4
    p1000.pick_up_tip()
    p1000.aspirate(500, mgso4)
    p1000.dispense(500, assay_buffer)
    p1000.drop_tip()
    
    # TPP
    p1000.pick_up_tip()
    p1000.aspirate(500, tpp)
    p1000.dispense(500, assay_buffer)
    
    # 1.2 Mix Assay Buffer
    p1000.mix(15, 800, assay_buffer)
    p1000.drop_tip()
    
    # Phase 2: Reaction Setup and Incubation
    # 2.1 Distribute Assay Buffer
    heater_shaker.close_labware_latch()  # Close latch before any pipetting near HS
    for col in sample_plate.columns():
        p1000.pick_up_tip()
        for well in col:
            p1000.aspirate(500, assay_buffer)
            p1000.dispense(500, well)
        p1000.drop_tip()
    
    # 2.2 Manual Intervention & Incubation Start
    protocol.pause("Part 1 complete. Move the 96-well plate from Slot 2 to the Heater-Shaker in Slot 1. Close the Heater-Shaker lid. Click RESUME in the Opentrons App.")
    heater_shaker.set_target_temperature(37)  # Minimum valid temperature is 37°C
    heater_shaker.set_and_wait_for_shake_speed(800)
    protocol.comment("Incubation started. Run Script 2 after 24 hours.")