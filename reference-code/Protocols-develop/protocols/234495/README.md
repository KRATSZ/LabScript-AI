# LC-MS Sample Prep: Standards/Calibration Curves/Patient Samples

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Mass Spec

## Description
Prepare Standard Samples for Calibration Curves. Prepare Pooled and or Patient Samples.

With this protocol, your robot can perform sample preparation for LC-MS as described [experimental protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-05-12/eq03qff/Protocol-90%20ul-tube.pdf)

This step prepares standards for calibration curves followed by patient samples.

## Protocol Steps

Set up: See details in pause comment at the top of the script and displayed in the OT-app at the start of the protocol.

The OT-2 will perform the following steps:
1. Make a 1:2 dilution series of unlabeled standards.
2. Prepare a solution of labeled standards.
3. Distribute Golden Plasma to sample tubes.
4. Combine unlabelled standard, NEM, labeled standard.
5. Add TFA in Acetonitrile.
6. Pause for centrifugation.
7. Transfer supernatant to Amicon filters.
8. Pause for centrifugation and drying.
9. Resuspend in Acetonitrile:Water.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p300 and p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons p300 tips (Deck Slots 6, 9)
* Opentrons p20 tips (Deck Slots 2, 3)
* nest_12_reservoir_15ml (Deck Slot 5)
* opentrons_24_tuberack_nest_1.5ml_snapcap (Deck Slots 1 and 4)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Choose tuberack labware and clearances in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
234495
