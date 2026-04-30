# NEBNext Ultra II Directional RNA Library Prep Kit for Illumina Part 4: Second cDNA Strand Synthesis


### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* NEBNext® Ultra™ II Directional RNA Library Prep


## Description
This protocol is part 4 of a 10 part series. Please look at deck map and liquid legend below. This protocol adds the required reagents for the cDNA second strand synthesis


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* Thermo Fisher 96 Well Plate 200 µL #AB-3396
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* Opentrons 96 Filter Tip Rack 200 µL
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00f7b1/Part+4/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00f7b1/Part+4/reagents.png)


### Protocol Steps
0. Temperature module cools down to 4 C (this can be done manually prior to protocol start)
1. 8 uL of reaction buffer is added from the temperature module in slot 3, column 1 to all samples
2. 4 uL of enzyme mix is added from the temperature module in slot 3, column 3 to all samples then mixed to combine
3. 48 ul of nuclease free water is added to each sample from slot 4, column 12 then mixed
4. Protocol is complete, OT-2 will flash to alert user


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
00f7b1_part3
