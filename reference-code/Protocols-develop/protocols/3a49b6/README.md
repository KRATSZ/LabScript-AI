# Normalization of RNA Concentration

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Normalization

## Description
Normalize RNA concentration across up to 96 samples by combining custom volumes of water and RNA sample (volumes specified in csv file).

Links:

[example csv](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-09/0e24lpo/RNA%20conc_sample.xlsx)
[deck layout](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-09/aw34l9t/1.jpg)

This protocol combines custom volumes of input RNA with custom volumes of water (volumes listed in csv file, example above) to achieve uniform RNA concentration across all samples. This protocol normalizes up to 96 input RNA samples.

## Protocol Steps

Set up: Pre-cool the temperature module to 4 degrees via settings in the Opentrons app prior to running this protocol. Add p20 filtered tips (slots 8 and 5), water (15 ml conical tube in well A1 in slot 11), destination plate (slot 9) and intermediate dilution plate (slot 6) to the OT-2 deck. Place the 96-well plate containing initial RNA samples (added to the plate in A1-A12, B1-B12, C1-C12 order) on the temperature module (slot 3).

The OT-2 will perform the following steps:

1. A custom volume of water (listed in the csv file) is dispensed to the wells of the destination plate using a single channel p20.

2. A custom volume of RNA (listed in the csv file) is dispensed to the wells of the destination plate using a single channel p20. When listed RNA volumes are less than 2 ul, an intermediate 5X dilution of the RNA is used (3 ul RNA + 12 ul water in a temporary plate) and then a 5-fold larger volume of this dilution is transferred to the destination plate (with a corresponding reduction in Vol H2O). The dilution and destination plates are mixed after each dispense of RNA.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Temperature Module (Deck Slot 3)
* Opentrons p20 filter tips (Deck Slots 8 , 5)
* Opentrons "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical" (Deck Slot 11)
* Opentrons "nest_96_wellplate_100ul_pcr_full_skirt" (Deck Slot 9)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your csv file using the parameters below. Also choose the right or left pipette mount for the p20, the tube bottom clearance in millimeters for the water aspiration, the number of mixes to perform, and the preferred flow rate (default, 2 x default, or 3x default) for aspirate and dispense with the p20.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3a49b6
