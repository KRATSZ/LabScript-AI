# Mock Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Pooling

## Description
This protocol automates the pooling of 20 ul aliquots taken from designated wells of a 2 mL 96-well plate and dispensed into a single tube.
Only the rear-most channel of the p300 multichannel pipette is used.

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p300 pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons p300 tips (Deck Slot 4)
* 'nest_96_wellplate_2ml_deep' (Deck Slot 5)
* 'lvltechnologies_48_wellplate_2000ul' (Deck Slot 6)

### Robot
* [OT-2](https://opentrons.com/ot-2)


## Process
1. Use the parameters below to provide a list of designated source wells (as a comma-separated string like "A1,B2,C3" with no spaces), provide the row and column location of the pool tube (example "A1"), answer "YES" if using the same tip for pooling and provide well bottom clearance for aspirate and dispense (in mm).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes

###### Internal
315118
