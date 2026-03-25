# Dispensing Diluted Phage to Agar Plates

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol dispenses diluted phage by column in a source 360ul corning plate to all specified agar plates. The tips are to not touch the agar medium but instead dispense right above it, saving up to 5 times the number of tips per run. Column 1 of the source plate is dispensed into into column 1 of all agar plates in a multi-dispense fashion to additionally save time.

Explanation of complex parameters below:
* `Number of plates`: Specify the number of agar plates (1-5) to fill for this run.
* `Number of columns in each plate`: Specify the number of columns (1-12) in each agar plate to fill.
* `Number of rows in each plate`: Specify the number of rows (1-8) in each agar plate to fill.
* `P20 Multi-Channel Pipette Mount`: Specify which mount (left or right) to host the P20 multi-channel pipette.

---

### Labware
* [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* Custom Agar Plates

### Pipettes
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/659888/Screen+Shot+2021-10-11+at+4.52.16+PM.png)

---

### Protocol Steps
1. The P20 multi-channel pipette picks up tips equal to the number of rows specified by the user.
2. The P20 aspirates 2.5ul*(number of plates) of diluted phage in column 1 of the Corning 360ul plate.
3. The P20 dispenses into column 1 of all of the agar plates up to the number of plates specified without touching the medium in each plate.
4. Steps 1-3 are repeated up to the number of columns specified by the user.

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
659888
