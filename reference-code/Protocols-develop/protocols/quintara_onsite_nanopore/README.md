# Nanopore Aliquoting

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Nanopore


## Description
This protocol preps 1-7 destination plates from one source barcode plate. Destination plates should loaded onto the deck in order of lowest to highest, depending on the number of plates selected (up to 7). For detailed protocol steps, see below.


### Labware
* Barcode 96 Well Plate 200 µL
* Combo 96 Well Plate Black Label on Nest Plate 300µL
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/quintara-onsite/quintara_nanopore/deck.png)



### Protocol Steps
1. Pick up tips.
2. Aspirate 8.5ul of water and dispense into A1 of source barcode plate.
3. Mix 3 times at 14ul.
4. 2ul single aspiration single dispense from A1 of source plate to A1 of destination plate(s), up to the number of plates specified.
5. Drop tip.
6. Repeat 1-5 for all columns in source plate (column to column transfer).


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
quintara_onsite_nanopore
