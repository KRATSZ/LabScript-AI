# Cherrypicking with Defined Aspiration Heights

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Featured
	* Cherrypicking

## Description
With this protocol, your robot can perform multiple well-to-well liquid transfers using a single-channel pipette by parsing through a user-defined .csv file. The protocol can use Opentrons GEN1 or GEN2 pipettes.

This particular cherrypicking protocol  allows you to specify the source plate labware and slot number, as well as the aspiration height above the bottom of the well (in mm). Appropriate tip racks will be placed in every slot that isn't already populated with a source or destination labware.


Explanation of complex parameters below:
* `Pipette Type`: Specify which single channel pipette you will be using for this protocol.
* `input .csv file`: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3359a5/template.csv) being sure to include the header line. Refer to our [Labware Library](https://labware.opentrons.com/?category=wellPlate) to copy API names for labware to include in the `source_labware` and `destination_labware` columns of the .csv.

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
Example Deck Setup - this is variable depending on the .csv uploaded.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3359a5/Screen+Shot+2021-04-29+at+2.45.06+PM.png)


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
3359a5
