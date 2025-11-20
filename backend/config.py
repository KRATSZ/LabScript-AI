# -*- coding: utf-8 -*-
"""Configuration file for the Opentrons AI Protocol Generator."""

# --- Common Pitfalls for OT-2 ---
COMMON_PITFALLS_OT2 = [
    "Use metadata = {{\"apiLevel\": \"2.19\"}} for OT-2, not the 'requirements' dictionary.",
    "Deck slots for OT-2 are strings of numbers: '1', '2', '3', ..., '11'. Do not use 'A1', 'B2', etc.",
    "Pipette names must be GEN2, e.g., 'p20_single_gen2', 'p300_multi_gen2'. Avoid old names like 'p10_multi'.",
    "The trash is fixed in slot 12. Do not use protocol.load_trash_bin().",
    "For the magnetic module on OT-2, the correct API name is 'magneticModuleV2'.",
    "Ensure every pick_up_tip() has a corresponding drop_tip() or return_tip() to avoid errors.",
    "Check pipette volume limits carefully: p20 (1-20μL), p300 (20-300μL), p1000 (100-1000μL).",
    "Do not use labware with 'flex' in the name on an OT-2 protocol.",
    "Before aspirating from a magnetic bead pellet, you must call magnetic_module.disengage().",
    "After dispensing beads for mixing, call magnetic_module.engage() to pellet them before removing supernatant."
]

CODE_EXAMPLES = """---
--- OT-2 EXAMPLES (API Level 2.19) ---
---

Example 1: Basic OT-2 Setup & Transfer
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')

    # Pipette
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Commands
    p300.pick_up_tip()
    p300.aspirate(100, reservoir.wells_by_name()['A1'])
    p300.dispense(100, plate.wells_by_name()['A1'])
    p300.drop_tip()
```

Example 2: OT-2 Magnetic Bead Purification
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Modules
    mag_mod = protocol.load_module('magneticModuleV2', '1')
    
    # Labware
    plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Pipette
    p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])
    
    # Reagents
    beads = reservoir.wells_by_name()['A1']
    supernatant = plate.rows_by_name()['A'][0]
    
    # Protocol
    p300.pick_up_tip()
    p300.aspirate(180, beads)
    p300.dispense(180, supernatant)
    p300.mix(10, 200, supernatant)
    p300.drop_tip()
    
    protocol.delay(minutes=5) # Incubate
    mag_mod.engage()
    protocol.delay(minutes=2) # Let beads settle
    
    p300.pick_up_tip()
    p300.aspirate(200, supernatant) # Remove supernatant
    p300.dispense(200, protocol.fixed_trash['A1'])
    p300.drop_tip()
    
    mag_mod.disengage()
```

Example 3: OT-2 Serial Dilution
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_20ul', '1')
    tuberack = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')

    # Pipette
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tiprack])

    # Reagents
    stock = tuberack.wells_by_name()['A1']
    diluent = plate.columns_by_name()['1']
    
    # Protocol
    # Distribute diluent
    p20.pick_up_tip()
    for well in diluent:
        p20.aspirate(10, stock) # Incorrect, should be from a diluent source. Example for structure.
        p20.dispense(10, well)
    p20.drop_tip()

    # Serial Dilution
    p20.transfer(10, plate.columns_by_name()['1'], plate.columns_by_name()['2'], mix_after=(3, 10))
```

---
--- FLEX EXAMPLES (API Level 2.19) ---
---

Example 4: Basic Flex Setup & Transfer
```python
from opentrons import protocol_api

requirements = {{"robotType": "Flex", "apiLevel": "2.19"}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'D3')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'D2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', 'C2')
    trash = protocol.load_trash_bin('A3')

    # Pipette
    p1000 = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])

    # Commands
    p1000.pick_up_tip()
    p1000.aspirate(100, reservoir['A1'])
    p1000.dispense(100, plate['A1'])
    p1000.drop_tip()
```
"""

# 1. API Configuration
api_key = "YOUR_OPENAI_API_KEY"
base_url = "https://api.ai190.com/v1"
model_name = "gemini-2.5-pro"
# Specialized API for Intent Classification (faster model)
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY"
DEEPSEEK_BASE_URL = "https://www.sophnet.com/api/open-apis/v1"
DEEPSEEK_INTENT_MODEL = "DeepSeek-V3-Fast"

# Reviewer configuration (textual reasoning + optional vision assist)
REVIEW_PRIMARY_MODEL_NAME = model_name  # default to main Gemini model
REVIEW_VISION_TOOL_CONFIG = {
    "model": "zai-org/GLM-4.5V",
    "base_url": "https://api.siliconflow.cn/v1",
    "api_key": "YOUR_GLM_API_KEY",
}

# 2. Valid Opentrons Names and Code Examples (Knowledge Base)

# --- Original Flat Lists (for reference and comprehensive checks) ---
ALL_LABWARE_NAMES = [
    "agilent_1_reservoir_290ml", "appliedbiosystemsmicroamp_384_wellplate_40ul",
    "axygen_1_reservoir_90ml", "biorad_384_wellplate_50ul",
    "biorad_96_wellplate_200ul_pcr", "corning_12_wellplate_6.9ml_flat",
    "corning_24_wellplate_3.4ml_flat", "corning_384_wellplate_112ul_flat",
    "corning_48_wellplate_1.6ml_flat", "corning_6_wellplate_16.8ml_flat",
    "corning_96_wellplate_360ul_flat", "geb_96_tiprack_1000ul",
    "geb_96_tiprack_10ul", "nest_12_reservoir_15ml", "nest_1_reservoir_195ml",
    "nest_1_reservoir_290ml", "nest_96_wellplate_100ul_pcr_full_skirt",
    "nest_96_wellplate_200ul_flat", "nest_96_wellplate_2ml_deep",
    "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical",
    "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical",
    "opentrons_15_tuberack_falcon_15ml_conical", "opentrons_15_tuberack_nest_15ml_conical",
    "opentrons_24_aluminumblock_generic_2ml_screwcap",
    "opentrons_24_aluminumblock_nest_0.5ml_screwcap",
    "opentrons_24_aluminumblock_nest_1.5ml_screwcap",
    "opentrons_24_aluminumblock_nest_1.5ml_snapcap",
    "opentrons_24_aluminumblock_nest_2ml_screwcap",
    "opentrons_24_aluminumblock_nest_2ml_snapcap",
    "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
    "opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap",
    "opentrons_24_tuberack_generic_2ml_screwcap",
    "opentrons_24_tuberack_nest_0.5ml_screwcap",
    "opentrons_24_tuberack_nest_1.5ml_screwcap",
    "opentrons_24_tuberack_nest_1.5ml_snapcap",
    "opentrons_24_tuberack_nest_2ml_screwcap",
    "opentrons_24_tuberack_nest_2ml_snapcap",
    "opentrons_6_tuberack_falcon_50ml_conical", "opentrons_6_tuberack_nest_50ml_conical",
    "opentrons_96_deep_well_temp_mod_adapter",
    "opentrons_96_aluminumblock_biorad_wellplate_200ul",
    "opentrons_96_aluminumblock_generic_pcr_strip_200ul",
    "opentrons_96_aluminumblock_nest_wellplate_100ul",
    "opentrons_96_deep_well_adapter",
    "opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep",
    "opentrons_96_filtertiprack_1000ul", "opentrons_96_filtertiprack_10ul",
    "opentrons_96_filtertiprack_200ul", "opentrons_96_filtertiprack_20ul",
    "opentrons_96_flat_bottom_adapter",
    "opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat",
    "opentrons_96_pcr_adapter",
    "opentrons_96_pcr_adapter_nest_wellplate_100ul_pcr_full_skirt",
    "opentrons_96_tiprack_1000ul", "opentrons_96_tiprack_10ul",
    "opentrons_96_tiprack_20ul", "opentrons_96_tiprack_300ul",
    "opentrons_96_well_aluminum_block",
    "opentrons_96_wellplate_200ul_pcr_full_skirt",
    "opentrons_aluminum_flat_bottom_plate",
    "opentrons_flex_96_filtertiprack_1000ul", "opentrons_flex_96_filtertiprack_200ul",
    "opentrons_flex_96_filtertiprack_50ul", "opentrons_flex_96_tiprack_1000ul",
    "opentrons_flex_96_tiprack_200ul", "opentrons_flex_96_tiprack_50ul",
    "opentrons_flex_96_tiprack_adapter", "opentrons_flex_deck_riser",
    "opentrons_tough_pcr_auto_sealing_lid", "opentrons_universal_flat_adapter",
    "opentrons_universal_flat_adapter_corning_384_wellplate_112ul_flat",
    "thermoscientificnunc_96_wellplate_1300ul",
    "thermoscientificnunc_96_wellplate_2000ul", "usascientific_12_reservoir_22ml",
    "usascientific_96_wellplate_2.4ml_deep"
]

ALL_INSTRUMENT_NAMES = [
    # OT-2 GEN2
    "p20_single_gen2","p20_multi_gen2","p300_single_gen2","p300_multi_gen2","p1000_single_gen2",
    # Flex
    "flex_1channel_50", "flex_1channel_1000",
    "flex_8channel_50", "flex_8channel_1000",
    "flex_96channel_1000"
]

ALL_MODULE_NAMES = [
    # API Names (Prefer these in code)
    "temperatureModuleV2",     # OT-2/Flex API Name
    "thermocyclerModuleV2",    # OT-2/Flex API Name
    "magneticModuleV2",        # OT-2 API Name
    "heaterShakerModuleV1",    # OT-2/Flex API Name
    "magneticBlockV1",         # Flex Only API Name
    # User-facing Names (Less preferred for load_module)
    "temperature module gen2", # OT-2/Flex
    "thermocycler module gen2",# OT-2/Flex
    "magnetic module gen2",    # OT-2/Flex
]


# --- Categorized Lists ---

# Labware
LABWARE_FLEX = sorted([name for name in ALL_LABWARE_NAMES if "flex" in name])
LABWARE_OT2_AND_COMMON = sorted([name for name in ALL_LABWARE_NAMES if "flex" not in name])

# Instruments
INSTRUMENTS_OT2 = sorted([
    "p20_single_gen2","p20_multi_gen2","p300_single_gen2","p300_multi_gen2","p1000_single_gen2"
])
INSTRUMENTS_FLEX = sorted([
    "flex_1channel_50", "flex_1channel_1000",
    "flex_8channel_50", "flex_8channel_1000",
    "flex_96channel_1000"
])

# Modules
MODULES_OT2 = sorted([
    "magneticModuleV2",        # OT-2 Only API Name
])
MODULES_FLEX = sorted([
    "magneticBlockV1",         # Flex Only API Name
])
MODULES_SHARED = sorted([
    "temperatureModuleV2",     # OT-2/Flex API Name
    "thermocyclerModuleV2",    # OT-2/Flex API Name
    "heaterShakerModuleV1",    # OT-2/Flex API Name
    "temperature module gen2", # User-facing, OT-2/Flex
    "thermocycler module gen2",# User-facing, OT-2/Flex
    # "magnetic module gen2" is ambiguous, typically magneticModuleV2 for OT-2.
    # For clarity, it's better to use specific API names.
])

# For UI population, it's useful to have combined lists for each robot type
LABWARE_FOR_OT2 = sorted(list(set(LABWARE_OT2_AND_COMMON))) # All non-Flex labware
LABWARE_FOR_FLEX = sorted(list(set(LABWARE_FLEX + LABWARE_OT2_AND_COMMON))) # Flex can use its own and common ones

INSTRUMENTS_FOR_OT2 = INSTRUMENTS_OT2
INSTRUMENTS_FOR_FLEX = INSTRUMENTS_FLEX

MODULES_FOR_OT2 = sorted(list(set(MODULES_OT2 + MODULES_SHARED)))
MODULES_FOR_FLEX = sorted(list(set(MODULES_FLEX + MODULES_SHARED)))


# --- Common Pitfalls for OT-2 ---
COMMON_PITFALLS_OT2 = [
    "Use metadata = {{\"apiLevel\": \"2.19\"}} for OT-2, not the 'requirements' dictionary.",
    "Deck slots for OT-2 are strings of numbers: '1', '2', '3', ..., '11'. Do not use 'A1', 'B2', etc.",
    "Pipette names must be GEN2, e.g., 'p20_single_gen2', 'p300_multi_gen2'. Avoid old names like 'p10_multi'.",
    "The trash is fixed in slot 12. Do not use protocol.load_trash_bin().",
    "For the magnetic module on OT-2, the correct API name is 'magneticModuleV2'.",
    "Ensure every pick_up_tip() has a corresponding drop_tip() or return_tip() to avoid errors.",
    "Check pipette volume limits carefully: p20 (1-20μL), p300 (20-300μL), p1000 (100-1000μL).",
    "Do not use labware with 'flex' in the name on an OT-2 protocol.",
    "Before aspirating from a magnetic bead pellet, you must call magnetic_module.disengage().",
    "After dispensing beads for mixing, call magnetic_module.engage() to pellet them before removing supernatant."
]

# --- Deprecated Original Variables (will be removed or updated if no longer needed by other parts of your code) ---
# These are now superseded by the ALL_ and categorized lists above.
# If other parts of your project directly use these exact variable names,
# you might need to update them or temporarily keep these as aliases.
VALID_LABWARE_NAMES = ALL_LABWARE_NAMES
VALID_INSTRUMENT_NAMES = ALL_INSTRUMENT_NAMES
VALID_MODULE_NAMES = ALL_MODULE_NAMES
# It's recommended to update downstream code to use the new categorized lists (e.g., LABWARE_FOR_FLEX)
# or the comprehensive ALL_ lists (e.g., ALL_LABWARE_NAMES) as appropriate.


CODE_EXAMPLES = """---
--- OT-2 EXAMPLES (API Level 2.19) ---
---

Example 1: Basic OT-2 Setup & Transfer
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')

    # Pipette
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Commands
    p300.pick_up_tip()
    p300.aspirate(100, reservoir.wells_by_name()['A1'])
    p300.dispense(100, plate.wells_by_name()['A1'])
    p300.drop_tip()
```

Example 2: OT-2 Magnetic Bead Purification
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Modules
    mag_mod = protocol.load_module('magneticModuleV2', '1')
    
    # Labware
    plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Pipette
    p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])
    
    # Reagents
    beads = reservoir.wells_by_name()['A1']
    supernatant = plate.rows_by_name()['A'][0]
    
    # Protocol
    p300.pick_up_tip()
    p300.aspirate(180, beads)
    p300.dispense(180, supernatant)
    p300.mix(10, 200, supernatant)
    p300.drop_tip()
    
    protocol.delay(minutes=5) # Incubate
    mag_mod.engage()
    protocol.delay(minutes=2) # Let beads settle
    
    p300.pick_up_tip()
    p300.aspirate(200, supernatant) # Remove supernatant
    p300.dispense(200, protocol.fixed_trash['A1'])
    p300.drop_tip()
    
    mag_mod.disengage()
```

Example 3: OT-2 Serial Dilution
```python
from opentrons import protocol_api

metadata = {{'apiLevel': '2.19'}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_20ul', '1')
    tuberack = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '2')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')

    # Pipette
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tiprack])

    # Reagents
    stock = tuberack.wells_by_name()['A1']
    diluent = plate.columns_by_name()['1']
    
    # Protocol
    # Distribute diluent
    p20.pick_up_tip()
    for well in diluent:
        p20.aspirate(10, stock) # Incorrect, should be from a diluent source. Example for structure.
        p20.dispense(10, well)
    p20.drop_tip()

    # Serial Dilution
    p20.transfer(10, plate.columns_by_name()['1'], plate.columns_by_name()['2'], mix_after=(3, 10))
```

---
--- FLEX EXAMPLES (API Level 2.19) ---
---

Example 4: Basic Flex Setup & Transfer
```python
from opentrons import protocol_api

requirements = {{"robotType": "Flex", "apiLevel": "2.19"}}

def run(protocol: protocol_api.ProtocolContext):
    # Labware
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'D3')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'D2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', 'C2')
    trash = protocol.load_trash_bin('A3')

    # Pipette
    p1000 = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])

    # Commands
    p1000.pick_up_tip()
    p1000.aspirate(100, reservoir['A1'])
    p1000.dispense(100, plate['A1'])
    p1000.drop_tip()
```
""" 