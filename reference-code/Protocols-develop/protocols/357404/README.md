# Slide Sample Antibody Staining

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Microscopy Slide Antibody Staining

## Description
This protocol performs immunostaining of slides in a custom 3D printed slide block with Shandon coverplates.
Up to 7 slide blocks, each with 8 wells can be placed on the deck resulting in the ability to immunostain up to 56 slides simultaneously.

The protocol can be stopped after the addition of the block reagent if the user wants to incubate the slides overnight, and can be restarted at the next step which is the addition of the 1st antibody.

Pipette racks and reagents may have to be replaced during the run depending on the number of samples. If that happens the lights on the OT-2 will flash to indicate that the protocol requires the users attention.

Explanation of parameters below:
* `Number of slide blocks`: How many slide holding blocks there are on the deck. The maximum number that will fit on the deck are 7.
* `Number of samples in the last block`: All slide blocks except the last one are assumed to be full, however the last block may have a number of samples between 1 and 8
* `Volume in reagents containers`: How much volume (µL) there is in each reagent tube (meaning block, antibody 1, antibody 2, and nuclear counterstain tubes). It is a good idea to have some amount of excess in each tube, about 50-100 uL to account for pipetting variance.
* `Sweep dispense steps`: How many discrete step motions + dispenses to do when dispensing reagents and PBS, this is designed to replicate a sweeping motion with a manual pipette while dispensing. For example if the parameter is set to 5 the pipette will cover the length of the Shandon coverplate's mouth in 5 steps and dispense a 5th of the total dispensation volume each time.
* `Reagent tuberack`: What type of tuberack you wish to use for the reagents (block, the antibodies and the nuclear counterstain). The maximal number of tubes for any reagents is 4 (a full column, so dimension the tubes accordingly). The maximal required volume for each reagent is 4.9 mL for a full deck (7 blocks*8 samples each). This volume would fit for example in 4 1.5 mL tubes.
* `Pipette offset`: Pipetting offset in `millimeter` when dispensing, increasing this parameter will mean that the pipette will dispense at a higher height in the wells, while making it negative will lower the height of dispenses. **This parameter must be adjusted carefully so that there are no collisions between the pipette tip and the Shandon coverplates!**
* `Start protocol after 1st incubation step`: Starts the protocol at the step after the samples have already been incubated with `block` overnight.
* `Stop protocol after 1st incubation step`: The protocol stops after adding the block reagent and the user is asked to incubate the samples at 4 degrees C overnight.
* `Do a dry run?`: Skip all incubation pauses and return tips to their racks after use.
* `Time per block (s)`: The amount of time it takes to transfer reagent per block. The user must measure the time it takes for the reagent dispensation steps to finish for each block using a stopwatch, for example by putting the maximum of of seven blocks on the deck, running the protocol and then calculating the average block time by dividing by seven. This time is used to subtract from the total incubation time such that each sample will have an hour of incubation instead of 1 hour plus the time it takes to transfer reagent or PBS.
* `Multi-dispense reagents?`: Whether to aspirate a 100 uL of reagent at a time and dispense it in the next well or aspirate 900 uL and go from well to well dispensing 100 uL each before picking up more reagent.
* `Reuse reagent tips?`: Use the same tip for each individual reagent.
* `Reuse PBS wash tips?`: Use one tip to do one wash with PBS
* `Use temperature module?`: Whether to use a temperature module to chill the reagents in the tuberack, or put the tuberack directly on the slot.
* `P1000 slot`: Which mount to use for the P1000 single GEN2 pipette
* `Reagent tuberack`: Which reagent tuberack you want to use in the protocol
* `Well edge offset (mm)`: The offset from the well's edge when performing the dispensing while moving action. The pipette will start dispensing on one side of the well minus the offset and will travel to the other side of the well minus the same offset.
* `Use a custom slide block`: Setting this parameter to Yes means that the protocol will try to load an alternative definition for the slide block. See `Custom labware loadName` parameter below.
* `Custom labware loadName`: Put the labware load name of the alternative slide block labware definition you wish to use. To find the loadName: Open your labware_definition.json file, look for the section "parameters"
e.g.
```
"parameters": {
		"format": "irregular",
		"quirks": [],
		"isTiprack": false,
		"isMagneticModuleCompatible": false,
		"loadName": "customslideblockv2_8_wellplate"
```
and copy the value of loadName (without the quotation marks). paste that value into this parameter field, i.e. in this case that would be: `customslideblockv2_8_wellplate`

Remember to load the labware into the Opentrons app before running your protocol

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) (optional)

### Labware
* [Opentrons tuberacks](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons tubes & vials](https://shop.opentrons.com/consumables/)
* [Agilent 1-Well Reservoir 290 mL](https://labware.opentrons.com/agilent_1_reservoir_290ml)
* [1000 uL tipracks](https://shop.opentrons.com/opentrons-1000-l-tips/)
* [Opentrons aluminum block set](https://shop.opentrons.com/aluminum-block-set/) (optional)
* [Agilent 1-Well Reservoir 290 mL](https://labware.opentrons.com/agilent_1_reservoir_290ml)
* Custom 3D printed block for holding Shandon coverplates + slides.

### Pipettes
* [P1000 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
290 mL reservoir on slot 2:
* Phosphate buffered saline (PBS)

Reagent tuberack on slot 3:
* Block
* Antibody 1
* Antibody 2
* Nuclear counterstain

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/357404/deck.jpg)

### Reagent Setup
* Reservoir 2: slot 3
![Reagent reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/357404/reagent_tuberack.jpg)

---

### Protocol Steps
1. The temperature module is set to 4 degrees C.
2. 100 µL of Block is added to the samples wells, unless the protocol is set to skip the 1st reagent addition step.
3. The protocol incubates for 1 hour (with the time it takes to add the Block reagent subtracted)
4. 100 µL Antibody 1 is added (This may be the 1st reagent added in the protocol if the user chooses to start with samples that have been incubated overnight with Block)
5. The protocol incubates for 1 hour
6. The slides are washed with 4 mL PBS each
7. 100 µL of Antibody 2 is added to each slide
8. The protocol incubates for 1 hour
9.  The slides are washed with 4 mL PBS each
10. 100 µL of nuclear counterstain is added to each slide
11. The protocol pauses for 5 minutes
12. The slides are washed with 4 mL PBS each

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
357404
