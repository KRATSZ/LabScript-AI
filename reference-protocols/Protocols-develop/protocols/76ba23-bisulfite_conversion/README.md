# NGS Library Prep for Targeted Sequencing of DNA Methylation Patterns in Cell-Free DNA: Step 2 of 5: Bisulfite Conversion

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Zymoresearch: EZ DNA Methylation-Gold Kit

## Description
Part 2 of 5: Cell-free DNA (output from step 1) is chemically treated to convert unmethylated cytosine (C to T) in order to reveal patterns of methylated cytosine by DNA sequencing (methylated cytosine is protected and remains unchanged). This bisulfite conversion is followed by bead-clean up, elution, and transfer of the eluate to a fresh PCR plate.

Links:
* [Part 1: DNA Extraction](http://protocols.opentrons.com/protocol/76ba23)
* [Part 2: Bisulfite Conversion](http://protocols.opentrons.com/protocol/76ba23-bisulfite_conversion)
* [Part 3: PCR1](http://protocols.opentrons.com/protocol/76ba23-pcr1)
* [Part 4: PCR2](http://protocols.opentrons.com/protocol/76ba23-pcr2)
* [Part 5: Pooling](http://protocols.opentrons.com/protocol/76ba23-pooling)

With this protocol, your robot will use reagents from the Zymoresearch EZ DNA Methylation-Gold Kit [Zymoresearch EZ DNA Methylation-Gold Kit](https://www.zymoresearch.com/collections/ez-dna-methylation-gold-kits) to perform the custom steps (DNA extraction, Bisulfite Conversion, PCR1, PCR2, Pooling) detailed in the HKG SOP.[HKG SOP](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-03-04/vw23kchHKG%20Standard%20Operating%20Procedure%20for%20DNA%20extraction%20Targeted%20next%20generation%20sequencing%20and%20.xlsx).

This is part 2 of the protocol: Bisulfite Conversion.

This step performs the bisulfite conversion and bead-clean up steps using the output samples from step 1 (DNA extraction).

After the steps carried out in this protocol (part 2), proceed with part 3: PCR1.


## Protocol Steps

Set up: Place cell free DNA samples (output from DNA Extraction in step 1), CT conversion reagent, beads, water, wash, magnetic module, waste reservoir, elution plate and tips on the OT-2 deck.  

The OT-2 will perform the following steps:
1. Distribute cell-free DNA and CT conversion buffer to the PCR plate.
2. Pause for the following steps (OT-2 deck lights will signal pauses):

           Thermocycling steps (outside of the OT-2).

           Replenish tips.

           55 degree incubations (outside of the OT-2) to dry beads and elute.

3. Desulphonation, bead clean up, elute and transfer eluate to fresh PCR plate.

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
* Opentrons p300 tips (Deck Slots 6 and 9)
* 96 cell free DNA samples ("nest_96_wellplate_100ul_pcr_full_skirt" Deck slot 1)
* pcr plate for CT conversion ("biorad_96_wellplate_200ul_pcr" Deck slot 2)
* reservoir for CT conv buffer, beads, water ("nest_12_reservoir_15ml" Deck slot 5)
* reservoir for wash ("nest_1_reservoir_195ml" Deck slot 5)
* reservoir for desulph buffer ("nest_1_reservoir_195ml" Deck slot 8)
* pcr plate for eluate ("nest_96_wellplate_100ul_pcr_full_skirt" Deck slot 10)
* reservoir for waste ("agilent_1_reservoir_290ml" Deck slot 11)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Choose Filtered or Standard Tips for P300 multi" parameter below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76ba23-bisulfite_conversion
