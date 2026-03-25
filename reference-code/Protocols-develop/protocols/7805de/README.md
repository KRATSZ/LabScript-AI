# NEBNext Ultra II Directional RNA Library Prep Kit for Illumina with Poly(A) Selection: Part 1 of 4: RNA Isolation, Fragmentation and Priming

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II Directional Library Prep Kit for Illumina

## Description
Part 1 of 4: Isolate poly(A) RNA from starting total RNA and perform fragmentation and priming in preparation for cDNA synthesis.

Links:
* [Part 1: RNA Isolation, Fragmentation and Priming](http://protocols.opentrons.com/protocol/7805de)
* [Part 2: cDNA Synthesis](http://protocols.opentrons.com/protocol/7805de-part-2)
* [Part 3: End Prep and Adapter Ligation](http://protocols.opentrons.com/protocol/7805de-part-3)
* [Part 4: PCR Enrichment](http://protocols.opentrons.com/protocol/7805de-part-4)

With this protocol, your robot can perform the NEBNext Ultra II Directional RNA Library Prep Kit for Illumina protocol described by the [NEB Instruction Manual](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-05-20/dv23jqz/NEBNext%20Ultra%20II%20Directional%20RNA%20library%20Prep%20kit%20manualE7760_E7765.pdf).

This is part 1 of the protocol: RNA Isolation, Fragmentation and Priming.

This step isolates poly(A) RNA from up to 48 total RNA samples and then fragments and primes the RNA in preparation for cDNA synthesis (occurs in part 2). This protocol follows Section 1 of the NEB Instruction Manual.

After the steps carried out in this protocol (part 1), it is best to immediately proceed with part 2: cDNA Synthesis.


## Protocol Steps

Set up and process steps: Please see pause comments displayed in the script and in the OT app.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p300 and p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Temperature Module and opentrons_96_aluminumblock_generic_pcr_strip_200ul (Deck Slot 3)
* Opentrons Magnetic Module (Deck Slot 4)
* Opentrons p300 tips (Deck Slots 6 and 9)
* Opentrons p20 tips (Deck Slots 2 and 5)
* nest_12_reservoir_15ml (Deck Slot 1)
* nest_96_wellplate_100ul_pcr_full_skirt (Deck Slot 7)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 24)" in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
7805de
