# Reagent Addition

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Reagent Addition

## Description
This is a specialized reagent addition to add reagent from vials in a Cytiva well plate to a 96 well plate which are then transferred to a 384 well plate. The vials and transfer volumes are specified via a CSV file. The tips are picked up in a non-standard manner with a single tip picked up from the bottom of a specified column continuing up and to the left with each new tip pick-up. E.g. Column 11 is specified, first tip picked up will be H11, then G11, F11,.....H10, G10, etc. These single tips are used to add from the vials to the 96 well plate. The columns of the 96 well plate will then have a specified amount of each column added to the 384 well plate, reusing tips as much as possible. Transfer volumes from the vials to the 96 well plate, transfer volumes from the 96 well plate to the 384 well plate, and which vials will be used is specified by uploading a CSV. The specific format can be found in this [example CSV located here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/059126/example_trans.csv)

Explanation of complex parameters below:
* `Number of Columns in 384 Well Plate`: How many columns will be in the 384 well plate starting from the left side
* `Starting Tip Column (1-12)`: Which tip will be picked up first. Number corresponds to column from left to right. Bottom tip will be picked up first in each column.
* `P20 Multi GEN2 Mount`: Which mount the P20 multi-channel is connected to. The P300 will be connected to the opposite mount.
* `Transfer .CSV File`: Upload the CSV file with vial list and transfer volumes.

---

### Labware
* Greiner 96 Well Plate 340uL
* Greiner 384 Well Plate 50uL
* Cytive 24 Well Plate 2000uL used as Vial Holder

### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P20 8 Channel Electronic Pipette (GEN20)](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
* Starting Deck Setup for 2 Reagent Vials:
![deck_setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/059126/deck_setup.png)

---

### Protocol Steps
1. Tips are picked up by the P300 starting from the front of the specified column of the tip rack. They will be picked up column-wise then row-wise
2. X uL is aspirated from the first vial in the 24 well holder A1 and added to each well in the first column
3. Repeat step 2 for each vial specified with their own specified volume in the CSV (up to 12, one for each column)
4. A set volume of each column in the 96 well plate is added with the P20 multichannel to each sample in the 384 well plate. The volume is set for each reagent in the CSV. The number of columns in the 384 well plate is specified in the user-defined variables

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
059126
