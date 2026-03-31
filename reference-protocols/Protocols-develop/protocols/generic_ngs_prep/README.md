# Custom NGS Library Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Generic

## Description
This protocol performs a generic NGS Library Prep. It utilizes up to three temperature modules in Slot 1, 4 and 7 for the cooling of reagents. It also utilizes the magnetic module for bead based purification of samples.

Explanation of parameters below:
* `P20 Multichannel GEN2 Mount Position`: Choose the mount position of the P20 Multichannel GEN2 pipette. (left or right)
* `P300 Multichannel GEN2 Mount Position`: Choose the mount position of the P300 Multichannel GEN2 pipette. (left or right
* `Number of Samples`: Enter total number of samples in the protocol run. **Note: Because both pipettes are 8-channels, the number of samples should be a multiple of 8 or close if possible, otherwise it will use up additional tips for an entire column.**
* `Temperature module in slot 1` (Optional parameter) Specify which temperature module to use in slot 1 (or None). This temperature module would allow the user to control the temperature of the sample plate in part 1 of the protocol.
*  `Temperature module in slot 1` (Optional parameter) Specify which temperature module to use in slot 4 (or None). This temperature module would allow the user to control the temperature of reagent plate 1 in part 1 of the protocol, and the primer plate in part 2.
*  `Temperature module in slot 7` (Optional parameter) Specify which temperature module to use in slot 7 (or None). This temperature module would allow the user to control the temperature of reagent plate 2 in part 1 of the protocol, and the Indexing plate in part 2.
* `Sample plate` The sample plate holds DNA samples and is the site of mixing with buffers and reagents in part 1.
* `Reagent 1 plate` The reagent 1 plate holds the first mixing reagent in column 1 (e.g. a buffer or an enzyme) to be mixed with the samples
* `Reagent 2 plate` The reagent 2 plate holds the second mixing reagent in column 1 (e.g. a buffer or an enzyme) to be mixed with the samples.
* `Primer plate` Contains primers to be mixed with DNA samples in step 2
* `Reagent reservoir` The (12 well) reservoir contains paramagnetic bead solution, PCR buffer, and PCR mastermix.
* `Ethanol reservoir` Ethanol solution for washing beads, e.g. 80:20 ethanol:water. Uses 180 µL per sample
* `Number of Samples` The number of DNA samples (up to 96)
* `Temperature (deg C) for temperature module on slot x in part 1` These parameters for each of the temperature modules allow the user to set the temperatures for all/any temperature module in part 1.
* `Temperature (deg C) for temperature module on slot x in part 2` These parameters for each of the temperature modules allow the user to set the temperatures for all/any temperature module in part 2.
* `Volume of reagent 1 to add` Volume of reagent 1 to add to samples, e.g. an enzyme or a reaction buffer
* `Volume of reagent 2 to add` Volume of reagent 2 to add to samples, e.g. an enzyme or a reaction buffer
* `Ethanol wash volume` The volume of ethanol solution to use for bead washing
* `Mastermix volume` Volume of PCR mastermix for the PCR reaction in step 2, this is added to the indexing plate
* `Primer mix volume` Volume of primer mix for the PCR reaction in step 2, this is added to the indexing plate
* `Bead volume` Volume of paramagnetic bead solution to use for cleaning up the DNA from the enzymatic reaction in part 1 of the protocol
* `Elution buffer volume` The volume of elution buffer to use for eluting the DNA after the ethanol cleanup
* `Sample volume` The initial volume of DNA on the sample plate
* `DNA supernatant volume` The volume of clean DNA to be transferred from the magnetic deck plate to the indexing plate to be used in the PCR reaction

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
**Plates**
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr/)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_generic_pcr_strip_200ul/)
* [Opentrons 96 Well Aluminum Block with Bio-Rad Well Plate 200 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_biorad_wellplate_200ul)
* [Opentrons 96 Well Aluminum Block with NEST Well Plate 100 µL](https://labware.opentrons.com/opentrons_96_aluminumblock_nest_wellplate_100ul)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://labware.opentrons.com/nest_96_wellplate_100ul_pcr_full_skirt)

**Tips**
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul/)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul/)

**12 well reservoir options**
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml/)
* [USA Scientific 12 Well Reservoir 22 mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml)

**reservoir options**  
* [Agilent 1 Well Reservoir 290 mL](https://labware.opentrons.com/agilent_1_reservoir_290ml)
* [Axygen 1 Well Reservoir 90 mL](https://labware.opentrons.com/axygen_1_reservoir_90ml)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml)

**Pipettes**
* [P20 Multichannel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5978988707869)
* [P300 Multichannel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

---

### Deck Setup
**Note: The deck setup changes throughout the course of the protocol. The initial calibration layout may differ from the final setup. Please follow the initial calibration setup and any instructions during the pauses.**

Initial deck state:

![Initial deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/generic_ngs_prep/starting_deck.jpg)

**Step 1**
* Slot 1: Temperature Module slot 1 + Sample Plate
* Slot 2: Reagent reservoir (SPRI, Buffer I, Mastermix)
* Slot 3: Magnetic Module (Empty)
* Slot 4: Temperature Module slot 4 + Reagent 1 Plate
* Slot 6: 1 Well Reservoir (Ethanol)
* Slot 7: Temperature Module slot 7 + Reagent 2 plate
* Slot 8: Opentrons 200 uL Filter Tips
* Slot 9: Opentrons 200 uL Filter Tips
* Slot 10: Opentrons 20 uL Filter Tips
* Slot 11: Opentrons 20 uL Filter Tips

**Step 2**
* Slot 1: Temperature Module slot 1
* Slot 2: Reagent reservoir (SPRI, Buffer I, Mastermix)
* Slot 3: Magnetic Module + Sample plate
* Slot 4: Temperature Module slot 4 + Primers
* Slot 6: 1 Well Reservoir (Ethanol Reservoir)
* Slot 7: Temperature Module slot 7 + Indexing plate
* Slot 8: Opentrons 200 uL Filter Tips
* Slot 9: Opentrons 200 uL Filter Tips
* Slot 10: Opentrons 20 uL Filter Tips
* Slot 11: Opentrons 20 uL Filter Tips

---

### Protocol Steps
* Step 1: Transfer Reagent 1 to Samples
* Step 2: Transfer Reagent 2 to Samples
* Pause Step to Change Deck Setup and allow user to do thermal incubation
* Step 3: Add SPRI solution to Samples
* Step 4: Incubate SPRI at RT
* Step 5: Engage Magnet
* Step 6: Remove Supernatant from samples
* Step 7: Add Ethanol to samples
* Step 8: Allow ethanol to sit
* Step 9: Remove Supernatant from samples
* Step 10: Repeat Ethanol Wash
* Step 11: Remove Supernatant from samples
* Step 12: Allow beads to dry
* Step 13: Transfer elution buffer to bead samples
* Step 14: Allow the elution buffer to incubate with the beads
* Step 15: Add PCR Master Mix to indexing plate
* Step 16: Transfer Primer Mix to Indexing Plate
* Step 17: Waiting delay to concentrate the sample plate beads before supernatant transfer
* Step 18: Transfer DNA supernatant from samples to indexing plate

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
generic_ngs_prep
