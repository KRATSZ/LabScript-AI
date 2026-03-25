# ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 2 of 4: cDNA Synthesis

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Custom

## Description

With this 4 part workflow, the OT-2 will follow [ArcBio Continuous RNA Workflow - Pre-PCR Instrument experimental protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2022-01-06/0h134y4/ArcBio_RNA_Workflow_Continuous.xlsx) to convert up to 96 input RNA samples into cDNA libraries. This is Part 2 of 4: This OT-2 protocol uses the RNA Continuous Workflow, Pre-PCR Instrument section of attached experimental protocol to perform cDNA synthesis.

## Protocol Steps

This is part 2 of 4 parts: cDNA Synthesis. After the steps carried out in this protocol (part 2), proceed to run the cDNA Library Purification, Library Prep protocol (Continuous RNA Workflow - Pre-PCR Instrument: Part 3 - cDNA Library Purification, Library Prep).

Links:
* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 1 of 4: DNase Digestion](https://protocols.opentrons.com/protocol/43d313)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 2 of 4: cDNA Synthesis](https://protocols.opentrons.com/protocol/43d313-part-2)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 3 of 4: cDNA Library Purification, Library Prep](https://protocols.opentrons.com/protocol/43d313-part-3)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: Part 4 of 4: cDNA Library Purification, Ligation](https://protocols.opentrons.com/protocol/43d313-part-4)

Set up: If using a custom deep well plate (one that is not listed in the [Opentrons Labware Library](https://labware.opentrons.com/) ) , a user-determined engage height must be provided as a parameter value (see protocol parameters below). In advance, prior to running the protocol, place temperature module in deck slot 3 and use settings in the OT App to pre-cool the temperature module to 4 degrees C. Place sample plate opentrons_96_aluminumblock_biorad_wellplate_200ul from step 1 on the aluminum block on the temperature module. Magnetic module in deck slot 1 with deep well plate. Reservoir nest_12_reservoir_15ml in deck slot 5 (A1-A3 - 9.6 mL beads, A12 - Tris). Reagents in strip tubes on 96-well aluminum block opentrons_96_aluminumblock_generic_pcr_strip_200ul (column 1 - EDTA, column 2 - RT Master Mix 1, column 3 - RT Master Mix 2) in deck slot 2. Reservoirs nest_1_reservoir_195ml in deck slots 4 and 6 (slot 6 - 144 mL 80 percent ethanol, slot 4 - waste). Place Opentrons 20 uL tips opentrons_96_tiprack_20ul in deck slots 10, 11 and Opentrons 300 uL tips opentrons_96_tiprack_300ul in deck slots 7, 8, 9.

The OT-2 will perform the following steps using the p20 multi- and p300 multi-channel pipettes, temperature module and magnetic module:
1. Mix EDTA with input samples from step 1 and transfer them to the deep well plate on the magnetic module.
2. Bead cleanup and elution with Tris.
3. Combine RT Master Mix 1 and eluted sample. Pause for off-deck thermocycler steps.
4. Add RT Master Mix 2. Pause for off-deck thermocycler steps.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/part2layout.png)

* Opentrons 20ul tips (deck slots 10, 11)
* Opentrons 300ul tips (deck slots 7, 8, 9)
* Opentrons Temperature Module (deck slot 3) with Sample Plate opentrons_96_aluminumblock_biorad_wellplate_200ul
* Opentrons Magnetic Module (deck slot 1) with deep well plate
* Reservoirs nest_1_reservoir_195ml (deck slots 4, 6)
* Reagents opentrons_96_aluminumblock_generic_pcr_strip_200ul (deck slot 2)
* Reservoir nest_12_reservoir_15ml (deck slot 5)

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/part2reagentblock.png)

![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/43d313/part2reservoir.png)

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
43d313-part-2
