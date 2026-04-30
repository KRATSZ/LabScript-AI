# QIAseq FastSelect Normalization


### Author
[Opentrons](https://opentrons.com/)




## Categories
* SAMPLE PREP
	* Normalization


## Description
With this Protocol you can Normalize RNA samples using RNA Concentration, Goal Concentration, Total Volume. This Normalization is the normalization protocol to preceed the QIAseq FastSelect and QIAsec FastSelect 5s , 16S and 23S.  


### Modules
* [Opentrons Temperature Module (GEN2)](https://shop.opentrons.com/temperature-module-gen2/)


### Labware
* Perkin Elmer 12 Reservoir 21000 µL
* Applied Biosystems Enduraplate 96 Aluminum Block 220 µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Well Aluminum Block with Bio-Rad Well Plate 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0b97ae/part+1/Image+8-11-23+at+1.10+PM.jpg)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0b97ae/part+1/Image+8-11-23+at+2.21+PM+(2).jpg)


### Protocol Steps
1. Load CSV into the slot above, With the Columns being RNA Concentration, Goal Concentration and Total Goal Volume
2. The Source Plate will be loaded onto the Temperature module on slot 10
3. The Dilution Plate will be loaded onto the Temperature module on slot 7


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
0b97ae
