# qRT-PCR Setup: Part 1 - Custom RNA Normalization from CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Normalization

## Description

This protocol uses p300 and p20 single channel pipettes to transfer custom volumes of water (1-50 uL from a single tube) and then RNA (1-50 uL) from a single 96-well source plate or from up to four 24-tube racks to a single 96-well destination plate (RNA volume and water volume, rack number (1-4) or plate number (1) for the input RNA source, tube (A1-D6) or well (A1-H12) location for the RNA source, and destination well (A1-H12) specified by user in a csv file uploaded at the time of protocol download).

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/RNA+normalization+123456.csv)

* [Part 2 - qRT-PCR Setup](https://protocols.opentrons.com/protocol/29225e-part-2)

This protocol was developed to transfer custom volumes of up to 96 input RNA samples from one of up to four 24-tube racks (or alternatively from a single 96-well RNA-source plate) to a single 96-well destination plate according to volumes, rack number (1-4) or plate number (1), and tube locations (A1-D6) or well locations (A1-H12) in the uploaded csv file.

## Protocol Steps

Set up: Use the OT app to pre-cool the temperature module to 4 degrees prior to running this protocol. Place the 96-well destination plate on the temperature module (deck slot 1). Up to 96 input RNA samples in up to a total of four 24-tube racks (deck slots 2, 3, 5, 6) or a single 96-well plate (deck slot 2), Opentrons 20 ul (deck slot 10) and 200 ul filter tips (deck slot 11). 1.5 mL eppendorf tubes containing RNAse-free water in well A1, B1, C1, D1, A2 of a 24-tube rack (deck slot 4).

The OT-2 will perform the following steps:
1. Distribute smaller volumes of water (10 uL or less) from the water tubes to wells of the destination plate according to the uploaded csv file.
2. Distribute remaining volumes of water (greater than 10 uL) from the water tubes to wells of the destination plate according to the uploaded csv file.
3. Transfer each input RNA sample to the destination plate according to the uploaded csv file. Mix the RNA with the water.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/norm_layout.png)

* Opentrons 200ul filter tips (Deck Slot 11)
* Opentrons 20ul filter tips (Deck Slot 10)
* Selected Labware for Input RNA Samples (Deck Slots 2, 3, 5, 6)
* Opentrons 24-tube rack with Water Tubes in A1, B1, C1, D1, A2 (Deck Slot 4)
* Opentrons Temperature Module with 96-well Destination Plate (Deck Slot 1)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/example_csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to choose the labware for the input RNA samples, indicate the starting volume of RNAse-free Water, and upload the input csv file (containing info about RNA (1-50 uL) and water volumes (1-50 uL), rack number (1-4) or plate number (1) containing each RNA sample, the destination well-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
29225e
