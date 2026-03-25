# NGS Library Prep for Targeted Sequencing of DNA Methylation Patterns in Cell-Free DNA: Step 4 of 5: PCR 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Zymoresearch: EZ DNA Methylation-Gold Kit

## Description
Part 4 of 5: PCR 1 product (output from step 2) is set up for a second PCR step featuring a unique forward primer for each plate (the forward primer is in the pcr2 mix, so different mixes should be used for each plate) and a unique, barcoded reverse primer for each well (there are two plates of unique barcodes for a total of 192).

Links:
* [Part 1: DNA Extraction](http://protocols.opentrons.com/protocol/76ba23)
* [Part 2: Bisulfite Conversion](http://protocols.opentrons.com/protocol/76ba23-bisulfite_conversion)
* [Part 3: PCR1](http://protocols.opentrons.com/protocol/76ba23-pcr1)
* [Part 4: PCR2](http://protocols.opentrons.com/protocol/76ba23-pcr2)
* [Part 5: Pooling](http://protocols.opentrons.com/protocol/76ba23-pooling)

With this work flow, your robot will use reagents from the Zymoresearch EZ DNA Methylation-Gold Kit [Zymoresearch EZ DNA Methylation-Gold Kit](https://www.zymoresearch.com/collections/ez-dna-methylation-gold-kits) to perform the custom steps (DNA extraction, Bisulfite Conversion, PCR1, PCR2, Pooling) detailed in the HKG SOP.[HKG SOP](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-04/vw23kchHKG%20Standard%20Operating%20Procedure%20for%20DNA%20extraction%20Targeted%20next%20generation%20sequencing%20and%20.xlsx).

This is part 4 of the work flow: PCR 2.

This step performs set up for a second PCR amplification using the output samples from PCR 1 as the starting template. A unique forward primer is used for each plate (so a different tube of pcr2 mix will be used for each plate). A unique reverse primer will be used for each well. There are 192 unique, barcoded reverse primers between the two barcode plates.

After the steps carried out in this protocol (part 4), proceed with part 5: pooling.


## Protocol Steps

Set up: Place PCR 1 output samples (1 or 2 plates), barcode plates (1 or 2), pcr plates for PCR 2 (1 or 2), pcr2 mix and p10 tips on the OT-2 deck.  

The OT-2 will perform the following steps:
1. Distribute sample (PCR 1 product) and pcr2 mix to the PCR plates.
2. Pause for the following steps (OT-2 deck lights will signal pauses):

           Thermocycling steps (outside of the OT-2).

           Replenish tips.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons p10 tips (Deck Slots 8, 11, 7, 10)
* 1 or 2 plates each with 96 samples (output from PCR 1) (Deck slots 1 and 4)
* pcr2 mix ("corning_96_wellplate_360ul_flat" Deck slot 9)
* 1 or 2 plates each with 96 unique barcoded primers (Deck slots 2 and 5)
* 1 or 2 pcr plates for PCR 2 (Deck slots 3 and 6)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Number of PCR2 Plates to Set Up (One or Two)", "Choose Filtered or Standard Tips for P10 multi" and "Uploaded CSV Copy of Sample Manifest" parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76ba23-pcr2
