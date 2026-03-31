# BioFluid Mix and Transfer - Part 1/2 (API v2)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Distribution


## Description
This protocol is part 1 of 2-part protocol designed to transfer biofluids and add the necessary reagents for preparation. In this part, The biofluids are distributed from cryovials to centrifuge tubes and two solutions are added. The samples are then transferred to a Nanosep 3k Ultrafiltration tube in preparation of centrifugation. See below for deck and reagent setup.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P50 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [50/300uL Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons aluminum block set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* Cryovials (containing samples)
* 0.5mL centrifuge tubes (clean and empty)
* Nanosep 3K Ultrafiltration tubes (clean and empty)
* Custom container for holding cryovials
* Custom container for holding centrifuge tubes (x2)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1/4/7: Custom container for holding centrifuge tubes, filled with Nanosep 3k Ultrafiltration tubes

Slot 2/5/8: Custom container for holding centrifuge tubes, filled with 0.5mL centrifuge tubes

Slot 3/6/9: Custom container for holding cryovials, filled with cryovials containing samples

Slot 10: [Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [24-Well Aluminum Block ](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set):
* A1: Solution 1
* A2: Solution 2
* A3: Solution 2
* A4: Solution 2
* B1: Solution 2
* B2: Solution 2

Slot 11: [50/300ul Opentrons tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3cf31f