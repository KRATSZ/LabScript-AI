# Nextera XT DNA Library Prep Kit Protocol: Part 3/4 - Normalize Libraries

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Featured
     * NGS Library Prep: Illumina Nextera XT

## Description
Part 3 of 4: Normalize Libraries

Links:
* [Part 1: Tagment and Amplify](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)
* [Part 3: Normalize Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)
* [Part 4: Pool Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part4)

With this protocol, your robot can perform the Nextera XT DNA Library Prep Kit protocol describe by the [Illumina Reference Guide](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-06.pdf).

This is part 3 of the protocol, which is step (4) of the overall workflow: normalize libraries. This step normalizes the concentration of each library to ensure correct library representation in the donwstream pooled libraries.

It is safe to stop after this step and re-start work at a later point. If you are stopping, seal the plate and store at -25°C to -15°C for up to seven days.

--
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 or P50 Pipette (Single or 8-Channel)](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Bio-Rad 96-Well Plate, 200μl](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr) containing samples from [Part 1](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)
* [Bio-Rad 96-Well Plate, 200μl](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr), clean and empty (x2)
* [USA Scientific 12-Channel Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* [Nextera XT DNA Library Prep Kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-xt-dna.html)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

This protocol requires specific labware in a specific set-up.

Slot 1: [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (clean and empty); final elution will be transferred to this plate.

Slot 2: [USA Scientific 12-Channel Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* A1: Library Normalization Additive 1 (LNA1)
* A2: Library Normalization Beads 1 (LNB1)
* A3: Library Normalization Wash 1 (LNW1)
* A4: Library Normalization Storage Buffer 1 (LNS1)
* A5: 0.1 N NaOH
* A6: Empty - LNA1 & LNB1 will be combined here, if not pre-mixed
* A12: Liquid Waste

Slot 4: [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (clean and empty)

Slot 5: [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr) containing samples from [Part 2](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)

Slot 7: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 8: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 9: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


Using the customization fields below, set up your protocol.
* Pipette Model: Select which pipette (P50/P300) you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right).
* Number of Samples: Select the number of samples (1-96) to be run in the protocol. NOTE ~ selecting 24 or less samples will result in only the top-left corner of the plates being used (A1 - D6).
* Mix LNA1 & LNB1 with OT-2: Select whether the OT-2 should mix the LNA1 or LNB1 together. If **yes**, the OT-2 will transfer the reagents from A1 and A2 of the reservoir, respectively, and mix in A6. Otherwise, the pre-mixed reagent should be loaded directly in A6 of the 12-well reservoir.



### Robot
* [OT 2](https://opentrons.com/ot-2)

### Modules
* [Magnetic Module](https://opentrons.com/modules)

### Reagents
* [Nextera XT DNA Library Prep Kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-xt-dna.html)

## Process
1. Select all desired settings according to the “Setup” section above to customize your protocol run.
NOTE ~ "Number of Samples" should be the same as [Part 1](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1) and [Part 2](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)
2. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
3. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
4. Make sure to add reagents to your labware before placing it on the deck! Your reagents should be in your reservoir, and the samples you’re starting with should be in your plate in slot 5 on the deck.


### Additional Notes
If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
bU7eUGEh
872
