# -*- coding: utf-8 -*-
"""Configuration file for the Opentrons AI Protocol Generator."""

# 1. API Configuration
# WARNING: Hardcoding API keys is generally not recommended for security reasons.
# Consider using environment variables or a configuration file for production.
api_key = "sk-TnKnlDtgvZgrG9wP543180A16aA34a1a978c90333dCa8746"
base_url = "https://api.pumpkinaigc.online/v1"
model_name = "gemini-2.5-pro-preview-05-06"

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
    "p20_single_gen2", "p300_single_gen2", "p1000_single_gen2",
    "p20_multi_gen2", "p300_multi_gen2", "p1000_multi_gen2",
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
    "magnetic module gen2",    # OT-2/Flex?
]

# --- Categorized Lists ---

# Labware
LABWARE_FLEX = sorted([name for name in ALL_LABWARE_NAMES if "flex" in name])
LABWARE_OT2_AND_COMMON = sorted([name for name in ALL_LABWARE_NAMES if "flex" not in name])

# Instruments
INSTRUMENTS_OT2 = sorted([
    "p20_single_gen2", "p300_single_gen2", "p1000_single_gen2",
    "p20_multi_gen2", "p300_multi_gen2", "p1000_multi_gen2",
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

# --- Deprecated Original Variables ---
VALID_LABWARE_NAMES = ALL_LABWARE_NAMES
VALID_INSTRUMENT_NAMES = ALL_INSTRUMENT_NAMES
VALID_MODULE_NAMES = ALL_MODULE_NAMES

# Code Examples
CODE_EXAMPLES = """Example 1: Basic Setup (Flex, API 2.20)
```python
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.20"}

def run(protocol: protocol_api.ProtocolContext):
    # load tip rack in deck slot D3
    tiprack = protocol.load_labware(
        load_name="opentrons_flex_96_tiprack_1000ul", location="D3"
    )
    # attach pipette to left mount
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tiprack]
    )
    # load well plate in deck slot D2
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat", location="D2"
    )
    # load reservoir in deck slot D1
    reservoir = protocol.load_labware(
        load_name="usascientific_12_reservoir_22ml", location="D1"
    )
    # load trash bin in deck slot A3 (Flex specific)
    trash = protocol.load_trash_bin(location="A3")
    # Put protocol commands here
```

Example 2: Basic Transfer (Flex, API 2.20)
```python
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel":"2.20"}

def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat",
        location="D1")
    tiprack_1 = protocol.load_labware(
        load_name="opentrons_flex_96_tiprack_200ul",
        location="D2")
    trash = protocol.load_trash_bin("A3")
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tiprack_1])

    pipette.pick_up_tip()
    pipette.aspirate(100, plate["A1"])
    pipette.dispense(100, plate["B1"])
    pipette.drop_tip()
```

Example 3: OT-2 Setup (API 2.20)
```python
from opentrons import protocol_api

metadata = {'apiLevel': '2.20'}

def run(protocol: protocol_api.ProtocolContext):
    # load tip rack in deck slot 3
    tiprack = protocol.load_labware(
        load_name="opentrons_96_tiprack_300ul", location="3"
    )
    # attach pipette to left mount
    pipette = protocol.load_instrument(
        instrument_name="p300_single_gen2",
        mount="left",
        tip_racks=[tiprack]
    )
    # load well plate in deck slot 2
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat", location="2"
    )
    # load tube rack in deck slot 1
    tube_rack = protocol.load_labware(
        load_name="opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap", location="1"
    )
    # OT-2 uses fixed trash in slot 12 by default, no need to load trash bin
    # Put protocol commands here
```
"""