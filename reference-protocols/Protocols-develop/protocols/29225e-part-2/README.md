# qRT-PCR Setup: Part 2 - Custom Reaction Set Up from CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
     * PCR Prep

## Description

This protocol uses p300 single and p20 (single or multi channel) pipettes to distribute custom volumes of water (0-2 uL from a single tube) and master mix (up to 19 uL from any single well or tube within up to 4 racks or plates) and then transfer normalized RNA samples (2-7 uL with either single or multi channel p20 from wells or columns of up to 4 racks or plates) to a single 96-well PCR plate held at 4 degrees C on the temperature module (water, master mix and normalized RNA volumes, locations etc. specified by user in two csv files uploaded at the time of protocol download). Valid source and destination well locations for the multi-channel pipette must be in row A of a 96-well formatted labware.

Links:
* [example master mix input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/mastermix.csv)

* [example transfers input csv for p20 single](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/qRT-PCR_for_p20_single.csv)

* [example transfers input csv for p20 multi](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/qRT-PCR_for_p20_multi.csv)

* [Part 1 - RNA Normalization](https://protocols.opentrons.com/protocol/29225e)

This protocol was developed to distribute custom volumes (0-2 uL) of water (to specific wells), (up to 19 uL) master mix (to specific wells), and then transfer (2-7 uL) normalized RNA (to specific wells or columns) to a single 96-well PCR plate held at 4 degrees on the temperature module.

## Protocol Steps

Set up: Use the OT app to pre-cool the temperature module to 4 degrees prior to running this protocol. Place the 96-well PCR plate on the temperature module (deck slot 1). Normalized RNA samples in up to a total of four racks or plates (deck slots 2, 3, 5, 6 in that order), master mixes in up to a total of four racks or plates (deck slots 4, 7, 8, 9 in that order), Opentrons 20 ul (deck slot 10) and 200 ul filter tips (deck slot 11). A single well or tube containing RNAse-free water (in well A1 of the first master mix rack or plate in deck slot 4).

The OT-2 will perform the following steps:
1. Use the p20 single to distribute water (0-2 uL) from the water tube to wells of the PCR plate according to the uploaded transfers csv file. Alternatively, when the p20 single is not selected by the user, pause and prompt the user to perform manual transfers of water. Volumes and destination wells are provided in a displayed pause comment viewable in the OT app.
2. Use the p300 single to distribute master mixes (up to 19 uL) to wells of the PCR plate according to the uploaded transfers csv file.
3. Use either the p20 single or p20 multi to transfer (2-7 uL) normalized RNA samples to the PCR plate according to the uploaded transfers csv file. Mix the RNA with the master mix and water. Valid source and destination well locations for the multi-channel pipette must be in row A of a 96-well formatted labware.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20, Multi-Channel p20 and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips for the p20 and p300 Pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/deck_layout.png)
![water tube in A1 of first master mix plate or rack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/water_tube_in_A1_of_first_mastermix_rack.png)

* Opentrons 200ul filter tips (Deck Slot 11)
* Opentrons 20ul filter tips (Deck Slot 10)
* Selected Labware for Normalized RNA Samples (Deck Slots 2, 3, 5, 6)
* Selected Labware for Water and Master Mixes (Deck Slots 4, 7, 8, 9)
* Opentrons Temperature Module with 96-well PCR Plate (Deck Slot 1)

![input master mix csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/example_mastermix_csv.png)
![input transfers csv data and file format for p20 single](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/example_transfers_csv.png)
![input transfers csv data and file format for p20 single](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/29225e/screen+capture+example+csv+multi-channel.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to choose the labware for the pcr plate, master mixes and water, and normalized RNA samples. Indicate the starting volume of RNAse-free Water. Upload the two input csv files (containing info about master mixes and transfers to be performed-see examples for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
29225e-part-2
