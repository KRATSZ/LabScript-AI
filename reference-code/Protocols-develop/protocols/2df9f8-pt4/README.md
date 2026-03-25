# Pooling Deep Well Plates by Column

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol pools up to 5 plates by column to a final destination plate. 100ul of sample is taken from each column of each specified plate and dispensed into the final deep well plate on slot 11.

Explanation of complex parameters below:
* `Number of plates`: Specify the number of agar plates (1-5) to fill for this run.
* `Number of columns in each plate`: Specify the number of columns (1-12) in each agar plate to fill.
* `P300 Multi-Channel Pipette Mount`: Specify which mount (left or right) to host the P300 multi-channel pipette.

---

### Labware
* [NEST 2mL 96 well deep well plate](nest_96_wellplate_2ml_deep)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2df9f8/Screen+Shot+2021-10-04+at+5.29.56+PM.png)

---

### Protocol Steps
1. 100ul of sample is taken from sample column 1 of plate 1 and dispensed into column 1 of the pool plate.
2. Change tip
3. Steps 1-2 is repeated for all columns of plate 1.
4. Steps 1-3 are repeated for all plates that the user specifies.

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
2df9f8-pt4
