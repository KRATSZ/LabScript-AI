# Reformatting with Custom Tube Rack


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol reformats tubes from up to 4 custom tube racks to a 96 deepwell plate. The user has the option to dispense 25ul or 50ul into the deepwell plate. The sample input starts at A11 of the deepwell plate, moving by row.


### Labware
* Custom 24 Tube Rack
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/079db2/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/079db2/reagents.png)


### Protocol Steps
1. Aspirate 25ul or 50ul from the tube rack to the well plate (start at A11)
2. Grab new tip
3. Repeat up to the number of samples specified, moving by row


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
079db2
