# NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L: Step 1 of 4: Fragmentation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L

## Description
Part 1 of 4: Fragment genomic DNA and prepare ends for adapter ligation.

Links:
* [Part 1: Fragmentation](http://protocols.opentrons.com/protocol/4b4a80-fragmentation)
* [Part 2: Adapter Ligation](http://protocols.opentrons.com/protocol/4b4a80-adapter_ligation)
* [Part 3: Size Selection](http://protocols.opentrons.com/protocol/4b4a80-size_selection)
* [Part 4: PCR Enrichment](http://protocols.opentrons.com/protocol/4b4a80-pcr_enrichment)

With this protocol, your robot can perform the NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L protocol described by the [NEBNext E6177S/L](https://www.neb.com/products/e6177-nebnext-ultra-ii-fs-dna-library-prep-with-sample-purification-beads#Product%20Information). [NEB Instruction Manual for NEBNext E6177S/L](https://s3.amazonaws.com./pf-upload-01/u-4256/0/2021-02-16/8q531ae/manualE6177-E7805.pdf).

This is part 1 of the protocol: Fragmentation.

This step fragments the input DNA into a tunable size range (choose optimal size range by setting the incubation time with the "Incubation Time for Fragmentation (minutes)" parameter below following guidelines in the instruction manual) suitable for sequencing and prepares the ends for adapter ligation. This protocol assumes up to 24 input DNA samples of > 100 ng and follows Section 2 of the NEB Instruction Manual.

After the steps carried out in this protocol (part 1), it is best to immediately proceed with part 2: Adapter Ligation. If you are stopping (not recommended-a slight loss in yield may occur), seal the plate and store at -20 C.


## Protocol Steps

Set up: Pre-cool the temperature module to 4 degrees via settings in the Opentrons app prior to running this protocol. Add reaction buffer, enzyme mix, and an empty vial to the 4 degree temperature module. Place 96-well plate containing initial DNA samples (located in first three columns) on the thermocycler module.

The OT-2 will perform the following steps:
1. Combine reaction buffer + enzyme mix. Dispense this mixture to the initial DNA samples.
2. Run the fragmentation protocol on the thermocycler.

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
* Opentrons Temperature Module (Deck Slot 2)
* Opentrons p300 tips (Deck Slot 3)
* Opentrons p20 tips (Deck Slot 6)
* Opentrons Thermocycler Module (Deck Slots 7,8,10,11)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Set the "Sample Count (up to 24)", "Incubation Time for Fragmentation (minutes)", and the "PCR labware" in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b4a80-fragmentation
