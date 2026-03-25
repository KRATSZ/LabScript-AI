# Custom Cherry Picking based on CSV File Input

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Cherrypicking

## Description

This protocol cherrypicks from source plate wells specified in the first column of an input CSV file and transfers 2 ul of the well's contents to destination plate wells specified in the second column of the input CSV file.

Links:
* [Custom Cherrypicking json Protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-06-09/cn23rrl/custom%20program.zip)
* [Opentrons Protocol Designer No-Code Tool](https://designer.opentrons.com/)
* [Sample CSV File](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-06-09/0y13r26/custom%20transfer.csv)

This protocol is a python translation of the attached custom cherrypicking json protocol that can be downloaded from the link above (and then uploaded to the online Opentrons Protocol Designer tool). This python translation has an added feature: upload of an input CSV file to specify source and destination wells.

## Protocol Steps

Set up: 195 mL NEST 1 Well Reservoir in slot 4 containing 50 mL LB, Destination Plate in slot 6, Source Plate in slot 8 containing 180 ul LB in outer wells and otherwise containing 200 ul SBW25, p20 tips in slot 7, p300 tips in slots 10 and 11.

The OT-2 will perform the following steps:
1. p300m transfer 198 ul LB to destination columns.
2. p300m mix 10 columns of SOURCE 80 ul 5X.
3. p20s transfer 2 ul from SOURCE A2, A11 and 30 custom-selected wells specified in the input CSV file to DESTINATION A2, A11, B2-B11, C2-C11, D2-D11.
4. p20s transfer 2 ul from SOURCE 30 custom-selected wells specified in the input CSV file and H2, H11 to DESTINATION E2-E11, F2-F11, G2-G11, H2, H11.
5. p300m mix columns of DESTINATION 80 ul 5X.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 and  Single-Channel p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1477ea/layout_1477ea.png)

* Opentrons p300 tips (Deck Slots 10, 11)
* Opentrons p20 tips (Deck Slot 7)
* 195 mL NEST 1 Well Reservoir (Deck Slot 4)
* Source Plate (TPP 96 well tissue culture plate Deck Slot 8)
* Destination Plate (NUNC WHITE 96F 236105 96 well plate Deck Slot 6)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload your input CSV file using the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1477ea
