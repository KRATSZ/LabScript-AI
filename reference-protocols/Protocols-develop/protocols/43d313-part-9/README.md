# ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 9 of 9: Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Custom

## Description

With this 9 part workflow, the OT-2 will follow [ArcBio Continuous RNA Workflow - Pre-PCR Instrument and Post-PCR Instrument experimental protocol](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/ArcBio_RNA_Workflow_020922.xlsx) to convert up to 96 input RNA samples into cDNA libraries. This is Part 9 of 9: This OT-2 protocol uses the RNA Continuous Workflow, Post-PCR Instrument section of attached experimental protocol to perform pooling steps.

## Protocol Steps

This is part 9 of 9 parts: Pooling.

Links:
* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 1 of 9: DNase Digestion](https://protocols.opentrons.com/protocol/43d313)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 2 of 9: cDNA Synthesis](https://protocols.opentrons.com/protocol/43d313-part-2)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 3 of 9: cDNA Library Purification, Library Prep](https://protocols.opentrons.com/protocol/43d313-part-3)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 4 of 9: cDNA Library Purification, Ligation](https://protocols.opentrons.com/protocol/43d313-part-4)

* [ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 5 of 9: RNA-POST-PCR-1 Post Indexing](https://protocols.opentrons.com/protocol/43d313-part-5)

* [ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 6 of 9: RNA-POST-PCR-2 Post Indexing Purification](https://protocols.opentrons.com/protocol/43d313-part-6)

* [ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 7 of 9: RNA-POST-PCR-3 Library Purification](https://protocols.opentrons.com/protocol/43d313-part-7)

* [ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 8 of 9: Library QC](https://protocols.opentrons.com/protocol/43d313-part-8)

* [ArcBio Continuous RNA Workflow - Post-PCR Instrument: Part 9 of 9: Pooling](https://protocols.opentrons.com/protocol/43d313-part-9)

* [example csv for Pooling](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/example_csv.csv)

Set up: Use settings in the Opentrons app prior to running this protocol to pre-cool the Temperature Module (deck slot 3) to 4 degrees C. Place Twin Tec 200 uL PCR plate with libraries on the Temperature Module. Place the Opentrons 24-tube rack with four 1.5 mL eppendorf tubes (in A1-A4 for pools 1-4) in deck slot 2. Place Opentrons 20 uL filter tips opentrons_96_filtertiprack_20ul in deck slot 10.

The OT-2 will perform the following steps using the p20 single-channel pipette and temperature module:
1. Use the p20 single to transfer the specified volume (specified in the uploaded csv file) of each library to one of the four pool tubes (3 source columns = 24 libraries per pool).
---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 and p300 Multi-Channel Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/screenshot+deck-9.png)

* Opentrons 20ul filter tips (deck slot 10)
* Opentrons Temperature Module at 4 degrees C (deck slot 3) with libraries in 200 uL PCR plate
* Rack for pool tubes Opentrons 24-tube rack with 1.5 mL eppendorf snap cap tubes (deck slot 2)

![example csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/screenshot+example+csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameters on this page to make any needed adjustments.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
43d313-part-9
