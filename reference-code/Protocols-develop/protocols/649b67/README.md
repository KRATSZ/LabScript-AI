# Advanced cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Advanced cherrypicking

## Description

This is an advanced cherrypicking protocol that allows for liquid transfers, aspirating and parking tips, pauses, and dispensing parked tips. The protocol allows for fine tuning how the instructions are carried out by specifying air gap volumes, tip touching and blow outs in the target wells.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Explanation of complex parameters below:

* `Transfer .csv File`: Here, you should upload a .CSV file formatted as shown below, making sure to include headers in your csv file.
* `Pipette type in the left mount`: Select which pipette you will use in the left mount for this protocol.
* `Pipette type in the right mount`: Select which pipette you will use in the right mount for this protocol.
* `Tip type for the left pipette`: Specify whether you want to use filter tips.
* `Tip type for the right pipette`: Specify whether you want to use filter tips.
* `Tip Usage Strategy`: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.


**CSV Format**

Example CSV input:
![CSV Example part 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/649b67/CSV_part1.png)
*Part 1 of an example CSV*
![CSV Example part 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/649b67/CSV_part2.png)
*Part 2 of an example CSV*


**Explanation of CSV Headers:**

*step_id:* Succesive natural number that gives each instruction an identity

*instruction:* What type of operation that this row specifies. There are four different instructions. **transfer:** Transfer a volume from the source well to the destination well. **aspirate_and_park_tip:** Aspirates from the source well and parks the tip, the tip can later be retrieved through its step_id. **pause:** Pause for some specified amount of time. **dispense_parked_tip** Dispense a parked tip into a destination well, specify the tip by identifying the step id from a previous aspirate_and_park_tip instruction.

*instruction_parameters:* Some instructions like pause have parameters, in the case of pause it is `time` (see below).

*source_labware:* The source labware used in this instruction, should be a valid Opentrons API name. The API name only needs to be specified the first time a slot is specified in an instruction.

*source_magnetic_module:* yes or no depending on whether a magnetic module is used with the source labware, only needs to be specified the first time and can be left blank after that.

*source_temperature_module:* yes or no depending on whether a temperature module is used with the source labware, only needs to be specified the first time and can be left blank after that.

*source_slot:* A valid slot on the Opentrons deck, i.e. it's a slot from 1 to 11 and it is not occupied by other labware or tipracks. Once a labware has been defined it is enough to specify a slot and a well for any subsequent operation.

*source_well:* The well to aspirate from, if it is a 15 or 50 mL tube the liquid height will be calculated for aspirations.

*Source_well_starting_volume:* The starting volume of the given well, only needs to be specified the first time.

*transfer_volume:* The volume (in uL) to transfer from the source well to the target well.

*air_gap_volume:* An air gap volume for protecting from dripping. Can be 0 or blank if not used.

*dest_labware:* The destination labware used in this instruction, should be a valid Opentrons API name. The API name only needs to be specified the first time the slot is specified in an instruction.

*dest_magnetic_module:* yes or no depending on whether a magnetic module is used with the destination labware, only needs to be specified the first time and can be left blank after that.

*dest_temperature_module:* yes or no depending on whether a temperature module is used with the destination labware, only needs to be specified the first time and can be left blank after that.

*dest_slot:* The slot where the destination labware resides. Once a labware has been defined it is enough to specify a slot and a well for any subsequent operation.

*dest_well:* The destination well to dispense liquid into.

*dest_well_starting_volume:* The initial volume of the target well, only needs to be specified for the first occurence of the well.

*touch_tip:* yes/no depending on if you want tip touching after dispensing into a well.

*blow_out:* yes/no depending on if you want blow out after dispensing into a well.

**Explanation of Instructions**

The labware is loaded by looking for the first definition of a slot and labware combination that occurs in a CSV instruction. The user should make sure that the first instruction where a source and/or destination slot is mentioned is fully specified with the source and/or destination labware and which (if any) modules it is using. If the temperature module is used the labware should be of an aluminum block type.

**Transfer instructions**

The transfer instruction can be limited to the step_id, and instruction, source slot, source well, transfer volume, target slot and target well if all the labware has been specified previously. If not, the labware source and target API load names and module usage must also be specified (by answering yes/no in the module fields). The transfer instruction tells the protocol how and where to transfer one liquid from a source well to a target well. Additionally an air gap volume, tip touching in the target well, and blow out in the target well can be specified. There are no instruction_parameters (3rd column field) associated with transfers.

**Pause instructions**

Requires three entries: A step id (1st field), an instruction named "pause" (2nd field) and a time parameter (3rd parameter). The time parameter should be formatted likes this: time=[\<x>h][\<y>m][\<z>s]. For example all of the following time parameters are valid:
`time=1h10m30s`, `time=25s`, `time=5m`, `time=3m10s`, etc.

**Aspirate and park tip instructions**

Aspirates a given volume from the source well and parks the tip, can be used for binding an analyte or contaminants in a liquid to a resin filled tip for example.

**Dispense parked tip instructions**

Picks up a parked tip identified by an `aspirate_and_park_tip` instruction step_id and dispenses it to a target well. e.g. the parameter_instruction could be `step_id=3` if that step_id belongs to an earlier `aspirate_and_park_tip` instruction.

---

### Labware
* Any verified labware found in our [Labware Library](https://labware.opentrons.com/). This includes aluminum block labware for use with temperature modules, well plates, tuberacks and reservoirs.

### Pipettes
* [P20 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P1000 Single GEN2 Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
* Example deck setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/Screen+Shot+2021-04-29+at+3.10.02+PM.png)

---

### Protocol Steps
1. The protocol will validate the Transfer CSV and the parameters before executing any instructions. The protocol validates the fields in the CSV, and makes sure that no well will be filled more than 80 % of the max volume. If the protocol detects overflow it will report in which steps the errors occur, warn the user and exit.
2. Transfer instructions: Pipette will aspirate a user-specified volume at the designated labware and well according to the instructions on that CSV row. If the well is a tube the protocol calculates the height of aspiration in order to avoid plunging the pipette into the liquid. The pipette then dispenses into the target well. If the target well is also a tube the pipette will dispense above the liquid level. The user can specifty an air gap volume, tip touching, and blow out.
3. Aspirate and park tip instructions: The pipette aspirates a given volume of liquid from a source well and then parks the tip. The tip can be retrieved subsequently.
4. Dispsense parked tip instructions: By specifying the step ID in which a tip was parked the protocol can pick up the same tip and dispense it somewhere else.
5. Pause instruction: The user can specify a pause in the protocol at that step, e.g. 5m30s.
6. The protocol proceeds until each instruction in the CSV is finished.

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
649b67
