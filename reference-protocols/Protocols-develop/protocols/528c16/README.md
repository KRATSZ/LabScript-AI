# Bioanalysis with CSV input

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps 1.5mL and 2mL tubes from stock solutions including but not limited to acetonitrile, water, and methanol. Sources and destinations are determined via a csv uploaded by the user, as well as transfer volumes.


Explanation of complex parameters below:
* `csv file`: The csv file should be formatted like so. Note - for no mix steps, input "0" for the mix repetition. Also specify whether to mix at the source, or destination tube for that row:

![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/528c16/Screen+Shot+2022-03-11+at+1.52.52+PM.png)
* Note: for aspiration height percent (column J), a value of 10 means that we will be aspirating from 10% of the tube depth, 50 will be 50% of the tube depth, etc.
* `P20/P1000 Mount`: Specify which mount (left or right) for each single channel pipette.

---

### Labware
* [Opentrons 4-in-1 tube rack with 50mL & 15mL Falcon tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 4-in-1 tube rack with 1.5mL Eppendorf snap cap tubes](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 1000ul tips](https://shop.opentrons.com/universal-filter-tips/)
* [Opentrons 20ul tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [P1000 Single-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/528c16/Screen+Shot+2022-03-14+at+9.46.44+AM.png)

---

### Protocol Steps
1. Protocol parse of csv.
2. OT-2 visits source labware, source well.
3. Volume is transferred to destination labware, destination well as specified in the csv.
4. New tip is granted (note for transfer volumes < 100ul, the P20 pipette is used, otherwise the P1000 pipette is used).
5. Steps 2-4 are repeated for all lines of the csv.

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
528c16
