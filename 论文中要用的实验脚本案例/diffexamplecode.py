------- SEARCH
plate = protocol.load_labware('96_wellplate_flat', '1')
=======
plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
+++++++ REPLACE


# === ITERATION 1: FAILED CODE ===
def run(protocol):
    pipette = protocol.load_instrument('p20_single_gen2', 'left')
    # Error: Volume exceeds pipette capacity
    pipette.aspirate(50, source_well)
    
# Simulation Error:
# ValueError: Volume 50.0 exceeds maximum volume (20.0) for pipette

# === AI-GENERATED DIFF PATCH ===
------- SEARCH
    pipette = protocol.load_instrument('p20_single_gen2', 'left')
    pipette.aspirate(50, source_well)
=======
    pipette = protocol.load_instrument('p300_single_gen2', 'left')
    pipette.aspirate(50, source_well)
+++++++ REPLACE

# === ITERATION 2: CORRECTED CODE ===
def run(protocol):
    pipette = protocol.load_instrument('p300_single_gen2', 'left')
    # Fixed: Upgraded to P300 pipette for 50µL volume
    pipette.aspirate(50, source_well)

# === ITERATION 1: FAILED CODE ===
def run(protocol):
    pipette = protocol.load_instrument('p20_single_gen2', 'left')
    # Error: Volume exceeds pipette capacity
    pipette.aspirate(50, source_well)
    
# Simulation Error:
# ValueError: Volume 50.0 exceeds maximum volume (20.0) for pipette

# === AI-GENERATED DIFF PATCH ===
------- SEARCH
    pipette = protocol.load_instrument('p20_single_gen2', 'left')
    pipette.aspirate(50, source_well)
=======
    pipette = protocol.load_instrument('p300_single_gen2', 'left')
    pipette.aspirate(50, source_well)
+++++++ REPLACE

# === ITERATION 2: CORRECTED CODE ===
def run(protocol):
    pipette = protocol.load_instrument('p300_single_gen2', 'left')
    # Fixed: Upgraded to P300 pipette for 50µL volume
    pipette.aspirate(50, source_well)

# Original Code
draw_volume = 150  # uL of ink per dot
# SEARCH/REPLACE
------- SEARCH
draw_volume = 150  # uL of ink per dot
=======
draw_volume = 200  # uL of ink per dot
+++++++ REPLACE

# Output:
draw_volume = 200  # uL of ink per dot



"""
Diff Strategy Examples for Opentrons Automation
===============================================

This file demonstrates the three matching strategies used in diff_utils.py
with real Opentrons automation scenarios that highlight common pain points.

Each example shows:
1. Original Code (based on real automation needs)
2. Diff Input (SEARCH/REPLACE format)
3. Expected Output
4. Which strategy would be used and why

Author: Gaoyuan
"""

from backend.diff_utils import apply_diff

# =============================================================================
# STRATEGY 1: EXACT MATCH
# =============================================================================
# Use Case: Precise parameter changes (volume, temperature, etc.)
# Pain Point: Need to quickly adjust liquid volumes across protocols

def example_strategy_1_exact_match():
    """
    Scenario: Changing pipette volume from 50uL to 100uL
    This demonstrates exact string matching for precise parameter updates.
    """
    
    original_code = '''# Load Pipettes
    p1000_1ch = protocol_context.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack_50ul])
    
    # Drawing parameters
    draw_volume = 50  # uL of ink per dot
    
    # Perform drawing
    p1000_1ch.transfer(draw_volume, ink_well, target_wells)'''
    
    diff_input = '''------- SEARCH
    draw_volume = 50  # uL of ink per dot
=======
    draw_volume = 100  # uL of ink per dot
+++++++ REPLACE'''
    
    result = apply_diff(original_code, diff_input)
    
    print("=== STRATEGY 1: EXACT MATCH ===")
    print("Original:")
    print(original_code)
    print("\nDiff:")
    print(diff_input)
    print("\nResult:")
    print(result)
    print("\nStrategy Used: Exact string match - found exact text '    draw_volume = 50  # uL of ink per dot'")
    print("Pain Point Solved: Quick volume parameter adjustment\n")
    
    return result

# =============================================================================
# STRATEGY 2: LINE-TRIMMED FALLBACK
# =============================================================================
# Use Case: Handling different indentation/formatting
# Pain Point: Code formatted differently but logically same

def example_strategy_2_whitespace_tolerance():
    """
    Scenario: Changing labware layout despite different indentation
    This demonstrates whitespace-tolerant matching for formatting variations.
    """
    
    original_code = '''    # Load Labware
        tiprack_50ul = protocol_context.load_labware('opentrons_flex_96_tiprack_200ul', 'C2', '200uL Tips')
        pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2', 'ELISA Plate')
        reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'B3', 'Ink Reservoir')'''
    
    # Notice: Different indentation in search block (2 spaces vs 4)
    diff_input = '''------- SEARCH
  pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2', 'ELISA Plate')
=======
  pcr_plate = protocol_context.load_labware('corning_384_wellplate_112ul_flat', 'B2', '384-Well Plate')
+++++++ REPLACE'''
    
    result = apply_diff(original_code, diff_input)
    
    print("=== STRATEGY 2: LINE-TRIMMED FALLBACK ===")
    print("Original (with 8 spaces indent):")
    print(repr(original_code))
    print("\nDiff (with 2 spaces indent):")
    print(diff_input)
    print("\nResult:")
    print(result)
    print("\nStrategy Used: Line-trimmed fallback - exact match failed due to whitespace, but trimmed lines matched")
    print("Pain Point Solved: Handle different code formatting/indentation\n")
    
    return result

# =============================================================================
# STRATEGY 3: BLOCK ANCHOR FALLBACK
# =============================================================================
# Use Case: Major code block restructuring
# Pain Point: Need to modify large blocks where middle content might vary

def example_strategy_3_block_anchor():
    """
    Scenario: Changing entire pipetting workflow while preserving structure
    This demonstrates first/last line matching for structural changes.
    """
    
    original_code = '''def run(protocol_context):
    """Protocol to draw a cute cat on an ELISA plate"""
    # Load Trash Bin
    trash_bin = protocol_context.load_trash_bin('A3')
    
    # Load Labware - original setup
    tiprack_50ul = protocol_context.load_labware('opentrons_flex_96_tiprack_200ul', 'C2')
    pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'B3')
    
    # Original cat coordinates
    cat_face_coords = [('B', 4), ('B', 9), ('C', 3)]
    target_wells = [pcr_plate.wells_by_name()[f'{row}{col}'] for row, col in cat_face_coords]
    
    protocol_context.comment("Protocol complete")'''
    
    # Search block: Only first and last lines will match exactly
    # Middle content is different due to added comments/modifications
    diff_input = '''------- SEARCH
    # Load Labware - original setup
    tiprack_50ul = protocol_context.load_labware('opentrons_flex_96_tiprack_200ul', 'C2')
    pcr_plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'B2')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'B3')
    
    # Original cat coordinates
    cat_face_coords = [('B', 4), ('B', 9), ('C', 3)]
    target_wells = [pcr_plate.wells_by_name()[f'{row}{col}'] for row, col in cat_face_coords]
=======
    # Load Labware - batch processing setup
    tiprack_1000ul = protocol_context.load_labware('opentrons_flex_96_tiprack_1000ul', 'C2')
    source_plate = protocol_context.load_labware('nest_96_wellplate_2ml_deep', 'B2') 
    dest_plates = [
        protocol_context.load_labware('corning_384_wellplate_112ul_flat', 'B3'),
        protocol_context.load_labware('corning_384_wellplate_112ul_flat', 'C3')
    ]
    
    # Batch transfer coordinates for 384-well processing
    batch_coords = [(row, col) for row in 'ABCDEFGH' for col in range(1, 25)]
    all_wells = [plate.wells_by_name()[f'{row}{col}'] for plate in dest_plates 
                 for row, col in batch_coords[:192]]  # 192 wells per plate
+++++++ REPLACE'''
    
    result = apply_diff(original_code, diff_input)
    
    print("=== STRATEGY 3: BLOCK ANCHOR FALLBACK ===")
    print("Original:")
    print(original_code)
    print("\nDiff (targeting large structural change):")
    print(diff_input)
    print("\nResult:")
    print(result)
    print("\nStrategy Used: Block anchor fallback - first line '# Load Labware...' and last line 'target_wells = ...' matched")
    print("Pain Point Solved: Major workflow restructuring from single-plate drawing to batch 384-well processing\n")
    
    return result

# =============================================================================
# REAL AUTOMATION PAIN POINTS EXAMPLES
# =============================================================================

def example_batch_volume_adjustment():
    """
    Real Pain Point: Adjusting transfer volumes across multiple steps
    """
    
    original = '''    # Step 1: Sample preparation
    p1000.transfer(50, source_plate['A1'], dest_plate['A1'])
    p1000.transfer(50, source_plate['A2'], dest_plate['A2'])
    
    # Step 2: Reagent addition  
    p1000.transfer(25, reagent_reservoir['A1'], dest_plate['A1'])
    p1000.transfer(25, reagent_reservoir['A1'], dest_plate['A2'])'''
    
    # Batch change all 50uL to 75uL and 25uL to 40uL
    diff = '''------- SEARCH
    p1000.transfer(50, source_plate['A1'], dest_plate['A1'])
    p1000.transfer(50, source_plate['A2'], dest_plate['A2'])
=======
    p1000.transfer(75, source_plate['A1'], dest_plate['A1'])
    p1000.transfer(75, source_plate['A2'], dest_plate['A2'])
+++++++ REPLACE

------- SEARCH
    p1000.transfer(25, reagent_reservoir['A1'], dest_plate['A1'])
    p1000.transfer(25, reagent_reservoir['A1'], dest_plate['A2'])
=======
    p1000.transfer(40, reagent_reservoir['A1'], dest_plate['A1'])
    p1000.transfer(40, reagent_reservoir['A1'], dest_plate['A2'])
+++++++ REPLACE'''
    
    result = apply_diff(original, diff)
    print("=== REAL PAIN POINT: BATCH VOLUME ADJUSTMENT ===")
    print("Before:", original)
    print("\nAfter:", result)
    print("Benefit: Changed multiple transfer volumes in one operation\n")

def example_deck_layout_migration():
    """
    Real Pain Point: Migrating from OT-2 to Flex deck layout
    """
    
    original = '''    # OT-2 Layout
    tips = protocol_context.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', '3')'''
    
    diff = '''------- SEARCH
    # OT-2 Layout
    tips = protocol_context.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', '3')
=======
    # Flex Layout  
    tips = protocol_context.load_labware('opentrons_flex_96_tiprack_300ul', 'C1')
    plate = protocol_context.load_labware('corning_96_wellplate_360ul_flat', 'D1')
    reservoir = protocol_context.load_labware('nest_12_reservoir_15ml', 'D2')
+++++++ REPLACE'''
    
    result = apply_diff(original, diff)
    print("=== REAL PAIN POINT: DECK LAYOUT MIGRATION ===")
    print("Before (OT-2):", original)
    print("\nAfter (Flex):", result)
    print("Benefit: Easy migration between robot platforms\n")

if __name__ == "__main__":
    print("DIFF STRATEGY EXAMPLES FOR OPENTRONS AUTOMATION")
    print("=" * 60)
    print()
    
    # Run all examples
    example_strategy_1_exact_match()
    example_strategy_2_whitespace_tolerance()  
    example_strategy_3_block_anchor()
    example_batch_volume_adjustment()
    example_deck_layout_migration()
    
    print("All examples completed! Each demonstrates how diff strategies solve real automation pain points.")