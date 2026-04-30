# Illumina TruSeq Stranded mRNA Sample Prep: Part 1 of 3: mRNA Isolation and cDNA Synthesis

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * Illumina TruSeq Stranded mRNA Sample Prep

## Description

With this 3 part workflow, your OT-2 can use [Illumina TruSeq Stranded mRNA Sampe Preparation Guide](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7e3b31/stranded-mrnaTruseq.pdf) to convert 8-48 input total RNA samples into libraries having known strand origin to be used for cluster generation and DNA sequencing. This is Part 1 of 3: This OT-2 protocol uses the LT kit and follows the LS protocol found on pages 12-44 of the attached sample prep guide. Oligo-dT magnetic beads are used to isolate poly(A) RNA from input total RNA, followed by fragmentation, priming, and cDNA synthesis. The second-strand synthesis includes dUTP in order to quench the amplification of the second strand.

## Protocol Steps

This is part 1 of 3 parts: mRNA isolation and cDNA synthesis. After the steps carried out in this protocol (part 1), the double-stranded cDNA plate can be covered and stored at -20 C for up to 7 days.

Set up: Thermocycler module in deck slots 7, 8, 10 and 11. Magnetic module in deck slot 1. Reservoir nest_12_reservoir_15ml (A1 - water, A2 - bead wash, A11 - waste, A12 - 80 percent ethanol) in deck slot 2. Reagents in strip tubes on 96-well aluminum block opentrons_96_aluminumblock_generic_pcr_strip_200ul (see visual below for reagent locations) in deck slot 5. Place Opentrons 20 uL filter tips opentrons_96_filtertiprack_20ul in deck slot 3 and Opentrons 200 uL filter tips opentrons_96_filtertiprack_200ul in deck slots 6 and 9.

The OT-2 will perform the following steps using the p20 multi, p300 multi, Thermocycler Module and Magnetic Module:
1. Mix water, input total RNA and oligo-dT magnetic beads. Denature and bind RNA.
2. Pellet and wash beads. Elute.
3. Rebind, second elution with fragmention, priming, synthesis of first cDNA strand.
4. Second strand synthesis and cleanup with Ampure XP magnetic beads.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons p20 and p300 Multi-Channel Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7e3b31/deck_map.png)

![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7e3b31/reservoir.png)

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7e3b31/reagents.png)

* Opentrons 20ul filter tips (deck slot 3)
* Opentrons 200ul filter tips (deck slots 6, 9)
* Opentrons Thermocycler Module (deck slots 7, 8, 10, 11)
* Opentrons Magnetic Module (deck slot 1)
* Sample Plate nest_96_wellplate_100ul_pcr_full_skirt (deck slot 4)
* Reagents opentrons_96_aluminumblock_generic_pcr_strip_200ul (deck slot 5)
* Reservoir nest_12_reservoir_15ml (deck slot 2)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameters on this page to make any needed adjustments to the volume of input RNA to be mixed with oligo-dT beads, the number of input RNA samples, well bottom clearances etc, time to engage magnets or dry beads.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7e3b31
