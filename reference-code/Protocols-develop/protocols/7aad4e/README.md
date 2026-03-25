# Cell Culture Cherry Picking with CSV File

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Cherry Picking

## Description
This protocol preps up to two 96 well plates with cell culture media from up to 6 source 384 well plates. The protocol will automatically parse through the csv to determine how many plates are on the deck, giving the user the ability to have flexibility in run size, however plates should still be placed in order of the deck slot numbers. Culture is pre-mixed with an airgap before transfer.


Explanation of complex parameters below:
* `.CSV File`: Here, you should upload a .csv file formatted in the following way, being sure to include the header line (do NOT have "0" in between well names i.e. "A01", it should be "A1")
![csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7aad4e/Screen+Shot+2022-02-28+at+2.41.45+PM.png)
* `P300 Mount`: Specify which mount (left or right) to host the P300 pipette.

---


### Labware
* Corning 96 well plate, flat
* Perkin Elmer 110ul 384 well plate, flat
* [Opentrons 200ul Filter tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [Opentrons P300 Single-Channel Pipette](https://shop.opentrons.com/pipettes/)

---

### Deck Setup
Note: the protocol will read the csv source and destination slots to load labware onto the deck. Plates should always be placed in order of smaller deck number to large (i.e. place 384 plates in slots 1, 2, 3, and 4 if running 4 plates. If running one 96 plate, place it in slot 7 as opposed to 8).
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7aad4e/Screen+Shot+2022-02-28+at+2.44.21+PM.png)

---

### Protocol Steps
1. Pick up 1 tip from Opentrons 96 Filter Tip Rack 200uL using P300 Single Channel 20uL-300uL
2. Find location on Perkin Elmer 384-well Plate (Cat. 6007658)
3. Mix and Aspirate 50ul of Cell Culture Media leaving an air gap
4. Find location on Corning 96-well Plate (Cat. CLS3596-50EA)
5. Dispense 50ul of Cell Culture Media into Corning 96-well Plate (Cat. CLS3596-50EA)
6. Discard Single Tip Opentrons 96 Filter Tip 200uL into Trash
7. Repeat Steps 1 through 5 until all samples are transferred

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
7aad4e
