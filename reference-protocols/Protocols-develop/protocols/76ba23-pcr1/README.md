# NGS Library Prep for Targeted Sequencing of DNA Methylation Patterns in Cell-Free DNA: Step 3 of 5: PCR 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Zymoresearch: EZ DNA Methylation-Gold Kit

## Description
Part 3 of 5: Bisulfite converted DNA (output from step 2) is set up for a PCR amplification step. For plasma samples (but not saliva) the protocol includes post-PCR clean up steps.

Links:
* [Part 1: DNA Extraction](http://protocols.opentrons.com/protocol/76ba23)
* [Part 2: Bisulfite Conversion](http://protocols.opentrons.com/protocol/76ba23-bisulfite_conversion)
* [Part 3: PCR1](http://protocols.opentrons.com/protocol/76ba23-pcr1)
* [Part 4: PCR2](http://protocols.opentrons.com/protocol/76ba23-pcr2)
* [Part 5: Pooling](http://protocols.opentrons.com/protocol/76ba23-pooling)

With this work flow, your robot will use reagents from the Zymoresearch EZ DNA Methylation-Gold Kit [Zymoresearch EZ DNA Methylation-Gold Kit](https://www.zymoresearch.com/collections/ez-dna-methylation-gold-kits) to perform the custom steps (DNA extraction, Bisulfite Conversion, PCR1, PCR2, Pooling) detailed in the HKG SOP.[HKG SOP](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-04/vw23kchHKG%20Standard%20Operating%20Procedure%20for%20DNA%20extraction%20Targeted%20next%20generation%20sequencing%20and%20.xlsx).

This is part 3 of the work flow: Bisulfite Conversion.

This step performs set up for PCR amplification (with additional post-PCR clean up steps for plasma samples only) using the output samples from step 2 (Bisulfite Conversion).

After the steps carried out in this protocol (part 3), proceed with part 4: PCR2.


## Protocol Steps

Set up: Place bisulfite-converted DNA samples (output from Bisulfite Conversion in step 2), pcr1 master mix, beads, water, magnetic module and tips on the OT-2 deck.  

The OT-2 will perform the following steps:
1. Distribute sample and pcr1 master mix to the PCR plate.
2. Pause for the following steps (OT-2 deck lights will signal pauses):

           Thermocycling steps (outside of the OT-2).

           Replenish tips.

3. (Plasma only) Bead clean up, elute and transfer eluate to fresh PCR plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Magnetic Module (Deck Slot 4)
* Opentrons p300 tips (Deck Slots 6, 9, 8, 11)
* 96 samples from step 2 ("nest_96_wellplate_100ul_pcr_full_skirt" Deck slot 1)
* pcr1 master mix ("corning_96_wellplate_360ul_flat" Deck slot 3)
* trough for beads, water, waste ("nest_12_reservoir_15ml" Deck slot 5)
* pcr plate ("nest_96_wellplate_100ul_pcr_full_skirt" Deck slot 2)
* reservoir for ethanol ("nest_1_reservoir_195ml" Deck slot 7)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Choose Filtered or Standard Tips for P300 multi" and "Uploaded CSV Copy of Sample Manifest" parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76ba23-pcr1
