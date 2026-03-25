# NGS Library Prep for Targeted Sequencing of DNA Methylation Patterns in Cell-Free DNA: Step 5 of 5: Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Zymoresearch: EZ DNA Methylation-Gold Kit

## Description
Part 5 of 5: 5 ul aliquots of PCR 2 product (output from step 4) are combined to form a single pool for each plate followed by bead clean up and transfer to a fresh tube.

Links:
* [Part 1: DNA Extraction](http://protocols.opentrons.com/protocol/76ba23)
* [Part 2: Bisulfite Conversion](http://protocols.opentrons.com/protocol/76ba23-bisulfite_conversion)
* [Part 3: PCR1](http://protocols.opentrons.com/protocol/76ba23-pcr1)
* [Part 4: PCR2](http://protocols.opentrons.com/protocol/76ba23-pcr2)
* [Part 5: Pooling](http://protocols.opentrons.com/protocol/76ba23-pooling)

With this work flow, your robot will use reagents from the Zymoresearch EZ DNA Methylation-Gold Kit [Zymoresearch EZ DNA Methylation-Gold Kit](https://www.zymoresearch.com/collections/ez-dna-methylation-gold-kits) to perform the custom steps (DNA extraction, Bisulfite Conversion, PCR1, PCR2, Pooling) detailed in the HKG SOP.[HKG SOP](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-04/vw23kchHKG%20Standard%20Operating%20Procedure%20for%20DNA%20extraction%20Targeted%20next%20generation%20sequencing%20and%20.xlsx).

This is part 5 of the work flow: Pooling.

This step combines 5 ul aliquots of 96 post-PCR 2 samples into a single pool for either one or two post-PCR 2 plates. This step is followed by a bead clean up and transfer of the finished pools to clean tubes.


## Protocol Steps

Set up: Place PCR 2 output samples (1 or 2 plates), tube rack (with 1 or 2 tubes for output pools), magnetic module and deep well plate, p300 and p10 tips on the OT-2 deck.  

The OT-2 will perform the following steps:
1. For each plate, combine 5 ul aliquots of PCR 2 product into a single pool.
2. Pause for the following manual steps (OT-2 deck lights will signal pauses):

   Vortex the beads prior to addition to well "A3" on the magnetic module.

3. Bead clean up and transfer of pools to fresh tubes.



---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Magnetic Module (Deck Slot 4)
* Opentrons p300 tips (Deck Slot 3)
* Opentrons p10 tips (Deck Slots 8, 7)
* 1 or 2 pcr plates PCR 2 product from previous step (Deck slots 2 and 5)
* tube rack for pools (Deck Slot 1)
* deep well plate on Magnetic Module ('usascientific_96_wellplate_2.4ml_deep') with pool_1_clean_up (pool 1 temporary dispense location and for clean up steps), pool_2_clean_up (pool 2 temporary dispense location and for clean up steps), beads, etoh, water in 'A1', 'A2', 'A3', 'A4', 'A5'

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Minutes to Air Dry Beads", "Number of PCR2 Plates to Pool (One or Two)", "Choose Filtered or Standard Tips for P300 single", "Choose Filtered or Standard Tips for P10 single" parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76ba23-pooling
