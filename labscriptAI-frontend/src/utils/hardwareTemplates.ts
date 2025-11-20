// /src/utils/hardwareTemplates.ts

export const hardwareTemplates: Record<string, string> = {
  'Flex': `// Default configuration for Opentrons Flex
Robot Model: Flex
API Version: 2.19
Left Pipette: flex_1channel_1000
Right Pipette: flex_8channel_1000
Use Gripper: True
Deck Layout:
  A1: opentrons_flex_96_tiprack_1000ul
  B2: corning_96_wellplate_360ul_flat
  C1: nest_12_reservoir_15ml
  D1: opentrons_96_pcr_adapter`,
  'OT-2': `// Default configuration for Opentrons OT-2
Robot Model: OT-2
API Version: 2.19
Left Pipette: p300_single_gen2
Right Pipette: null
Deck Layout:
  '1': opentrons_96_tiprack_300ul
  '2': corning_96_wellplate_360ul_flat
  '3': nest_12_reservoir_22ml`
}; 