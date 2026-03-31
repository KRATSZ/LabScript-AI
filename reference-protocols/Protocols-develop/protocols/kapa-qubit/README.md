# Kapa Qubit


### Author
[Opentrons](https://opentrons.com/)


## Categories
* Broad Category
	* Specific Category


## Description
This protocol prepares a 96 Agilent plate for qubit. For detailed protocol steps, please see below. 


### Labware
* Agilent 96 Well Plate 270 µL
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/kapa-qubit/QUBIT.png)



### Protocol Steps
1. Transfer 190ul of buffer to column 1, 2 of destination plate
2. Transfer 198ul of buffer to eventual sample columns of destination plate
3. 10ul of standard 1 to column 1, 10ul of standard 2 to column 2 of destination plate
4. 2ul from samples to sample columns of destination plate



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
kapa-qubit
