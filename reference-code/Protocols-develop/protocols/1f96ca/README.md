# NGS Library Prep: KAPA Hyper Plus 96rx, cat 07962428001 ROCHE - part 1 of 2 - Fragmentation, End Repair, Adapter Ligation, Library Amplification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * KAPA Hyper Plus 96rx, cat 07962428001 ROCHE

## Description
Part 1 of 2: Fragmentation, End Repair, Adapter Ligation, Library Amplification

Links:
* [Part 1: Fragmentation, End Repair, Adapter Ligation, Library Amplification](http://protocols.opentrons.com/protocol/1f96ca)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/1f96ca-part-2)

With this protocol, your robot can perform the ROCHE KAPA HyperPlus NGS library prep protocol described by the [KAPA HyperPlus Kit](https://www.n-genetics.com/products/1104/1023/17277.pdf).

This is part 1 of the protocol, which includes the steps (1) enzymatic DNA fragmentation (2) end repair and A-tailing (3) adapter ligation and (4) library amplification.

The double stranded DNA fragments are end-repaired to generate 5'-phosphorylated, 3'-dA-tailed dsDNA. dsDNA adapters with 3'-dTMP overhangs are ligated to the 3'-dA-tailed DNA. These steps are followed by PCR amplification of the libraries.

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [KAPA Hyper Plus 96rx, cat 07962428001 ROCHE](https://www.n-genetics.com/products/1104/1023/17277.pdf)

## Protocol Steps

Set up: Pre-cool the thermocycler block to 4 degrees via settings in the Opentrons app prior to running this protocol. Add reagent strip tubes to the aluminum block during the protocol run as indicated in comments displayed during pauses in the protocol run. Place DNA sample plate in deck slot 1.

The OT-2 will perform the following steps:
1. Combine Frag-MM and DNA and incubate at 37 degrees. Add ERAT-MM and incubate at 65 degrees. Add Liga-MM and incubate 20 degrees. Perform post-ligation clean up. Combine KAPA mix, purified library, P7 and P5.
2. Run PCR steps on the thermocycler module.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 and p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Thermocycler Module (Deck Slots 7, 8, 10, 11)
* Opentrons Magnetic Module (Deck Slot 9)
* Opentrons p300 tips (Deck Slot 4)
* Opentrons p20 tips (Deck Slots 3, 6)
* opentrons_96_aluminumblock_generic_pcr_strip_200ul (Deck Slot 5) with
frag_mm, erat_mm, liga_mm, beads, water, kapa mix in columns 1-6
* DNA sample plate (Deck Slot 1)
* nest_12_reservoir_15ml (Deck Slot 2)

## Process
1. Input your number of samples.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

###### Internal
1f96ca
