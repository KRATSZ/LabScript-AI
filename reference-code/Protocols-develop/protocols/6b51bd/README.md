# Custom Dilution From CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Normalization

## Description

This protocol uses a p300 single-channel pipette to distribute custom volumes of buffer from a 12-well reservoir to specified wells of up to three 96-well child plates followed by transfer of well contents from up to three 96-well parent plates to the corresponding well in a child plate (volumes, plate locations and well locations are specified in a csv file uploaded at the time of protocol download).

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6b51bd/Example+CSV.csv)


This protocol was developed to distribute custom volumes of buffer from a 12-well reservoir to specific wells of a child plate and then transfer contents from specific wells of parent plates to corresponding wells of child plates.

## Protocol Steps

Set up: Place up to three 96-well parent plates in deck slots 4, 7, and 10 and up to three 96-well child plates in deck slots 5, 8 and 11 (the count of parent and child plates and their deck slot locations will be determined by the content of the uploaded csv). Place the 12-well reservoir for buffer in deck slot 9. The protocol run will pause and remind of the number of reservoir wells to fill with the indicated volume of buffer. Opentrons 20 ul filter tips (deck slots 1 , 2 and 3). Opentrons 200 ul filter tips (deck slot 6).

The OT-2 will perform the following steps:
1. Use the p300 single to distribute buffer from the reservoir to wells of the child plates according to the uploaded csv file.
2. Use either the p20 single or p300 single to transfer parent plate well contents to wells of child plates and then mix according to plate locations, well locations and volumes specified in the uploaded csv file.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips for the p20 and p300 Pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6b51bd/6b51bd_layout.png)

* Opentrons 200ul filter tips (Deck Slot 6)
* Opentrons 20ul filter tips (Deck Slots 1, 2, 3)
* 96-well Child Plates (Deck Slots 5, 8, 11)
* 96-well Parent Plates (Deck Slots 4, 7, 10)
* Reservoir (Deck Slot 9)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6b51bd/example_csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to choose the labware for the parent and child plates and the reservoir. Indicate the dead volume for the reservoir wells (volume at which to change to next source well). Upload the input csv file (containing info about plate locations, well locations and volumes for the transfers to be performed-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6b51bd
