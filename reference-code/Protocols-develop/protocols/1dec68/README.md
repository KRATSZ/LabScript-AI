# Covid Sample Prep with Custom 96 Tube Rack

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 96 well plate with 50ul of sample from a custom 96 tube tube rack. Samples are drawn from the tube rack by column (A1, B1, C1...H1, A2...etc.) and dispensed to the well plate in the same order. The pipette will dispense, and then blowout after dispensing into the well plate. The user has the ability to manipulate the number of samples per run. 

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples (1-96) for this run.
* `P300 Single-Channel Mount`: Specify which mount (left or right) to host the P300-single channel pipette.

---

### Labware
* Bio-Rad 50ul 96 Well Plate
* (Opentrons 300uL tips)[https://shop.opentrons.com/universal-filter-tips/]
* Custom 96 tube rack

### Pipettes
* [P300 Single-Channel Pipette](https://shop.opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1dec68/Screen+Shot+2022-02-22+at+11.29.54+AM.png)

---

### Protocol Steps
1. Mount the needle on position 10.
2. Extract 50µl of sample (contain 5ml/sample).
3. Pipette 50µl to standard BIORAD 96 plate (with 50µl).
4. Discard the needle on trash.

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
1dec68
