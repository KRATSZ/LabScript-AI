# Custom Normalization From CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Normalization

## Description

This protocol uses a single tip on the p300 multi-channel pipette to distribute custom volumes of buffer (150-300 uL) from a 195 mL reservoir to specified wells of a 96-well destination plate followed by transfer of custom volumes of sample (2-15 uL) from up to three 24-tube racks to specified wells in the destination plate (volumes, rack locations and well locations are specified in a csv file uploaded at the time of protocol download).

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04fed3/example.csv)

## Protocol Steps

Set up: Place up to three 24-tube Opentrons racks in deck slots 1, 4, and 7 and the 96-well destination plate in deck slot 6. Place the reservoir containing diluent in deck slot 5. Opentrons 20 ul tips (deck slot 10). Opentrons 300 ul tips (deck slot 11).

The OT-2 will perform the following steps:
1. Use the p300 multi to distribute buffer from the reservoir to wells of the destination plate according to the uploaded csv file.
2. Use the p20 single to mix the sample source 6x, transfer sample to wells of the destination plate, and mix the destination well 3x according to the uploaded csv file.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 and Multi-Channel p300 Gen2 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 Pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04fed3/screenshot-deck.png)

* Opentrons 300ul tips (Deck Slot 11)
* Opentrons 20ul tips (Deck Slots 10)
* 96-well destination plate genesee25221_96_wellplate_300ul (Deck Slot 6)
* 24-tube Opentrons racks with 1.5 mL snap cap tubes opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap (Deck Slots 1,4,7)
* Reservoir nest_1_reservoir_195ml (Deck Slot 5)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04fed3/screenshot-example+csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to indicate the number of sample racks and upload the input csv file.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Run labware position check using the OT App. For tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
04fed3
