# Plasma Spike w/Optional Serial Dilution


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Serial Dilution and Screening


## Description
This protocol adds a serially diluted stock solution to 12 plasma filled vials. The serial dilution can be toggled on and off in the variables. This protocol also predicts diluent and plasma height based on known labware dimensions. The initial liquid level needs to be specified for this to be accurate.


### Labware
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00222e/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/00222e/reagents.png)


### Protocol Steps
0. Steps 1-4 only are performed if serial dilution is selected in the variable feeds
1. Diluent is added to tubes 2-12 (rows A and B) in the 24 tube rack
2. 980 uL of diluent is added to tube A1 in the 24 tube rack, mixed well
3. The protocol is paused to allow a user to add 20 uL of stock solution to tube A1 in the 24 tube rack
4. A serial dilution is performed from tube 1-12 (rows A and B) by moving 20 uL from tube A to tube A+1
5. 100 uL plasma is added to tubes 13-24 (rows C and D)
6. 10 uL from tube A1 is added to C1, this is repeated for all of rows A and B



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
00222e
