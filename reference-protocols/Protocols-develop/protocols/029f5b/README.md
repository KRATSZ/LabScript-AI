# FBelz Protocol


### Author
[Opentrons](https://opentrons.com/)




## Categories
* SAMPLE PREP
	* Custom Sample Transfer


## Description
With this Protocol you can add lysis buffer, chloroform, and wash with Isopropanol to samples. This protocol is set up to do 384 samples across 4 different plates.  


### Modules
N/A


### Labware
* Axygen 96well minitube system corning 96 wellplate 1320µL
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons Nest 1 well Reservoir 290 mL]


### Pipettes
* [Opentrons P300 multi Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/029f5b/Layout.jpg)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/029f5b/Liquids.jpg)


### Protocol Steps
1. Load tubes and reservoirs
2. The reagent reservoir will be on slot 6
3. The cleaning reservoir will be on slot 9


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
029f5b
