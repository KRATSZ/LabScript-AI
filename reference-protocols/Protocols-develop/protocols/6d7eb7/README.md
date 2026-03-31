# Cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description

Our most robust cherrypicking protocol. Specify aspiration height, labware, pipette, as well as source and destination wells with this all inclusive cherrypicking protocol.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Your `Transfer .csv File` should be a .csv file formatted in the following way:

```
Pipette Mount to use,Source Labware,Source Slot,Source Well,Source Aspiration Height Above Bottom (in mm),Destination Well,Volume (in ul)
left,4x6 2ml screw true,1,A1,1,A11,1
left,4x6 1.5ml snap,1,A1,1,A5,3
right,8x12 0.5ml snap,2,A1,1.5,H12,7
...
```
You can also download a template [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7eb7/ex.csv). **Please making sure to include headers in your .csv file.**

Your source labware selection in the .csv file must be one of the following options, which correspond to the different sample tubes you use in your workflow:
* `384 wellplate`
* `96 wellplate`
* `4x6 2ml screw true`
* `4x6 2ml screw false`
* `4x6 1.5ml snap`
* `4x6 1.5ml screw`
* `8x12 strip`
* `8x12 1ml plug`
* `8x12 0.5ml snap`

The height offsets of different tubes seated in the same tuberack will be automatically calculated in the Python protocol logic. However, **please ensure to calibrate your tuberacks with the following tube types in spot A1**:
* 4x6 Opentrons tuberack: 2ml screwcap false bottom in spot A1
* 8x12 ThermoScientific Matrix tuberack: 1ml plugcap in spot A1

Calibration to these tubes and tuberacks will allow for offsets to be properly taken into account during the protocol run.

---

### Pipettes
* [P20 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P1000 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Multi GEN2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* Example deck setup - tip racks loaded onto remining slots.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7eb7/deck.png)

---

### Protocol Steps
1. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot is also specified, as well as aspiration height from the bottom of the well.
2. Pipette will dispense this volume into user-specified labware and well according to the imported csv file. Slot is also specified.
3. Steps 1 and 2 repeated over the duration of the CSV.

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
6d7eb7
