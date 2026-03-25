# Cherrypicking with multi-channel pipette substituting for a single channel pipette

### Author
[Opentrons](https://opentrons.com/)

### Partner
[AstraZeneca](https://www.astrazeneca.com/)



## Categories
* Sample Prep
	* Cherrypicking

## Description

A protocol based on our most robust [cherrypicking protocol](https://protocols.opentrons.com/protocol/cherrypicking) that has been modified to use a multi-channel pipette as single channel by only picking up a single tip at a time. Specify aspiration height, pipette, as well as source and destination wells with this all inclusive cherrypicking protocol.

This is an optional Part 2 protocol to its corresponding [Part 1: Normalization protocol using a multi-channel pipette](https://protocols.opentrons.com/protocol/6d901d)

**Note**: This protocol was updated for a change in our software stack and will require app 7.0 or greater.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Explanation of complex parameters below:

* `input .csv file`: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d901d/2/example.csv), making sure to include headers in your csv file.
* `Source Plate Type`: The plate that you want to cherrypick samples from.
* `Destination Plate Type`: The plate that you want to dispense cherrypicked samples in.
* `Reservoir Type`: A placeholder from part 1 of this protocol, it should be the same as the reservoir from part 1, although it is not used in this protocol. If there is no reservoir present in slot 9 you can set it to None.
* `Pipette Model`: Select which pipette you will use for this protocol.
* `Pipette Mount`: Specify which mount your multi-channel pipette is on (left or right)
* `Tip Type`: Specify whether you want to use filter- or regular tips.
* `Tip Usage Strategy`: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.
* `Starting Tiprack Slot`: If you want to start this protocol right after finishing part 1 without replacing your tipracks you can designate the first non-empty tiprack on the deck to start picking up tips from, otherwise leave this parameter at its default value of slot 4. The tipracks are ordered from first to last as slot 4, 5, 10, and 11.
* `Starting Tip Well`: Indicate the first well of the first non-empty tiprack containing a tip, e.g. H5, or B3, etc. Leave this parameter with the default value of H1 if starting with fresh tipracks.

---

### Labware
* Any verified labware found in our [Labware Library](https://labware.opentrons.com/?category=wellPlate) and some additional microplates (see plate options for source and destination plates parameters below, e.g. Greiner Bio-One plates).

### Pipettes
* [P20 Multi GEN2 Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P300 Multi GEN2 Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
* Example deck setup.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d901d/2/example_deck.jpg)

---

### Protocol Steps
1. The pipette will aspirate a user-specified volume from the well on the (optionally normalized, see [Protocol Part 1](https://protocols.opentrons.com/protocol/6d901d)) source plate according to the imported csv file. The CSV also defines the aspiration height from the bottom of the source well.
2. The pipette will dispense this volume into a user-specified target well according to the csv file.
3. Steps 1 and 2 repeated for each line the CSV.

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
6d901d-2
