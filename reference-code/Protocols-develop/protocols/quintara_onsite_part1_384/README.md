# 384 Plate to 96 Plate


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol preps a 96 plate from a 384 source plate.


### Labware
* Quintara Vertical Plate 192 Wells
* Quintara 12 Reservoir 15000 µL
* Double Pcr 96 Well Plate 300 µL
* Appliedbiosystem 384 Well Plate 40 µL
* Quintara 96 Well Plate 300 µL
* Quintara Vertical Plate 192 Wells
* Deepwell 96 Well Plate 2000 µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara-onsite/pt1_384/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara_onsite_part1_384/reagents.png)


### Protocol Steps
1. 20, 2, 2, and 20ul are transferred from A1, A3, A5, A7 of the 384 plate to column 1 of the 96 plate.
2. Same volumes are transferred from A9, A11, A13, and A15 to column 2 of the 96 plate.
3. Steps 1 and 2 are repeated until the end of the plate is reached for that row to subsequent destination columns.
4. Steps 1, 2, and 3 are repeated for start wells A2, B1, and B2. 


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
quintara_onsite_part1_384
