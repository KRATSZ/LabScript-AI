# Spotsee Well Distribution Protocol


### Author
[Opentrons](https://opentrons.com/)


## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol will add a specified amount of liquid to determined wells in a custom 80 well plate. If the volume is less than 20, the pipette selected will be a P20 single-channel pipette, otherwise, if the volume is greater than 20ul, then the pipette selected will be a P300 single-channel pipette. Please match the correct pipette with the tips loaded. 


### Labware
* Custom 80 Well Plate
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/spotsee/Screen+Shot+2024-02-09+at+1.06.24+PM.png)



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
spotsee
