# Nanopore Aliquoting

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Nanopore


## Description
This protocol pools 1-6 destination plates from all columns to the first 4 wells in column 1 for each respective plate. Destination plates should loaded onto the deck in order of lowest to highest, depending on the number of plates selected (up to 6). That is, for two plates, load the plates in slots 4 and 5. For detailed protocol steps, see below.


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
2. Aspirate 20ul from column 12 to column 7 on plate 1.
3. Dispense all aspirations into column 1 of the respective plate.
4. Aspirate 20ul from column 6 to column 2 on plate 1.
5. Dispense all aspirations into column 1 of the respective plate.
6. Move wells E1-H1 in column 1 to A1-D1 in column 1.



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
