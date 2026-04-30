# PCR Prep


### Author
[Opentrons](https://opentrons.com/)


## Categories
* PCR
	* PCR Prep


## Description
This protocol creates mastermix according to the number of samples, then distributes the resultant mastermix to a final pcr plate along with sample. For detailed protocol steps, please see below.


### Labware
* Pcr Plate 96 Well Plate 200 µL
* Opentrons 24 Tube Rack with starstedt 2 mL
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04711e/Screen+Shot+2024-02-15+at+12.10.56+PM.png)


### Protocol Steps
1. Mastermix is made in empty tube in tuberack according to the number of samples.
2. Mastermix is distributed to the first column of the middle plate on slot 2 (single channel pipette).
3. Mastermix is distributed to final plate (multi-channel pipette).
4. Sample is added to final plate.


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
04711e
