# DMSO and Compound Stock Solution Addition - Part 1


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Serial Dilution


## Description
This protocol serially diluted compound stock with DMSO. There is an optional predilution step in this protocol. For detailed protocol steps, please see below. Slots 6, 7, 8, 9 are nest deep well plates, and slots 2, 4, 5, 10, 11 are NEST PCR plates.


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Deepwell Plate 2mL #503001](http://www.cell-nest.com/page94?product_id=101&_l=en)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/056f47/Screen+Shot+2023-04-24+at+3.41.25+PM.png)



### Protocol Steps
1. Transfer 2.4 uL from DMSO reservoir to columns 2-12 in Dilution Plates DMSO 1-1+2-1 , keep tips (variable step)
2. Transfer 2.4 uL from DMSO reservoir to all wells in Dilution Plates DMSO 1-2+2-2, discard tips (variable step)
Optional predilution step, dilute compounds in columns 1 and/or 2 with DMSO by a specified factor into columns 11/12 for a total volume of 20 uL (variable step)
3. Transfer 7.2 uL from column 1 of Compound Stocks to column 1 or column 11 if predilution takes place of Dilution Plate DMSO 1-1, keep tips
4. Transfer 4.8 uL from column 1 of Dilution plate DMSO 1-1 to column 2, mixing after. Repeat process, transferring from 2-3 3-4 4-5 etc mixing after each time, until transferring from 10-11 (skip 12), keep tips
5. Transfer 4.8 uL from column 11 of Dilution plate DMSO 1-1 to column 1 of Dilution Plate DMSO 1-2, mixing after, keep tips.
6. Transfer 4.8 uL from column 1 of Dilution plate DMSO 1-2 to column 2, mixing after. Repeat process, transferring from 2-3 3-4 4-5 etc mixing after each time, until transferring from 10-11 (skip 12), discard tips
7. Repeat steps 4-8 for column 2/12 of compound stocks and Dilution Plate DMSO 2-1+2-2
8. Manual tip box replacement.
9. Transfer 2.4 uL from each column of Dilution Plate DMSO 1-1 to the same column of Media Plate 1-1, discarding tips after each transfer.
10. Manual tip box replacement.
11. Repeat steps 10-11 for Dilution Plates DMSO/Media Plates 1-2, 2-1, 2-2


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
04318b