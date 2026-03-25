# DMSO and Compound Stock Solution Addition - Part 2


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Serial Dilution


## Description
This protocol serially diluted compound stock with DMSO. For detailed protocol steps, please see below. Note: if n < 15, use NEST PCR plates, and if n > 15, use deep well plates. 


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* Opentrons 96 Filter Tip Rack 20 µL
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/056f47/Screen+Shot+2023-04-24+at+3.42.36+PM.png)



### Protocol Steps
1. Transfer 2.4 uL * n from DMSO reservoir to columns 2-12 in Dilution Plates DMSO 1-1, keep tips
2. Transfer 2.4 uL * n from DMSO reservoir to all wells in Dilution Plates DMSO 1-2, discard tips
3. Transfer 7.2 uL * n from column 1 of Compound Stocks to column 1 of Dilution Plate DMSO 1-1, keep tips
4. Transfer 4.8 uL * n from column 1 of Dilution plate DMSO 1-1 to column 2, mixing after. Repeat process, transferring from 2-3 3-4 4-5 etc mixing after each time, until transferring from 10-11 (skip 12), keep tips
5. Transfer 4.8 uL * n from column 11 of Dilution plate DMSO 1-1 to column 1 of Dilution Plate DMSO 1-2, mixing after, keep tips.
6. Transfer 4.8 uL * n  from column 1 of Dilution plate DMSO 1-2 to column 2, mixing after. Repeat process, transferring from 2-3 3-4 4-5 etc mixing after each time, until transferring from 10-11 (skip 12), discard tips



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
056f47
