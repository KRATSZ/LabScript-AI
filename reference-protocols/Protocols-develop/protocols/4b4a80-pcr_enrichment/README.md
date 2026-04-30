# NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L: Step 4 of 4: PCR Enrichment

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L

## Description
Part 4 of 4: Enrichment, barcoding, and post-PCR clean up of size-selected DNA fragments

Links:
* [Part 1: Fragmentation](http://protocols.opentrons.com/protocol/4b4a80-fragmentation)
* [Part 2: Adapter Ligation](http://protocols.opentrons.com/protocol/4b4a80-adapter_ligation)
* [Part 3: Size Selection](http://protocols.opentrons.com/protocol/4b4a80-size_selection)
* [Part 4: PCR Enrichment](http://protocols.opentrons.com/protocol/4b4a80-pcr_enrichment)

With this protocol, your robot can perform the NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L protocol described by the [NEBNext E6177S/L](https://www.neb.com/products/e6177-nebnext-ultra-ii-fs-dna-library-prep-with-sample-purification-beads#Product%20Information). [NEB Instruction Manual for NEBNext E6177S/L](https://s3.amazonaws.com./pf-upload-01/u-4256/0/2021-02-16/8q531ae/manualE6177-E7805.pdf).

This is part 4 of the protocol: PCR enrichment

This step amplifies and barcodes the size-selected output from part 3, followed by a post-PCR cleanup.

This protocol assumes up to 24 input DNA samples of > 100 ng and follows Section 2 of the NEB Instruction Manual.

After the pcr enrichment and cleanup steps carried out in this protocol, store samples at -20 C.


## Protocol Steps

Set up: Pre-cool the temperature module to 4 degrees via settings in the Opentrons app prior to running this protocol. Add Q5 mastermix, i5, i7 and an empty vial to the 4 degree temperature module. Place 96-well plate containing post-size selection samples from part 3 (located in first three columns) on the thermocycler module.

The OT-2 will perform the following steps:
1. Combine Q5 mastermix + i5 + i7 and mix. Dispense this mixture to the size-selected samples and mix.
2. Run the PCR enrichment protocol on the thermocycler.
3. Pause (Manually move plate from cycler to magnetic module. Place vortexed beads on the temperature module and freshly prepared 80% ethanol and 0.1X TE in the reagent reservoir.)
4. Add beads, mix, engage magnets, discard supernatant, wash beads, elute, transfer eluate to fresh plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel p300 and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tips for the p20 and p300 pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons Temperature Module (Deck Slot 2)
* Opentrons p300 tips (Deck Slots 3,6,9)
* Opentrons Thermocycler Module (Deck Slots 7,8,10,11)
* Opentrons Magnetic Module (Deck Slot 4)
* Reagent reservoir (Deck Slot 5)
* Eluate plate (Deck Slot 1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 24)", "Number of PCR Enrichment Cycles" (default 3), and the "PCR labware" (magnetic module compatible plate such as "Nest 96 wellplate 100ul pcr full skirt") in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b4a80-pcr_enrichment
