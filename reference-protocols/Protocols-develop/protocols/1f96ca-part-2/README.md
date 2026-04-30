# NGS Library Prep: KAPA Hyper Plus 96rx, cat 07962428001 ROCHE - part 2 of 2 - Library Clean Up and Pooling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * KAPA Hyper Plus 96rx, cat 07962428001 ROCHE

## Description
Part 2 of 2: Library Clean Up and Pooling

Links:
* [Part 1: Fragmentation, End Repair, Adapter Ligation, Library Amplification](http://protocols.opentrons.com/protocol/1f96ca)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/1f96ca-part-2)

With this protocol, your robot can perform the ROCHE KAPA HyperPlus NGS library prep protocol described by the [KAPA HyperPlus Kit](https://www.n-genetics.com/products/1104/1023/17277.pdf).

This is part 2 of the protocol, which includes the steps (1) bead clean up (2) pooling.

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [KAPA Hyper Plus 96rx, cat 07962428001 ROCHE](https://www.n-genetics.com/products/1104/1023/17277.pdf)

## Protocol Steps

Set up: Add reagent strip tubes to the aluminum block during the protocol run as indicated in comments displayed during pauses in the protocol run. Place post-PCR plate in deck slot 1.

The OT-2 will perform the following steps:
1. Perform bead clean up of amplified libraries.
2. Pool the libraries.

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
* Opentrons Magnetic Module (Deck Slot 9)
* Opentrons p300 tips (Deck Slots 10, 11)
* Opentrons p20 tips (Deck Slots 3, 4, 7, 8)
* opentrons_96_aluminumblock_generic_pcr_strip_200ul (Deck Slot 5) with
beads, water, intermediate_pools in columns 1-3
* post-PCR plate (Deck Slot 1)
* nest_12_reservoir_15ml (Deck Slot 2)
* pool tube and tube rack (Deck Slot 6) with pool tube in A1

## Process
1. Input your number of samples.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

###### Internal
1f96ca
