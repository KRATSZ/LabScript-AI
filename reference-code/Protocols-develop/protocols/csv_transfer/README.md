# Custom CSV Transfer Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* CSV Transfer

## Description

Accomplish complex workflows, easily with this Custom CSV Transfer Protocol. This protocol utilizes a CSV to specify aspiration height, labware, pipette, as well as source and destination wells.</br>
</br>
To use, simply upload a CSV (download a template with the proper format [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1211/example.csv) and select the parameters that match the OT-2 below before downloading the Python protocol. The protocol can then be used on the OT-2 and will make all of the transfers outlined in the CSV.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Explanation of complex parameters below:

* **input .csv file**: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1211/example.csv), making sure to include headers in your csv file. Refer to our [Labware Library](https://labware.opentrons.com/?category=wellPlate) to copy API names for labware to include in the *Source Labware* and *Dest Labware* columns of the .csv.
* **Pipette Model**: Select which pipette you will use for this protocol.
* **Pipette Mount**: Specify which mount your single-channel pipette is on (left or right)
* **Tip Type**: Specify whether you want to use filter tips.
* **Tip Usage Strategy**: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.



---


### Labware
* Any verified labware found in our [Labware Library](https://labware.opentrons.com/?category=wellPlate)

### Pipettes
* [P20 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P1000 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* P10 Single GEN1 Pipette
* P50 Single GEN1 Pipette
* P300 Single GEN1 Pipette
* P1000 Single GEN1 Pipette


---

### Deck Setup
* Example deck setup - tip racks loaded onto remining slots.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/Screen+Shot+2021-04-29+at+3.10.02+PM.png)

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
cherrypicking
