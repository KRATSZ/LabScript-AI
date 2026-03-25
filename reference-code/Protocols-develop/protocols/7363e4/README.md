# Custom Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Aliquoting

## Description

This protocol uses a p1000 single channel pipette to divide up to forty eight 3 mL clinical samples each into four aliquots with aliquot volumes of 1 mL, 0.5 mL, 0.5 mL and 1 mL.

Links:
* [Custom Aliquoting](https://protocols.opentrons.com/protocol/7363e4)
* [Custom Pooling](https://protocols.opentrons.com/protocol/7363e4-part-2)


## Protocol Steps

Set up: Place selected Opentrons 15-well or custom 40-well racks for clinical sample tubes (selected from pulldown list on this page at the time of protocol download) in one or both of deck slots 8 and 9. Place selected rack and tube type for aliquots in up to 8 deck slots and include 4 aliquot tubes for each clinical sample tube (deck slot fill order 10, 7, 4, 5, 6, 1, 2, 3). Ensure that the clinical sample tubes and aliquot tubes in all racks are in column-wise order. Place 1000 uL tips in deck slot 11.

The OT-2 will perform the following steps:
1. Aspirate 1 mL from the very first clinical sample tube (A1 of either deck slot 8 or deck slot 9).
2. Dispense 1 mL to the first aliquot tube in A1 deck slot 10 (aliquot 1).
3. Aspirate another 0.5 mL from the first clinical sample tube in A1.
4. Dispense 0.5 mL to the second aliquot tube in B1 deck slot 10 (aliquot 2).
5. Aspirate another 0.5 mL from the first clinical sample tube in A1.
6. Dispense 0.5 mL to the third aliquot tube in C1 deck slot 10 (aliquot 3).
7. Aspirate another 1 mL from the first clinical sample tube in A1.
8. Dispense 1 mL to the fourth aliquot tube in D1 deck slot 10 (aliquot 4).
9. Repeat for all clinical sample tubes.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p1000 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p1000 Pipette](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7363e4/1213_updated_layout.png)

* Opentrons p1000 tips (Deck Slot 11)
* 15 or 40-well custom rack or empty slot as specified in pulldown lists (Deck Slots 8-9)
* opentrons_24_tuberack_nest_1.5ml_snapcap or opentrons_24_tuberack_nest_2ml_snapcap as specified with pulldown list (up to 8 racks as displayed in OT app with deck slot fill order 10, 7, 4, 5, 6, 1, 2, 3)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Specify the following using pulldown lists or data entry fields on this page - Choose 15-well rack, 40-well rack, or empty slot for clinical samples in slots 8 and 9 and specify the number of clinical samples (48 in total maximum) to be loaded into these racks. Specify the rack and tube type for the aliquots.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7363e4
