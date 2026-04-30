# NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L: Step 3 of 4: Size Selection

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L

## Description
Part 3 of 4: Size select and clean up the adapter-ligated and User-enzyme-treated DNA fragments (the output from Part 2).

Links:
* [Part 1: Fragmentation](http://protocols.opentrons.com/protocol/4b4a80-fragmentation)
* [Part 2: Adapter Ligation](http://protocols.opentrons.com/protocol/4b4a80-adapter_ligation)
* [Part 3: Size Selection](http://protocols.opentrons.com/protocol/4b4a80-size_selection)
* [Part 4: PCR Enrichment](http://protocols.opentrons.com/protocol/4b4a80-pcr_enrichment)

With this protocol, your robot can perform the NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L protocol described by the [NEBNext E6177S/L](https://www.neb.com/products/e6177-nebnext-ultra-ii-fs-dna-library-prep-with-sample-purification-beads#Product%20Information). [NEB Instruction Manual for NEBNext E6177S/L](https://s3.amazonaws.com./pf-upload-01/u-4256/0/2021-02-16/8q531ae/manualE6177-E7805.pdf).

This is part 3 of the protocol: Size Selection

This step size-selects and cleans up the sample output from part 2 to obtain a specific insert size range of 350-600 bp. Choose pcr labware compatible with the Opentrons Magnetic Module such as "(Magnetic Module compatible) Nest 96 wellplate 100ul pcr full skirt" using the parameters below.

This protocol assumes up to 24 input DNA samples of > 100 ng and follows Section 2 of the NEB Instruction Manual.

After the size selection and cleanup steps carried out in this protocol (part 3), proceed with part 4: PCR enrichment, or seal the plate and store at -20 C.


## Protocol Steps

Set up: Pre-cool the temperature module to 4 degrees via settings in the Opentrons app prior to running this protocol. Add vortexed SPRI beads to the 4 degree temperature module and add water, freshly-prepared 80% ethanol, and 0.1X TE to the reagent reservoir. Place 96-well plate containing adapter-ligated and User-treated DNA samples from part 2 (located in first three columns) on the magnetic module.

The OT-2 will perform the following steps:
1. Add water to the samples on the magnetic module to bring volumes to 100 ul and mix.
2. Add 1st SPRI beads to samples for 0.2X right-side selection and mix.
3. With magnets engaged, transfer supernatants to a fresh 96-well plate on the OT-2 deck.
4. Pause: (manually remove plate with bead pellets, move sup plate to magnetic module).
5. Add 2nd SPRI beads for 0.375X left-side selection and mix.
6. With magnets engaged, transfer supernatants to trash.
7. Wash beads 2X with 80% ethanol, elute and transfer 15 ul eluate to fresh 96-well plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 and Single-Channel p20 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Temperature Module (Deck Slot 2)
* Opentrons p300 tips (Deck Slots 6,9)
* Opentrons p20 tips (Deck Slot 3)
* Opentrons Magnetic Module (Deck Slot 4)
* Reagent Reservoir (Deck Slot 5)
* Supernatant Plate (Deck Slot 7)
* Eluate Plate (Deck Slot 1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 24)" and the "PCR labware" (magnetic module compatible plate needed) in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b4a80-size_selection
