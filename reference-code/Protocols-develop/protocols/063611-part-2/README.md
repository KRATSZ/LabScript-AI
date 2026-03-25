# Custom Tip Rack Formatting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Plate Filling

## Description

This protocol uses a p300 multi-channel pipette to run a separate, preparative process to put 300 ul tips into a custom arrangement required for use of a multi-channel pipette with only four tips attached on alternating nozzles for use with a custom labware rack which contains 6 columns of 4 tubes. The starting deck arrangement requires either 2, 4 or 6 tip boxes. Half of those tip boxes must be completely full while the other half must be completely empty.

Links:
* [Custom Cap Filling](https://protocols.opentrons.com/protocol/063611)
* [Custom Tip Rack Formatting](https://protocols.opentrons.com/protocol/063611-part-2)

This protocol was developed as a separate preparative process to set up a custom arrangement of 300 ul tips needed to use a custom rack (with 6 columns of 4 wells each) in the attached Custom Cap Filling protocol.

## Protocol Steps

Set up: Place completely full tipracks opentrons_96_tiprack_300ul in deck slots 7, 8 and 9. Place completely empty tipracks opentrons_96_tiprack_300ul in deck slots 4, 5 and 6.

The OT-2 will perform the following steps:
1. Move 4 tips from each column of the full boxes to the corresponding column of the empty boxes.
2. Pick up and drop 3 tips, then 2 tips, then 1 tip for each column to put tips in alternating rows A, C, E, and G.
3. Note - this same process can be performed with conventional pipette movements and fewer steps (faster runtime) if a p300 single-channel pipette is available.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p300 pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/063611-part-2/tiprack_reformatting_layout.png)

* Opentrons p300 tips opentrons_96_tiprack_300ul (these boxes should be full) (Deck Slots 7, 8, 9)
* Opentrons p300 tips opentrons_96_tiprack_300ul (these boxes are initially empty) (Deck Slots 4, 5, 6)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate the box count as 2 (one full, one empty), 4 (two full, two empty), or 6 (three full, three empty) using the parameters available on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
063611-part-2
