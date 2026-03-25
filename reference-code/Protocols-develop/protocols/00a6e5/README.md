# LCMS Urine Extraction

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 96 well plate for an LCMS extraction. The 96 well plate is loaded with negative urine samples. Reagents include enzyme, buffer, water, and spike INSTD. All transfers in the 96 well plate are by column. No mix steps are included and a 30 minute pause is included after water is added to the plate.

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples (1-96) for this protocol.
* `P300 Mount`: Specify which mount (left or right) to host the P300 single-channel pipette.
* `Aspiration height`: Specify the aspiration height for this run. A value of 1mm is the default from the bottom of the well. 
* `P1000 Mount`: Specify which mount (left or right) to host the P1000 single-channel pipette.



---

### Labware
* [Opentrons 4-in-1 tube rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Opentrons 1000ul tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 300ul Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs)
* Agilent 1 Well Reservoir, 290mL
* Custom 96 well plate

### Pipettes
* [Opentrons P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

---

### Deck Setup


### Reagent Setup

---

### Protocol Steps
1. Add 60 microliters of Enzyme to all wells
2. Add 340 microliters of Buffer to all wells
3. Add 300 microliters of Negative Urine to A1 (blank)
4. Add 270 Microliters of Negative Urine to A2-A8 (cals)
5. Add 20 Microliters of Spike INSTD to all wells
6. Add 30 microliters of Water to all wells
7. Pause... (30 mins)
8. Add 700 microliters of Methanol to all wells

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
00a6e5
