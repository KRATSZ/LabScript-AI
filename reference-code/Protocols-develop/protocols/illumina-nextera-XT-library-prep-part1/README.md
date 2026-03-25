# Nextera XT DNA Library Prep Kit Protocol: Part 1/4 - Tagment Genomic DNA and Amplify Libraries

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Featured
     * NGS Library Prep: Illumina Nextera XT

## Description
Part 1 of 4: Tagment Genomic DNA and Amplify Libraries

Links:
* [Part 1: Tagment and Amplify](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)
* [Part 3: Normalize Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)
* [Part 4: Pool Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part4)

With this protocol, your robot can perform the Nextera XT DNA Library Prep Kit protocol described by the [Illumina Reference Guide](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-06.pdf).

This is part 1 of the protocol, which includes the steps (1) Tagment Genomic DNA and (2) Amplify Libraries.

The tagmentation step uses Nextera transposase to fragment DNA into sizes suitable for sequencing, and then tags the DNA with adapter sequences. The library amplification step increases the yield of the tagmented DNA using PCR. PCR adds the Index 1 (i7), Index 2 (i5), and full adapter sequences to the tagmented DNA from the previous step. This protocol assumes you are taking your plate off the OT-2 and thermocycling on a stand-alone PCR machine according to the [Illumina Reference Guide](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-05.pdf).

After the two steps carried out in this protocol, you can safely stop work and return to it at a later point. If you are stopping, seal the plate and store at 2°C to 8°C for up to 2 days.

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [Nextera XT DNA Library Prep Kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-xt-dna.html)

## Process
1. Input your number of samples.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
* 2-mL Tuberack Reagent Setup:
    * Amplicon Tagment Mix: **A1**
    * Tagment DNA Buffer: **B1**
    * Neutralize Tagment Buffer: **C1**
    * Nextera PCR Master Mix: **D1**
* Review the reference guide before proceeding to confirm kit contents and make sure you have the required equipment and consumables.

## Preview
With this series of protocols and the [Opentrons Magnetic Module](https://shop.opentrons.com/products/magdeck), your robot can complete a library prep using the [Illumina Nextera XT DNA Library Prep Kit](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-03.pdf). This library prep protocol comes in four parts: Tagment and Amplify, Clean Up Libraries, Normalize Libraries, and Pool Libraries.

###### Internal
bU7eUGEh
872
