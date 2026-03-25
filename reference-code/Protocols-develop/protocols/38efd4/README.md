# Protein Crystallization Screen Builder

### Author
[Opentrons](https://opentrons.com/), Ricardo Padua, Brandeis University



## Categories
* Sample Prep
     * Plate Filling

## Description

This protocol uses p300 single channel and p1000 single channel pipettes to transfer and mix custom volumes (ranging from 20 ul - 2 mL specified in input csv file) of water and each of up to 8 stock reagents to the wells of a 96-deep-well plate followed by optional mixing of the well contents.

Links:
* [example reagent csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/Configuration_0725.csv)
* [example formulation csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/Formulation_0725.csv)
* [supplemental information spreadsheet](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/ScreenMaker.xlsx)

This protocol was developed to combine and mix custom volumes (specified in input csv file) of water and up to 8 stock reagents for the screening of protein crystallization conditions in support of protein structure studies.

## Protocol Steps

Set up: Crystallization plate (96-deep-well plate) in deck slot 9, p300 tips in deck slot 10, p1000 tips in deck slot 11. Deck slots 1-8 will be either empty or occupied by a tube rack and tube type selected from the pulldown list at the time of protocol download. Water plus up to 8 stock reagent solutions will each be placed in one to many tubes (tubes of a given reagent must be in the same tube rack) with deck slot, well locations, volumes, liquid class (aqueous, volatile or viscous) and viscosity (units mPa.s) specified by the input reagent csv file (see example).

The OT-2 will perform the following steps:
1. step 1- For water and each of up to 8 reagents in reagents csv, transfer designated volumes to designated wells of the crystallization plate in slot 9.
2. step 2- Optionally, perform a mix of all wells in the crystallization plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/38efd4_layout.png)

* Opentrons p300 and p1000 tips (Deck Slots 10, 11)
* Crystallization Plate usascientific_96_wellplate_2.4ml_deep (Deck Slot 9)
* Deck Slots 1-8 will either be empty or contain any of the following labware (based on selections made from the pulldown list at the time of protocol download) opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical, opentrons_15_tuberack_falcon_15ml_conical, opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap, opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap, opentrons_6_tuberack_falcon_50ml_conical.

![reagents csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/38efd4_reagents_csv_format.png)

![formulation csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/38efd4/38efd4_dispenses_to_crystallization_plate.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select a tube rack or choose empty for deck slots 1-8 using the parameters below. Also upload reagents csv file (containing info about reagent stock solutions-see example for data and file format) and formulation csv file (defines custom mixture of reagents that each well of the crystallization plate will receive-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
38efd4
