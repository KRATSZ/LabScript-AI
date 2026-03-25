# QIAseq FastSelect Extraction


### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS LIBRARY PREP
	* QIASeq FastSelect


## Description
This is Part 3 to the QIAseq FastSelect 5s, 16s, 23s Protocol. This protocol is used to perform the addition of samples with mastermix into a plate.
Part 1 to this protocol is the normalization of samples.
Part 2 to this protocol is the Fragementation.

Links:
* [Part 1: Sample Normalization](http://protocols.opentrons.com/protocol/0b97ae)
* [Part 2: QIAseq FastSelect 5s, 16s, 23s Fragmentation](http://protocols.opentrons.com/protocol/0b97ae-protocol-2B)
* [Part 3: QIAseq FastSelect 5s, 16s, 23s Extraction](http://protocols.opentrons.com/protocol/0b97ae-protocol-3B)


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* Perkin Elmer 12 Reservoir 21000 µL
* Applied Biosystems Enduraplate 96 Aluminum Block 220 µL
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* Opentrons 96 Filter Tip Rack 20 µL
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Well Aluminum Block with Bio-Rad Well Plate 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0b97ae/deck.jpg)
Water Reservoir (slot 2):
	Column 1: Nuclease Free Water
	Column 2: Binding Buffer
	Column 3 & 4: Ethanol
	Column 10, 11 & 12: Empty for Supernatent Removal
Diluted RNA Plate (slot 7 Temperature Module):
	RNA Samples Starting Plate
Reagent Plate (Slot 10):
	Column 1: MasterMix
	Column 2: Magentic Beads

### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0b97ae/reagents.jpg)


### Protocol Steps
1. Before this protocol the RNA plate should have went through the thermocycler according to FastSelect 5s/16s/23s, Table 3 and placed on a back on the temperature deck on slot 7.
2. The Reagent plate will be placed on the temperature module on slot 10, which will contain MasterMix in column 1 and magentic beads in column 2.
3. The reservoir will be placed on slot 2, which will contain Nucleas Free Water in well 1, Binding Buffer in well 2, and Ethanol in wells 3 and 4. Wells 10, 11 and 12 will be used for supernatent removal.



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
0b97ae-protocol-3B
