# Custom Cap Filling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Plate Filling

## Description

This protocol uses a p300 multi-channel pipette to top-dispense 250 ul of liquid from a reservoir into as many as 96 caps housed in up to four custom racks (each rack has 6 columns of 4 caps each). The 300 ul tips are required to be in a custom arrangement (tiprack rows B, D, F, H are empty to permit a mode of non-standard, multi-channel pipetting with 4 tips mounted on alternating nozzles) to support use of custom racks having 6 columns of 4 wells each. The custom tip arrangement can be set up manually, with a separate preparative OT-2 protocol (part-2) attached on this page (recommended), or as a first step at the start of the main protocol.  

Links:
* [Custom Cap Filling](https://protocols.opentrons.com/protocol/063611)
* [Custom Tip Arranging](https://protocols.opentrons.com/protocol/063611-part-2)

This protocol was developed to transfer 250 ul of liquid from a reservoir into as many as 96 caps arranged in columns of 4 in up to 4 custom racks. Tip change after every rack is optional. Tip tracking to keep track of the starting tip from run to run is optional. Preparation of the custom tip arrangement at the start of this main protocol is optional (recommendation is to handle tip arrangement as a separate process by using protocol Custom Tip Arranging attached above as part 2).

## Protocol Steps

Set up: Up to 4 custom 24-well racks (6 columns of 4 caps each) in deck slot fill order 4, 1, 5, 2. Opentrons 300 ul tips (in custom arrangement) in slots 10 and 11.

The OT-2 will perform the following steps:
1. Aspirate 250 ul of liquid from the reservoir and top dispense 250 ul per cap to each column of caps in the custom racks. By default drop tips after all caps in a rack are filled or optionally change tips after every dispense.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p300](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/063611/063611_layout.png)

* Opentrons p300 tips in a custom arrangement (Deck Slots 10, 11)
* Custom Racks (4 columns of 6) (Deck Slots 4,1,5,2)
* Reservoir nest_1_reservoir_195ml (Deck Slot 3)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Indicate the cap count, rack count, if all four racks will stay on deck even when there are fewer than 96 caps, if tips should be changed after every dispense, and the height (in mm) for the tips above the bottom of the reservoir during aspiration using the parameters available on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
063611
