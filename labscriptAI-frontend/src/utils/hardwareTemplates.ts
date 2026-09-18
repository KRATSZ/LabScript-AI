// /src/utils/hardwareTemplates.ts

export const hardwareTemplates: Record<string, string> = {
  'Flex': `// Default configuration for Opentrons Flex
Robot Model: Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: flex_8channel_1000
Use Gripper: True
Deck Layout:
  A1: opentrons_flex_96_tiprack_1000ul (1000 µL Flex tips; type: tipRack)
  A3: trash_bin (Flex trash bin; type: trash)
  B2: corning_96_wellplate_360ul_flat (sample/reaction plate; type: plate)
  C1: nest_12_reservoir_15ml (reagent reservoir; type: reservoir)`,
  'OT-2': `// Default configuration for Opentrons OT-2
Robot Model: OT-2
API Version: 2.19
Left Pipette: p300_single_gen2
Right Pipette: null
Use Gripper: False
Deck Layout:
  '1': opentrons_96_tiprack_300ul (300 µL tips; type: tipRack)
  '2': corning_96_wellplate_360ul_flat (sample/reaction plate; type: plate)
  '3': nest_12_reservoir_15ml (reagent reservoir; type: reservoir)
  '12': fixed_trash (built-in OT-2 fixed trash; type: fixedTrash)`
}; 
