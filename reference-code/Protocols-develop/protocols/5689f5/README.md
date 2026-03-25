# NGS Clean Up


### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Clean Up


## Description
This protocol performs an NGS clean up protocol for up to 96 samples. The user is prompted to manually centrifuge the plate and replace on the magnetic module after 2x ethanol washes.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5689f5/deck.png)  
* green on magnetic plate (slot 4): starting samples
* blue on reagent plate (slot 2, column 1): DNA binding buffer
* pink on reagent plate (slot 2, column 2): Ampure beads
* orange on reagent plate (slot 2, column 3): elution buffer
* purple on reagent reservoir (slot 5, column 1): 80% ethanol
* dark blue on reagent reservoir (slot 5, column 12): waste (loaded empty)


### Protocol Steps
1. Add 5μL DNA binding buffer to each well, mix, and incubate the solution 5 minutes at room temperature.
2. Add 8μL Ampure beads to each well, mix, and incubate the solution for 5 minutes at room temperature.
3. Engage magnetic module and separate beads for 5 minutes.
4. Remove the resulting supernatant.
5. Wash 2x with 50μL of 80% ethanol without mixing.
6. Manually centrifuge the plate and replace the plate on the magnetic module.
7. Remove residual supernatant with P20 pipette.
8. Elute the beads in 7.6μL of elution buffer, mix, and incubate the solution three minutes at room temperature.
9. Engage magnetic module and separate beads for 3 minutes.
10. Transfer 6.6μL of elution to new plate.

### Process
1. Download your protocol and unzip if needed.
2. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
5689f5
