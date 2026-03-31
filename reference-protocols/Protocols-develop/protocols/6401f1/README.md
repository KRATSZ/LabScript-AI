# PCR/qPCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * PCR Prep

## Description

This protocol uses a p300 single channel and p20 single channel pipette to transfer custom volumes of master mixes to a 96-well PCR plate followed by addition of custom volumes of sample, positive control, or no-template control.

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6401f1/Sample%2Badd%2Bexample%2Bfile_2329C_updated.csv)

This protocol was developed to combine custom volumes of master mixes with custom volumes of sample, positive control, or no-template control for PCR/qPCR setup.

## Protocol Steps

Set up: PCR plate (96-deep-well BioRad Hard Shell Plate) in deck slot 1, Master Mix 24-Tube Rack in deck slot 2, Samples (LVL 96-Tube Rack) in deck slot 3, Positive and NTC (LVL 96-Tube Rack) in deck slot 6, p20 tips in deck slot 4, p300 tips in deck slot 5.

The OT-2 will perform the following steps:
1. step 1- Transfer master mix volumes to PCR plate wells according to input data in the csv file.
2. step 2- Transfer sample and positive, no-template control to PCR plate wells according to input data in the csv file.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 Pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6401f1/6401f1_layout.png)

* Opentrons p20 and p300 tips (Deck Slots 4, 5)
* PCR Plate hardshell_96_wellplate_200ul (Deck Slot 1)
* Sample Plate lvl_96_wellplate_1317.97ul (Deck Slot 3)
* Positive and No Template Control Plate lvl_96_wellplate_1317.97ul (Deck Slot 6)
* 24-Tube Rack (Master Mixes) beckman_24_tuberack_1000ul (Deck Slot 2)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6401f1/screenshot_example_csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload input csv file (containing info about master mixes, samples and controls, locations and volumes-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6401f1
