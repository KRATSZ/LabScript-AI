# Custom Emulsions via CSV File


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs custom emulsions via two uploaded csv files - one for the aqueous solutions (slot 10) and another for the oil solutions (slot 11). Touch tips and delays are instilled after aspirations, and blowouts are instilled after dispensing from the top of the well. One liquid solution is dispensed at a time into as many rows that are provided in the csv. If a value of 0 is passed in the csv, the pipette will skip that well. For volumes less than 300ul, the P300 single channel pipette is used, otherwise for volumes 300-1000ul, the P1000 pipette is used. All aspirations and dispenses are in order of row for all racks and plates.

![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/03f9cd/Screen+Shot+2022-10-06+at+11.01.24+AM.png)

* The csv should be formatted like so. Note that it should include the header, as well as a second row describing the initial volume in each tube in milliliters to ensure liquid height tracking, and avoid submerging the pipette plunger in solution. The aqueous and oil csv files do not necessarily need to have the same number of columns (liquid number), but they should have the same number of rows (up to 144 rows).

### Labware
* V&P Scientific 48 Well Plate 2000 µL #VP 416-ALB-48
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)


### Pipettes
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/03f9cd/deck.png)


### Protocol Steps
1. Aqueous solution is aspirated from the aqueous rack, with the volume informed by the csv.
2. Touch tip and 2 second delay.
3. Aqueous solution is dispensed from the top of the well by row into the 48 well plate.
4. Steps 1-3 repeated for the oil solution.


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
03f9cd
