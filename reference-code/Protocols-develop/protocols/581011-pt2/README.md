# Cherrypicking with Multi-Channel Pipette and CSV - Part 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description
This protocol parses an uploaded .csv file (see below) and determines the number of tips to pick up with a multi-channel pipette. The pipette transfers the specified volume of effector cell to a 384 well-plate to the parsed wells by multi-dispensing as much as the pipette tip can accommodate before returning to the reservoir. The pipette keeps the same tip for the duration of the run.

Note: Part 1 and Part 2 should receive the exact same .csv file.

Find part one of the protocol (target cell loading) below:

[Part 1 - Target Cell Loading](https://protocols.opentrons.com/protocol/581011)

Explanation of complex parameters below:
* `.CSV File`: Upload the .csv file according to the template shown [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/581011/co-culture_template_protocol.numbers). Any well to the left of a forward slash (`/`) will correspond to the well in the reservoir containing the desired target cell. Any well to the right of a forward slash (`/`) will correspond to the effector cell in the 96 well plate for part 2 of this protocol. If a cell is only to receive one of the effector or target cells, place a `0` (e.g. A1/0 would mean target cell from A1 of the reservoir with no effector cell). All cells that are to be skipped (receive neither effector nor target cell) should have a lowercase `'x'` in the resepective cell in the .csv file. For the parameters below, make sure there are NO commas inside of the wells, and just the values. For the mount, put nothing else but "left" or "right". For the pre-mix variable, you must start the well with "Yes" or "No", but can put anything else after that (e.g. "Yes premix", or "No premix").
* `Transfer Volume Target Cell`: Specify the volume (in ul) to transfer between target cells in reservoir to well plate.
* `Pre-mix before aspirating in source reservoir?`: Specify whether or not to pre-mix before each transfer of target cell in reservoir to plate.
* `Pre-mix height in reservoir`: If `Pre-mix` variable is set to `Yes`, specify the height in the reservoir wells in which to pre-mix.
* `Pre-mix repetitions`: If `Pre-mix` variable is set to `Yes`, specify the number of repetitions to mix before each transfer.
* `Pre-mix Volume`: If `Pre-mix` variable is set to `Yes`, specify the pre-mix volume (in ul).
* `Pre-mix Rate`: If `Pre-mix` variable is set to `Yes`, specify the mix rate. A value of `1` is default mix speed, whereas a value of `0.5` is half of the default mix speed, etc.
* `Dispense Reservoir Height`: Specify the height above the reservoir bottom to dispense residual solution.
* `Transfer Aspiration Height`: Specify the height in which to aspirate from in the reservoir. Default is 1mm from the bottom of the reservoir.
* `Transfer Dispense Height`: Specify the height in which to dispense from in the well plate. Default is 1mm from the bottom of the reservoir.
* `Aspiration Rate`: Specify the aspiration rate for transfers. A value of `1` is default aspiration speed, whereas a value of `0.5` is half of the default aspiration speed, etc.
* `Dispense Rate`: Specify the dispense rate for transfers. A value of `1` is default dispense speed, whereas a value of `0.5` is half of the default dispense speed, etc.
* `P300 Multi-Channel Mount`: Specify whether the P300 Multi-Channel pipette is on the left or right mount.
---

### Labware
* [Corning 384 Well Plate 112 µL Flat](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P300 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

---

### Deck Setup
* Deck layout - example 384 plate populated with target cells, random column chosen for effector cells. Note: only one column of effector cells should be loaded, but any column can be loaded. Effector cells should always be put in the 96 well plate from row A down (i.e. effector cell 1 should always be A1, A2, A3, A4,..., or A12).


![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/581011/Screen+Shot+2021-08-19+at+12.19.37+PM.png)

---

### Protocol Steps
1. Protocol scans .csv file.
2. Protocol determines number of tips to pickup with 8 channel pipette.
3. Target cell is aspirated from reservoir, with pre-mix if selected.
4. Target cell is dispensed into 384 well-plate.
5. Control are added to 384 plate.

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
581011
