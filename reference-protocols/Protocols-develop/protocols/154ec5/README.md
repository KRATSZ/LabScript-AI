# Custom Cherrypicking

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Cherrypicking

## Description

This protocol uses a p20 single channel pipette to transfer custom volumes (2-10 uL) from source wells located in one of up to 10 pieces of 24-well, 96-well or 384-well labware on the OT-2 deck to a destination well in one of the ten pieces of loaded labware. The labware, deck slot locations, source plate, source well, destination plate, destination well and transfer volume are supplied by the user in a csv file uploaded at the time of protocol download (see example for file and data format).

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/154ec5/example%2BCSV.csv)

This protocol was developed to transfer custom volumes (2-10 uL) from source wells to destination wells as described above.

## Protocol Steps

Set up: Place selected 24-well, 96-well and/or 384-well labware (selected from pulldown list on this page at the time of protocol download) in deck slots 1-10 as indicated in your uploaded csv file. Place 20 uL tips in deck slot 11.

The OT-2 will perform the following steps:
1. step 1- Aspirate custom volume (2-10 uL) from source well according to input data in the csv file.
2. step 2- Dispense to destination well according to input data in the csv file.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 Pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/154ec5/layout_154ec5.png)

* Opentrons p20 tips (Deck Slot 11)
* 24, 96 and/or 384-Well Labware As Specified With Pulldown Lists and in Your Uploaded CSV File - see example for file and data format (Deck Slots 1-10)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/154ec5/154ec5_example_csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Choose your 24, 96, and 384-well labware using pulldown lists on this page. Upload your input csv file (containing info about source plate, source well, destination plate, destination well and transfer volumes-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
154ec5
