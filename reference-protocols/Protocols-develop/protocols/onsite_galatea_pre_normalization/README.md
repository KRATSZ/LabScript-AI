# Pre Normalization Prep


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
The csv should include a header in row 1. Source/destination well should be in column 1. Qubit reading should be in column 3. The transfer volume is determined by the Qubit reading. 


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_galatea/magbind/prenorm.png)



### Protocol Steps
1. Water added to final plate depending on csv
2. DNA added to final plate depending on csv


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
onsite_galatea_pre_normalization
