# ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 4 of 4: cDNA Library Purification, Ligation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Custom

## Description

With this 4 part workflow, the OT-2 will follow [ArcBio Continuous RNA Workflow - Pre-PCR Instrument experimental protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-06/0h134y4/ArcBio_RNA_Workflow_Continuous.xlsx) to convert up to 96 input RNA samples into cDNA libraries. This is Part 4 of 4: This OT-2 protocol uses the RNA Continuous Workflow, Pre-PCR Instrument section of attached experimental protocol to perform Library Purification, Ligation.

## Protocol Steps

This is part 4 of 4 parts: cDNA Library Purification, Library Prep. After the steps carried out in this protocol (part 4), proceed to run Continuous RNA Workflow - Post-PCR Instrument: Part 1.

Links:
* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 1 of 4: DNase Digestion](https://protocols.opentrons.com/protocol/43d313)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 2 of 4: cDNA Synthesis](https://protocols.opentrons.com/protocol/43d313-part-2)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 3 of 4: cDNA Library Purification, Library Prep](https://protocols.opentrons.com/protocol/43d313-part-3)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 4 of 4: cDNA Library Purification, Ligation](https://protocols.opentrons.com/protocol/43d313-part-4)

Set up: In advance, prior to running the protocol, place temperature module in deck slot 3 and use settings in the OT App to pre-cool the temperature module to 4 degrees C. Place sample plate opentrons_96_aluminumblock_biorad_wellplate_200ul from step 1 on the aluminum block on the temperature module. Magnetic module in deck slot 1 with biorad_96_wellplate_200ul_pcr 200 uL 96 well PCR plate. Reservoir nest_12_reservoir_15ml in deck slot 5 (A1 - beads, A12 - Tris). Reagents in 200 uL BioRad PCR plate on 96-well aluminum block biorad_96_wellplate_200ul_pcr (earlier step - index plate, later step - enzyme 16 plate) in deck slot 2. Reservoirs nest_1_reservoir_195ml in deck slots 4 and 6 (slot 6 - 80 percent ethanol, slot 4 - waste). Place Opentrons 20 uL tips opentrons_96_tiprack_20ul in deck slots 10, 11 and Opentrons 300 uL tips opentrons_96_tiprack_300ul in deck slots 7, 8, 9.

The OT-2 will perform the following steps using the p20 multi- and p300 multi-channel pipettes, temperature module and magnetic module:
1. Bead cleanup and elution with Tris.
2. Combine index and eluted sample.
3. Add enzyme 16. Pause for off-deck thermocycler steps.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/part4layout.png)

* Opentrons 20ul tips (deck slots 10, 11)
* Opentrons 300ul tips (deck slots 7, 8, 9)
* Opentrons Temperature Module (deck slot 3) with Sample Plate opentrons_96_aluminumblock_biorad_wellplate_200ul
* Opentrons Magnetic Module (deck slot 1) with deep well plate
* Reservoirs nest_1_reservoir_195ml (deck slots 4, 6)
* Reagents opentrons_96_aluminumblock_biorad_wellplate_200ul (deck slot 2)
* Reservoir nest_12_reservoir_15ml (deck slot 5)

![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/part4reservoir.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameters on this page to make any needed adjustments to the number of samples, well bottom clearances, engage height and time for the deep well plate on the magnetic module, the magnitude of the move used to target and avoid the bead pellet, number of minutes for bead drying.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
43d313-part-4
