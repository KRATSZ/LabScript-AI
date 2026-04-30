# ArcBio Continuous DNA Workflow - Pre-PCR Instrument: DNA-PRE-PCR-3 Library Purification Indexing

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Custom

## Description

With this 6 part workflow, the OT-2 will follow [ArcBio Continuous DNA Workflow - Pre-PCR Instrument experimental protocol and Post-PCR Instrument experimental protocol](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/78d33c/ArcBio_DNA_Workflow_020822.xlsx) to convert up to 96 input DNA samples into DNA libraries. This is Part 3 of 6: This OT-2 protocol uses the DNA Continuous Workflow, Pre-PCR Instrument section of attached experimental protocol to perform library purification and indexing.

## Protocol Steps

This is part 3 of 6 parts: Library Purification Indexing. After the steps carried out in this protocol (part 3), proceed to run the first post-PCR instrument protocol Purification Post Indexing (Continuous DNA Workflow - Post-PCR Instrument: DNA-POST-PCR-1 - Purification Post Indexing).

Links:
* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: DNA-PRE-PCR-1 DNA Concentration Fragmentation](https://protocols.opentrons.com/protocol/78d33c)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: DNA-PRE-PCR-2 DNA Library Prep - Adapter Ligation](https://protocols.opentrons.com/protocol/78d33c-part-2)

* [ArcBio Continuous RNA Workflow - Pre-PCR Instrument: DNA-PRE-PCR-3 Library Purification Indexing](https://protocols.opentrons.com/protocol/78d33c-part-3)

* [ArcBio Continuous DNA Workflow - Post-PCR Instrument: DNA-POST-PCR-1 Library Purification Post-Indexing](https://protocols.opentrons.com/protocol/78d33c-part-4)

* [ArcBio Continuous DNA Workflow - Post-PCR Instrument: DNA-POST-PCR-2 Post-Indexing](https://protocols.opentrons.com/protocol/78d33c-part-5)

* [ArcBio Continuous DNA Workflow - Post-PCR Instrument: DNA-POST-PCR-3 Library Purification](https://protocols.opentrons.com/protocol/78d33c-part-6)

Set up: If using a custom deep well plate (one that is not listed in the [Opentrons Labware Library](https://labware.opentrons.com/) ) , a user-determined engage height must be provided as a parameter value (see protocol parameters below). In advance, prior to running the protocol, place temperature module in deck slot 3 and use settings in the OT App to pre-cool the temperature module to 4 degrees C. Place sample plate opentrons_96_aluminumblock_biorad_wellplate_200ul from step 1 on the aluminum block on the temperature module. Magnetic module in deck slot 1 with deep well plate. Reservoir nest_12_reservoir_15ml in deck slot 5 (A1-A3 - 9.6 mL beads, A12 - Tris). Reagents in strip tubes on 96-well aluminum block opentrons_96_aluminumblock_generic_pcr_strip_200ul (column 1 - EDTA, column 2 - RT Master Mix 1, column 3 - RT Master Mix 2) in deck slot 2. Reservoirs nest_1_reservoir_195ml in deck slots 4 and 6 (slot 6 - 144 mL 80 percent ethanol, slot 4 - waste). Place Opentrons 20 uL tips opentrons_96_tiprack_20ul in deck slots 10, 11 and Opentrons 300 uL tips opentrons_96_tiprack_300ul in deck slots 7, 8, 9.

The OT-2 will perform the following steps using the p20 multi- and p300 multi-channel pipettes, temperature module and magnetic module:
1. Add Tris to samples on the magnetic module.
2. Bead cleanup.
3. Combine index pair and eluted sample at 4 degrees on the temperature module.
4. Add enzyme 16.

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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/78d33c/screenshot+layout+dna-3.png)

* Opentrons 20ul tips (deck slots 10, 11)
* Opentrons 300ul tips (deck slots 7, 8, 9)
* Opentrons Temperature Module (deck slot 3) with Sample Plate opentrons_96_aluminumblock_biorad_wellplate_200ul
* Opentrons Magnetic Module (deck slot 1) with deep well plate
* Reservoirs nest_1_reservoir_195ml (deck slots 4, 6)
* Reagents opentrons_96_aluminumblock_generic_pcr_strip_200ul (deck slot 2)
* Reservoir nest_12_reservoir_15ml (deck slot 5)

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/78d33c/screenshot+reagents+dna-3.png)

![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/78d33c/screenshot+reservoir+dna-3.png)

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
78d33c-part-3
