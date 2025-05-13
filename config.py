# -*- coding: utf-8 -*-
"""Configuration file for the Opentrons AI Protocol Generator."""

# 1. API Configuration
# WARNING: Hardcoding API keys is generally not recommended for security reasons.
# Consider using environment variables or a configuration file for production.
api_key = "sk-6a58c74845004701b700dfcd6f577c08" 
base_url = "https://api.deepseek.com"
model_name = 'deepseek-chat'

# 2. Valid Opentrons Names and Code Examples (Knowledge Base)
VALID_LABWARE_NAMES = [
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

VALID_INSTRUMENT_NAMES = [
    # OT-2 GEN2
    "p20_single_gen2", "p300_single_gen2", "p1000_single_gen2",
    "p20_multi_gen2", "p300_multi_gen2", "p1000_multi_gen2",
    # Flex
    "flex_1channel_50", "flex_1channel_1000",
    "flex_8channel_50", "flex_8channel_1000",
    "flex_96channel_1000"
]

VALID_MODULE_NAMES = [
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

CODE_EXAMPLES = """Example 1: Basic Setup (Flex, API 2.20)
```python
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.20"} # Use appropriate API level

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
        instrument_name="flex_1channel_1000", # Use a valid Flex instrument name
        mount="left",
        tip_racks=[tiprack_1])

    pipette.pick_up_tip()
    pipette.aspirate(100, plate["A1"])
    pipette.dispense(100, plate["B1"])
    pipette.drop_tip() # Drop into trash bin loaded earlier
```

Example 3: OT-2 Setup (API 2.20)
```python
from opentrons import protocol_api

metadata = {'apiLevel': '2.20'} # Example for OT-2

def run(protocol: protocol_api.ProtocolContext):
    # load tip rack in deck slot 3
    tiprack = protocol.load_labware(
        load_name="opentrons_96_tiprack_300ul", location="3" # Use OT-2 slot numbering
    )
    # attach pipette to left mount
    pipette = protocol.load_instrument(
        instrument_name="p300_single_gen2", # Use a valid OT-2 instrument name
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

Example 4: Comprehensive Modules Example (Flex, API 2.20)
```python
from opentrons import protocol_api
import random

requirements = {
    'robotType': 'Flex', # 2.15-2.20
    'apiLevel': '2.20'
}

# OVERVIEW:
# This example demonstrates a comprehensive Flex protocol using:
# - Multiple modules (heaterShaker, thermocycler, temperature, magneticBlock)
# - Gripper operations for plate movement
# - Multiple labware types (tubes, PCR plates, reservoirs)
# - Both 50μL and 1000μL pipettes

def run(protocol: protocol_api.ProtocolContext):
    # Set trash location
    default_trash = protocol.load_trash_bin(location = "A3")
    # Set up heater-shaker module and adapter
    heatershaker = protocol.load_module('heaterShakerModuleV1', location = "D1")
    hs_pcr_adapter = heatershaker.load_adapter('opentrons_96_pcr_adapter')
    # Set up temperature module with adapter/labware
    temp_block = protocol.load_module('temperature module gen2', location = "D3")
    temp_tubes  = temp_block.load_labware('opentrons_24_aluminumblock_nest_2ml_screwcap')
    # Set up thermocycler module with PCR plate
    thermocycler = protocol.load_module('thermocycler module gen2')
    pcr_plate = thermocycler.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt')
    # Set up magnetic block module
    mag_block = protocol.load_module('magneticBlockV1', location = "C2")
    # Set up 12-well reservoir
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', location = "C1")
    # Set up 50ul and 1000ul tip racks
    tiprack_50 = protocol.load_labware('opentrons_flex_96_tiprack_50ul', location = "B3")
    tiprack_1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', location = "B2")
    # Set up Flex pipettes: left P50 single-channel, right P1000 8-channel
    P50S = protocol.load_instrument("flex_1channel_50", "left", tip_racks=[tiprack_50])
    P1000M = protocol.load_instrument("flex_8channel_1000", "right", tip_racks=[tiprack_1000])

    reservoir_well = reservoir.wells_by_name()['A1']
    p50tips = [tip for tip in tiprack_50.wells()]

    #################################
    # Define function for gripper labware movement
    def move_to_new_location(labware, slot):
        protocol.move_labware(
            labware=labware,
            new_location=slot,
            use_gripper=True
        )

    # Open thermocycler lid
    thermocycler.open_lid()
    # Close heater-shaker latch
    heatershaker.close_labware_latch()
    # Use P50 single-channel to get tips, transfer 30ul from temp_tubes A1 to first column of pcr_plate, then return tip
    P50S.pick_up_tip(p50tips[random.randint(0, 95)])
    for well in pcr_plate.columns()[0]:
        P50S.aspirate(30,temp_tubes.wells_by_name()['A1'])
        P50S.dispense(30,well)
    P50S.return_tip()
    # Use P1000M multi-channel to get tips, aspirate 300ul from reservoir A1, mix in reservoir A1
    P1000M.pick_up_tip(tiprack_1000.wells_by_name()['A1'])
    for _ in range(10):
        P1000M.aspirate(300,reservoir_well.bottom(2))
        P1000M.dispense(300,reservoir_well.bottom(15))
    P1000M.blow_out()

    # Use P1000M multi-channel to transfer 150ul from reservoir A1 to pcr_plate A1, then return tip
    P1000M.aspirate(150,reservoir_well.bottom(2))
    P1000M.dispense(150,pcr_plate.wells_by_name()['A1'])
    P1000M.blow_out(pcr_plate.wells_by_name()['A1'].top(-3))
    P1000M.return_tip()

    # Close thermocycler lid
    thermocycler.close_lid()
    # Wait for 8 seconds
    protocol.delay(8)
    # Open thermocycler lid
    thermocycler.open_lid()
    # Open heater-shaker latch
    heatershaker.open_labware_latch()
    # Move pcr_plate to heater-shaker module
    move_to_new_location(pcr_plate, hs_pcr_adapter)
    # Close heater-shaker latch
    heatershaker.close_labware_latch()
    # Set heater-shaker speed to 500 rpm
    heatershaker.set_and_wait_for_shake_speed(500)
    # Wait for 30 seconds
    protocol.delay(30)
    # Stop heater-shaker
    heatershaker.deactivate_shaker()
    # Open heater-shaker latch
    heatershaker.open_labware_latch()
    # Move pcr_plate to magnetic module
    move_to_new_location(pcr_plate,mag_block)
    # Wait for 10 seconds
    protocol.delay(10)
    # Move pcr_plate to thermocycler
    move_to_new_location(pcr_plate,thermocycler)
    # Use P1000M multi-channel to transfer 180ul from pcr_plate A1 to reservoir A1, then return tip
    P1000M.pick_up_tip(tiprack_1000.wells_by_name()['A2'])
    P1000M.aspirate(180,pcr_plate.wells_by_name()['A1'])
    P1000M.dispense(180,reservoir_well)
    P1000M.return_tip()
```

Example 5: OT-3/Flex SLAS Demo with Gripper and Multiple Modules (API 2.20)
```python
from opentrons import protocol_api
from opentrons import types
import random

metadata = {
    'ctxName': 'SLAS Demo',
    'author': 'Example User',
}
requirements = {
    'robotType': 'Flex', # Updated from OT-3
    'apiLevel': '2.20'
}

def run(protocol: protocol_api.ProtocolContext):
    # DECK SETUP AND LABWARE
    temp_mod = protocol.load_module('temperature module gen2', '3')
    thermocycler = protocol.load_module('thermocycler module gen2')
    heater_shaker = protocol.load_module('heaterShakerModuleV1', '1')
    heater_shaker.close_labware_latch()
    tc_plate = thermocycler.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt')
    temp_plate = temp_mod.load_labware('opentrons_24_aluminumblock_nest_1.5ml_screwcap')
    moved_plate = protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', 2)

    hs_plate = heater_shaker.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt')

    tiprack_50 = protocol.load_labware('opentrons_flex_96_tiprack_50ul',  '9')
    tiprack_1000 = protocol.load_labware('opentrons_flex_96_tiprack_1000ul',  '6')

    # LOAD PIPETTES
    p1000 = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tiprack_1000])
    m50 = protocol.load_instrument("flex_8channel_50", "right", tip_racks=[tiprack_50])

    p1000tips = [tip for tip in tiprack_1000.wells()]

    m50.well_bottom_clearance.aspirate = 3
    m50.well_bottom_clearance.dispense = 3
    p1000.well_bottom_clearance.aspirate = 3
    p1000.well_bottom_clearance.dispense = 3

    # COMMANDS
    num_runs = 1

    thermocycler.open_lid()
    heater_shaker.close_labware_latch()

    random_wells = ['G7', 'B2', 'B4', 'E12', 'A8', 'H1', 'C3', 'D9', 'H10',
                    'A2', 'C11', 'B4', 'A6', 'D9', 'C9', 'H1', 'A11', 'D3']

    for run_loop_counter in range(num_runs):
        p1000.pick_up_tip(p1000tips[random.randint(0, 95)])
        p1000.aspirate(10, temp_plate.wells_by_name()['A1'])
        p1000.dispense(10, tc_plate.wells_by_name()['A1'])
        p1000.aspirate(10, temp_plate.wells_by_name()['B1'])
        p1000.dispense(10, tc_plate.wells_by_name()['B1'])

        # HIT PICK ON 96 WELL
        p1000.distribute(10, hs_plate.wells()[0],
                       [hs_plate.wells_by_name()[well]
                        for well in random_wells],
                       new_tip='never')

        p1000.return_tip()

        # -- Close the lid of Thermocycler
        thermocycler.close_lid()

        # -- Open the lid of the Thermocycler.
        thermocycler.open_lid()

        # -- Run heater shaker for 10 seconds
        heater_shaker.set_and_wait_for_shake_speed(500)
        protocol.delay(seconds=8)
        heater_shaker.deactivate_shaker()

        # -- Pipette entire row of heater shaker
        m50.pick_up_tip()
        for i, col in enumerate(hs_plate.rows()[0]):
            m50.aspirate(1, col)
            if i % 4 == 0:
                m50.touch_tip()
        m50.return_tip()

        # -- Move the plate onto magnetic block.
        protocol.move_labware(
            labware=moved_plate,
            new_location=8,
            use_gripper=True,
            drop_offset={"x": 0, "y": 0, "z": 34.5},  # Offset for mag module
        )

        # -- Move plate from magnetic block back to deck using the gripper.
        protocol.move_labware(
            labware=moved_plate,
            new_location=2,
            use_gripper=True,
            pick_up_offset={"x": 0, "y": 0, "z": 34.5}
        )

    # CHANGE TIPS NOTIFICATION
    dt = 0.1
    for _ in range(5):
        protocol.set_rail_lights(True)
        protocol.delay(seconds=1-dt)
        protocol.set_rail_lights(False)
        protocol.delay(seconds=1-dt)
        dt += 0.2
```

Example 6: Flex Cell-FREE Purification with Magnetic Beads and Liquid Handling (API 2.20)
```python
from opentrons import protocol_api

metadata = {
    'protocolName': 'Flex Cell-FREE Purification',
    'author': 'Example User',
    'description': 'Cell-FREE with magnetic bead purification'
}
requirements = {"robotType": "Flex", "apiLevel": "2.20"}

def run(protocol: protocol_api.ProtocolContext):
    # 加载模块
    heater_shaker = protocol.load_module("heaterShakerModuleV1", location="D1")
    magnetic_block = protocol.load_module("magneticBlockV1", location="C1")
    trash = protocol.load_trash_bin(location = "A3")

    # 在模块上加载实验器皿
    pcr_adapter_96 = heater_shaker.load_adapter('opentrons_96_pcr_adapter')
    pcr_plate_magnetic = magnetic_block.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt")
    pcr_plate_magnetic.set_offset(x=-1.00, y=-1.00, z=-7.10)

    # 在工作台上加载实验器皿
    tiprack_200ul_96 = protocol.load_labware("opentrons_flex_96_tiprack_200ul", location="C3")
    tiprack_200ul_96.set_offset(x=-0.00, y=0.50, z=0.00)
    tube_rack_1_5ml = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", location="B2")
    pcr_plate_96_D2 = protocol.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt", location="D2")

    # Define liquids with colors for visualization
    liquid_500mz = protocol.define_liquid(
        name='500mz',
        description='500mz liquid',
        display_color='#0000FF'  # Blue
    )

    liquid_10mz = protocol.define_liquid(
        name='10mz',
        description='10mz liquid',
        display_color='#00FF00'  # Green
    )

    liquid_0mz = protocol.define_liquid(
        name='0mz',
        description='0mz liquid',
        display_color='#FFFFFF'  # Clear
    )

    liquid_magnetic = protocol.define_liquid(
        name='magnetic',
        description='magnetic liquid',
        display_color='#FF0000'  # Red
    )

    liquid_cellfree = protocol.define_liquid(
        name='cellfree',
        description='cellfree liquid',
        display_color='#FFFF00'  # Yellow
    )

    # Load liquids into the tube rack
    tube_rack_1_5ml.wells_by_name()['A5'].load_liquid(liquid=liquid_500mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['B5'].load_liquid(liquid=liquid_500mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['C5'].load_liquid(liquid=liquid_500mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['D5'].load_liquid(liquid=liquid_500mz, volume=100)

    tube_rack_1_5ml.wells_by_name()['A4'].load_liquid(liquid=liquid_10mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['B4'].load_liquid(liquid=liquid_10mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['C4'].load_liquid(liquid=liquid_10mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['D4'].load_liquid(liquid=liquid_10mz, volume=100)

    tube_rack_1_5ml.wells_by_name()['A3'].load_liquid(liquid=liquid_0mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['B3'].load_liquid(liquid=liquid_0mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['C3'].load_liquid(liquid=liquid_0mz, volume=100)
    tube_rack_1_5ml.wells_by_name()['D3'].load_liquid(liquid=liquid_0mz, volume=100)

    tube_rack_1_5ml.wells_by_name()['A2'].load_liquid(liquid=liquid_magnetic, volume=100)
    tube_rack_1_5ml.wells_by_name()['B2'].load_liquid(liquid=liquid_magnetic, volume=100)
    tube_rack_1_5ml.wells_by_name()['C2'].load_liquid(liquid=liquid_magnetic, volume=100)
    tube_rack_1_5ml.wells_by_name()['D2'].load_liquid(liquid=liquid_magnetic, volume=100)

    tube_rack_1_5ml.wells_by_name()['A1'].load_liquid(liquid=liquid_cellfree, volume=100)
    tube_rack_1_5ml.wells_by_name()['B1'].load_liquid(liquid=liquid_cellfree, volume=100)
    tube_rack_1_5ml.wells_by_name()['C1'].load_liquid(liquid=liquid_cellfree, volume=100)
    tube_rack_1_5ml.wells_by_name()['D1'].load_liquid(liquid=liquid_cellfree, volume=100)

    # Define labware movement functions
    def move_fromMAG_to_new(labware, slot):
        protocol.move_labware(
            labware=labware,
            new_location=slot,
            use_gripper=True,
            pick_up_offset={"x": 0, "y": 0, "z": -6}, # Extra 6mm down when picking up from mag module
        )

    def move_to_new_location(labware, slot):
        protocol.move_labware(
            labware=labware,
            new_location=slot,
            use_gripper=True
        )

    # Load pipette and begin protocol
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack_200ul_96])
    pipette.pick_up_tip()
    pipette.transfer(130, tube_rack_1_5ml['A1'], pcr_plate_magnetic['A1'], mix_after=(4, 100), new_tip='never')
    pipette.drop_tip()

    # Heater-shaker operations
    heater_shaker.open_labware_latch()
    move_fromMAG_to_new(pcr_plate_magnetic, pcr_adapter_96)

    heater_shaker.close_labware_latch()
    heater_shaker.set_and_wait_for_temperature(37)
    heater_shaker.set_and_wait_for_shake_speed(rpm=700)
    protocol.delay(minutes=120)
    heater_shaker.deactivate_shaker()
    heater_shaker.deactivate_heater()

    # Magnetic bead operations
    pipette.pick_up_tip()
    pipette.transfer(50, tube_rack_1_5ml['A2'], pcr_plate_magnetic['A1'], new_tip='never')
    pipette.drop_tip()

    # Repeat heat-shake for bead binding
    heater_shaker.set_and_wait_for_temperature(37)
    heater_shaker.set_and_wait_for_shake_speed(rpm=700)
    protocol.delay(seconds=300)
    heater_shaker.deactivate_shaker()
    heater_shaker.deactivate_heater()
    heater_shaker.open_labware_latch()

    # Move to magnetic module for separation
    move_to_new_location(pcr_plate_magnetic, magnetic_block)
    protocol.delay(seconds=10)

    # Transfer supernatant
    pipette.pick_up_tip()
    pipette.transfer(180, pcr_plate_magnetic['A1'], pcr_plate_96_D2['A1'], new_tip='never')
    pipette.drop_tip()
    protocol.delay(seconds=20)

    # Wash with 0mz buffer
    pipette.pick_up_tip()
    pipette.transfer(100, tube_rack_1_5ml['A3'], pcr_plate_magnetic['A1'], mix_after=(4, 100), new_tip='never')
    pipette.transfer(100, pcr_plate_magnetic['A1'], pcr_plate_96_D2['A2'], new_tip='never')
    pipette.drop_tip()
    protocol.delay(seconds=20)

    # Wash with 10mz buffer
    pipette.pick_up_tip()
    pipette.transfer(100, tube_rack_1_5ml['A4'], pcr_plate_magnetic['A1'], mix_after=(4, 100), new_tip='never')
    pipette.transfer(100, pcr_plate_magnetic['A1'], pcr_plate_96_D2['A3'], new_tip='never')
    pipette.drop_tip()
    protocol.delay(seconds=20)

    # Final elution with 500mz buffer
    move_fromMAG_to_new(pcr_plate_magnetic, pcr_adapter_96)
    heater_shaker.close_labware_latch()
    pipette.pick_up_tip()
    pipette.transfer(50, tube_rack_1_5ml['A5'], pcr_plate_magnetic['A1'], mix_after=(4, 100), new_tip='never')
    pipette.drop_tip()

    # Final heat-shake
    heater_shaker.set_and_wait_for_temperature(37)
    heater_shaker.set_and_wait_for_shake_speed(rpm=700)
    protocol.delay(seconds=300)
    heater_shaker.deactivate_shaker()
    heater_shaker.deactivate_heater()
    heater_shaker.open_labware_latch()

    # Final magnetic separation and transfer
    move_to_new_location(pcr_plate_magnetic, magnetic_block)
    protocol.delay(seconds=20)
    pipette.pick_up_tip()
    pipette.transfer(50, pcr_plate_magnetic['A1'], pcr_plate_96_D2['A4'], new_tip='never')
    pipette.drop_tip()
```

Example 7: Flex Protein Assay with Parameter Customization (API 2.20)
```python
from opentrons import protocol_api

metadata = {
    "protocolName": "Pierce BCA Protein Assay",
    "author": "Example User",
}

requirements = {"robotType": "Flex", "apiLevel": "2.20"}

def run(ctx):
    # Define customizable parameters
    # In a real protocol, these would be set through the Opentrons App
    params = {
        "reagent_prep_on_deck": 1,      # 1=Yes, 0=No
        "dilution_on_deck": 0,          # 1=Yes, 0=No
        "heating": 1,                   # 1=Heater-shaker Module, 2=Temperature Module
        "time_incubation": 30,          # Incubation time in minutes (0-120)
        "vol_sample": 25,               # Sample volume (25 or 10 uL)
        "num_sample": 48,               # Number of samples (1-48)
        "pipet_location": 1             # 1=right, 2=left
    }

    # Extract parameters
    reagent_prep_on_deck = params["reagent_prep_on_deck"]
    dilution_on_deck = params["dilution_on_deck"]
    heating = params["heating"]
    time_incubation = params["time_incubation"]
    vol_sample = params["vol_sample"]
    num_sample = params["num_sample"]
    pipet_location = params["pipet_location"]

    # Constants and calculations
    NUM_REPLICATE = 2
    VOL_WR = 200
    DEFAULT_RATE = 700

    # Calculate sample numbers based on dilutions
    if dilution_on_deck == 0:
        num_sample_final = num_sample
    else:
        num_sample_initial = num_sample
        num_sample_final = num_sample * 4

    if num_sample_final * NUM_REPLICATE > 96 or num_sample_final == 0:
        raise Exception("Invalid sample number")

    # Calculate reagent volumes
    num_rxn = num_sample_final * NUM_REPLICATE
    num_col = int(num_rxn // 8)
    if num_rxn % 8 != 0:
        num_col = num_col + 1

    if num_col > 6:
        vol_wr_well_1 = (6 - 1) * VOL_WR * 8 + 2000
        vol_wr_well_2 = (num_col - 6 - 1) * VOL_WR * 8 + 2000
    else:
        vol_wr_well_1 = (num_col - 1) * VOL_WR * 8 + 2000
        vol_wr_well_2 = 0

    vol_a_well_1 = (vol_wr_well_1 / 51) * 50
    vol_a_well_2 = (vol_wr_well_2 / 51) * 50
    vol_b_well_1 = (vol_wr_well_1 / 51) * 1
    vol_b_well_2 = (vol_wr_well_2 / 51) * 1

    # Set pipette locations
    if pipet_location == 1:
        p1k_1_loc = "right"
        p1k_8_loc = "left"
    else:
        p1k_1_loc = "left"
        p1k_8_loc = "right"

    # Deck setup
    if heating == 1:
        hs = ctx.load_module("heaterShakerModuleV1", "D1")
        hs_adapter = hs.load_adapter("opentrons_universal_flat_adapter")
    elif heating == 2:
        temp = ctx.load_module("temperature module gen2", "D3")
        temp_adapter = temp.load_adapter("opentrons_aluminum_flat_bottom_plate")

    if reagent_prep_on_deck == 1 or dilution_on_deck == 1:
        reagent_stock_rack = ctx.load_labware(
            "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical", "A2", "REAGENTS"
        )

    wr_reservoir = ctx.load_labware("nest_12_reservoir_15ml", "B2", "WORKING REAGENT")
    sample_rack_1 = ctx.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "C1", "SAMPLES")

    if num_sample_final > 24:
        sample_rack_2 = ctx.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "B1", "SAMPLES")

    ctx.load_trash_bin("A3")

    # Load tip racks
    if dilution_on_deck == 1:
        tips_200_A1 = ctx.load_labware("opentrons_flex_96_tiprack_200ul", "A1", "P200 TIPS A1")
        # tips_200_loc = tips_200.wells()[:96] # This variable was redefined later, ensure correct one is used or remove if not needed

    tips_1000_B3 = ctx.load_labware("opentrons_flex_96_tiprack_1000ul", "B3", "P1000 TIPS B3")
    # tips_1000_loc = tips_1000.wells()[:96] # This variable was redefined later, ensure correct one is used or remove if not needed
    tips_200_C3 = ctx.load_labware("opentrons_flex_96_tiprack_200ul", "C3", "P50 TIPS C3") # Assuming P50 was a typo for P200 based on tip type
    # tips_200_loc = tips_200.wells()[:96] # This variable is being shadowed. Let's make tip rack variables unique.

    # Corrected and distinct tip rack variables:
    all_tips_200_A1 = tips_200_A1.wells()[:96] if dilution_on_deck == 1 else []
    all_tips_1000_B3 = tips_1000_B3.wells()[:96]
    all_tips_200_C3 = tips_200_C3.wells()[:96]


    # Load pipettes
    p1k_1 = ctx.load_instrument("flex_1channel_1000", p1k_1_loc, tip_racks=[tips_1000_B3]) # Assign specific tip rack
    p1k_8 = ctx.load_instrument("flex_8channel_1000", p1k_8_loc, tip_racks=[tips_1000_B3]) # Assign specific tip rack
    
    # Placeholder for P50/P200 pipette if needed for dilutions, assuming it uses one of the 200ul tip racks
    # For example, if a P50/P200 single channel is needed for dilutions:
    # p200_single = ctx.load_instrument("flex_1channel_50", "left", tip_racks=[tips_200_A1 if dilution_on_deck == 1 else tips_200_C3])


    p1k_1.flow_rate.aspirate = DEFAULT_RATE
    p1k_1.flow_rate.dispense = DEFAULT_RATE
    p1k_8.flow_rate.aspirate = DEFAULT_RATE
    p1k_8.flow_rate.dispense = DEFAULT_RATE

    # Define liquid locations
    if reagent_prep_on_deck == 1:
        reagent_a = reagent_stock_rack.wells_by_name()['A3'] # Corrected from wells()[8] assuming 50ml tubes are A3, B3, C3, D3
        reagent_b = reagent_stock_rack.wells_by_name()['A1'] # Corrected from wells()[0] assuming 15ml tubes start at A1

    if dilution_on_deck == 1:
        buffer = reagent_stock_rack.wells_by_name()['A2'] # Corrected from wells()[2] assuming 15ml tubes for buffer

    wr_1 = wr_reservoir.wells()[0]
    if num_col > 6:
        wr_2 = wr_reservoir.wells()[1]

    sample_1_wells = sample_rack_1.wells()[:num_sample if num_sample <= 24 else 24]
    if num_sample > 24:
        sample_2_wells = sample_rack_2.wells()[:num_sample-24]


    # Define liquids with colors
    if reagent_prep_on_deck == 1:
        vol_a_calc = ((num_col - 1) * VOL_WR * 8 + 3000) / 51 * 50
        vol_b_calc = ((num_col - 1) * VOL_WR * 8 + 3000) / 51 * 1
        def_a = ctx.define_liquid(name="Reagent A", description=" ", display_color="#E5E4E2")  # Gray
        reagent_a.load_liquid(liquid=def_a, volume=vol_a_calc)
        def_b = ctx.define_liquid(name="Reagent B", description=" ", display_color="#0000FF")  # Blue
        reagent_b.load_liquid(liquid=def_b, volume=vol_b_calc)
    else: # Pre-made working reagent
        if num_col > 6:
            vol_1_calc = (6 - 1) * VOL_WR * 8 + 2000
            vol_2_calc = (num_col - 6 - 1) * VOL_WR * 8 + 2000
            def_wr1 = ctx.define_liquid(name="Working Reagent 1", description=" ", display_color="#50C878")  # Green
            wr_1.load_liquid(liquid=def_wr1, volume=vol_1_calc)
            def_wr2 = ctx.define_liquid(name="Working Reagent 2", description=" ", display_color="#50C878")  # Green
            wr_2.load_liquid(liquid=def_wr2, volume=vol_2_calc)
        else:
            vol_1_calc = (num_col - 1) * VOL_WR * 8 + 2000
            def_wr1 = ctx.define_liquid(name="Working Reagent", description=" ", display_color="#50C878")  # Green
            wr_1.load_liquid(liquid=def_wr1, volume=vol_1_calc)

    # Main protocol steps would follow...
    # This part needs to be implemented based on the assay's logic:
    # 1. Reagent Preparation (if reagent_prep_on_deck == 1)
    #    - Transfer Reagent A and Reagent B to the working reagent reservoir (wr_1, wr_2)
    #    - Mix them thoroughly.
    # 2. Sample Dilution (if dilution_on_deck == 1)
    #    - Prepare dilutions of samples in a separate plate or in the sample racks.
    # 3. Transfer Samples to Working Plate
    #    - Create a new working plate (e.g., corning_96_wellplate_360ul_flat on C2 or on a module).
    #    - Transfer `vol_sample` of each sample (and replicates) to the working plate.
    # 4. Transfer Working Reagent to Working Plate
    #    - Transfer `VOL_WR` of the prepared working reagent to each well containing a sample.
    #    - Mix gently.
    # 5. Incubation
    #    - Move working plate to Heater-Shaker or Temperature Module if heating == 1 or 2.
    #    - Set temperature (e.g., 37°C) and incubate for `time_incubation` minutes.
    #    - If using Heater-Shaker, may involve shaking.
    # 6. Read Absorbance (This step is typically done off-deck)

    # Example of a final step - incubation comment (actual commands would be above)
    if heating > 0 : # Simplified check if any heating module is used
        # Actual plate movement and module commands would be here
        ctx.comment(f"Incubation for {time_incubation} minutes at specified temperature would occur here.")
        if heating == 1: # Heater-shaker
             # hs.set_temperature(37) # Example
             # ctx.delay(minutes=time_incubation)
             # hs.deactivate_heater()
             pass
        elif heating == 2: # Temperature module
             # temp.set_temperature(37) # Example
             # ctx.delay(minutes=time_incubation)
             # temp.deactivate()
             pass

    ctx.comment("Assay complete. Please measure absorbance at 562 nm on a plate reader.")
```
""" 