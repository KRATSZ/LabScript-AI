# Reagent Preparation for Kingfisher Extraction


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol prepares deepwell plates for extraction. In the case that the protocol runs out of tips, it will automatically pause to prompt the user to refill tips.


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 1 Well Reservoir 195 mL #360103](http://www.cell-nest.com/page94?_l=en&product_id=102)
* Deepwell Plates
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/g42lab/Screen+Shot+2022-12-14+at+8.23.10+AM.png)

### Reagents
* The viral binding solution in the 12 well reservoir on slot 1 has a variable number of wells. One column of the reservoir accommodates 3 columns of sample (24 or less samples). For say, 20 samples, the reagent should just be placed in column 1 of the reservoir + overage. For say, 25 samples, then the total volume (550ul * 25 + overage) should be split equally between columns 1 and 2. For 96 samples, the volume + overage should be split equally over all 4 wells of the reservoir. 



### Protocol Steps
1. Place the 5 reservoirs and prelabelled 96 Well plates inside the Opentron.
2. Opentron robot to add, 1ml of 80% Ethanol from the reservoir into each well of the 96 well plate labelled, 80% Ethanol (do this for both 96 well plates labelled 80% Ethanol).
3. Opentron robot to add, 1ml of wash buffer from the reservoir into each well of the 96 well plate labelled, wash buffer (do this for both 96 well plates labelled Wash buffer).
4. Opentron robot to add, 550µl of viral binding solution and 50µl of binding bead in each well of the Sample plate.
5. Opentron robot to add 50µl of Elution buffer into each well of the 96 well plate labelled, Elution.


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
g42lab
