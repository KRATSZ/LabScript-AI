# NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L: Step 2 of 4: Adapter Ligation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L

## Description
Part 2 of 4: Adapter ligation and User enzyme treatment.

Links:
* [Part 1: Fragmentation](http://protocols.opentrons.com/protocol/4b4a80-fragmentation)
* [Part 2: Adapter Ligation](http://protocols.opentrons.com/protocol/4b4a80-adapter_ligation)
* [Part 3: Size Selection](http://protocols.opentrons.com/protocol/4b4a80-size_selection)
* [Part 4: PCR Enrichment](http://protocols.opentrons.com/protocol/4b4a80-pcr_enrichment)

With this protocol, your robot can perform the NEBNext Ultra II FS DNA Library Prep Kit for Illumina E6177S/L protocol described by the [NEBNext E6177S/L](https://www.neb.com/products/e6177-nebnext-ultra-ii-fs-dna-library-prep-with-sample-purification-beads#Product%20Information). [NEB Instruction Manual for NEBNext E6177S/L](https://s3.amazonaws.com./pf-upload-01/u-4256/0/2021-02-16/8q531ae/manualE6177-E7805.pdf).

This is part 2 of the protocol: Adapter Ligation.

This step performs the ligation with the NEBNext Adaptor followed by U excision.

This protocol assumes up to 24 input DNA samples of > 100 ng and follows Section 2 of the NEB Instruction Manual.

After the ligation and user enzyme steps carried out in this protocol (part 2), samples may be held overnight at -20 C before proceeding with part 3: Size Selection. If you are stopping, seal the plate and store at -20 C.


## Protocol Steps

Set up: Pre-cool the temperature module to 4 degrees via settings in the Opentrons app prior to running this protocol. Add ligation mastermix, ligation enhancer, ligation adapter, and an empty vial to the 4 degree temperature module. Place the 96-well plate containing the fragmented DNA samples (the output from part 1, located in first three columns) on the thermocycler module.

The OT-2 will perform the following steps:
1. Combine ligation mastermix + ligation enhancer + ligation adapter. Dispense this mixture to the fragmented DNA samples and mix.
2. Run the adapter ligation protocol on the thermocycler.
3. Add User enzyme to each post-ligation sample and mix.
4. Run the User enzyme treatment protocol on the thermocycler.

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
1. Set the "Sample Count (up to 24)" and the "PCR labware" in the parameters below.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b4a80-adapter_ligation
