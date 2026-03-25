# Custom NGS Library Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Custom

## Description
This protocol performs a custom NGS Library Prep. It utilizes two temperature modules in Slot 1 and Slot 3 for the cooling of reagents. It also utilizes the magnetic module for bead based purification of samples.

Explanation of complex parameters below:
* `P20 Multichannel GEN2 Mount Position`: Choose the mount position of the P20 Multichannel GEN2 pipette.
* `P300 Multichannel GEN2 Mount Position`: Choose the mount position of the P300 Multichannel GEN2 pipette.
* `Number of Samples`: Enter total number of samples in the protocol run. **Note: Because both pipettes are 8-channels, the number of samples should be a multiple of 8, otherwise it will use up additional tips for an entire column.**

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr/)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_generic_pcr_strip_200ul/)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul/)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul/)
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml/)

### Pipettes
* [P20 Multichannel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5978988707869)
* [P300 Multichannel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

---

### Deck Setup
**Note: The deck setup changes throughout the course of the protocol. The initial calibration layout may differ from the final setup. Please follow the initial calibration setup and any instructions during the pauses.**

* Slot 1: Temperature Module A + Bio Rad Plate (Sample Plate)
* Slot 2: Bio Rad Plate (Reagent #2 Plate)
* Slot 3: Temperature Module B + Bio Rad Plate (Reagent #1 Plate)
* Slot 4: Magnetic Module
* Slot 6: NEST 1 Well Reservoir (Ethanol Reservoir)
* Slot 7: Opentrons 200 uL Filter Tips
* Slot 8: Opentrons 200 uL Filter Tips
* Slot 10: Opentrons 20 uL Filter Tips
* Slot 11: Opentrons 20 uL Filter Tips

---

### Protocol Steps
* Step 1: Transfer Reagent 1 to Samples
* Step 2: Transfer Reagent 2 to Samples
* Pause Step to Change Deck Setup
* Step 3: Add SPRI solution to Samples
* Step 4: Incubate SPRI at RT
* Step 5: Engage Magnet
* Step 6: Remove Supernatant from samples
* Step 7: Add Ethanol to sammples
* Step 8: Allow ethanol to sit
* Step 9: Remove Supernatant from samples
* Step 10: Repeat Ethanol Wash
* Step 11: Remove Supernatant from samples
* Step 12: Allow beads to dry
* Step 13: Transfer Buffer 1 to samples
* Step 14: Allow beads to incubate
* Step 15: Add PCR Master Mix to indexing plate
* Step 16: Transfer Primer Mix to Indexing Plate
* Step 17: Concentrate sample plate beads
* Step 18: Transfer supernatant from samples to indexing plate

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6cd9d6