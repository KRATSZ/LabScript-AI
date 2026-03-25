# Adding Transfection and Sample to Plate


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol will transfer scattered sample tubes to a specified destination plate according to a csv. The csv header should read `sample well, sample slot, destination well`. Include the header in the csv and specify the volumes below. THe protocol will automatically pause if the user runs out of tips, rprompting the user to replace tips. A P20 or P300 pipette is specified depending on the volume selected by the user. Liquid height tracking is performed on the 50mL tube so that the pipette does not submerge.


### Labware
* Thermofisher 96 Well Plate 1400 µL
* Thermofisher 96 Well Plate 500 µL
* Corning 96 Well Plate 340 µL
* [Opentrons 10 Tube Rack with Falcon 4x50 mL, 6x15 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* Opentrons 96 Filter Tip Rack 200 µL
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0c24ca/deck.png)


### Protocol Steps
1. Add samples to plate according to csv
2. If transfection mix not selected, protocol will end
3. If transfection mix is selected, transfection mix will be added to plate depending on user-specified volume


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
0c24ca
