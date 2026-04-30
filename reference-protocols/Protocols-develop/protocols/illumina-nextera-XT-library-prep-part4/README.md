# Nextera XT DNA Library Prep Kit Protocol: Part 4/4 - Pool Libraries

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Featured
     * NGS Library Prep: Illumina Nextera XT

## Description
Part 4 of 4: Pool Libraries

Links:
* [Part 1: Tagment and Amplify](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)
* [Part 3: Normalize Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)
* [Part 4: Pool Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part4)

With this protocol, your robot can perform the Nextera XT DNA Library Prep Kit protocol described by the [Illumina Reference Guide](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-06.pdf).

This is part 4 of the protocol, which is step (4) pool libraries. This step combines equal volumes of normalized libraries in a single tube. After pooling, dilute and heat-denature the library pool before loading libraries for the sequencing run.

Store unused pooled libraries in the PAL tube and SGP plate at -25°C to -15°C for up to 7 days.

--
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Bio-Rad 96-Well Plate, 200μl](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr) containing samples from [Part 3](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)
* [Opentrons Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1) with 2mL tubes

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

This protocol requires specific labware in a specific set-up.

Slot 1: [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr) containing samples from [Part 3](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)

Slot 2: [Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1) with 2mL tubes (for collecting pools)

Slot 3: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* Note: If your protocol requires more tips due to the parameters you set, you will need to fill subsequent slots with tip racks.


Using the customization fields below, set up your protocol.
* Pipette Model: Select which pipette you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right).
* Number of Samples: Select the number of samples (1-96) to be run in the protocol. NOTE ~ selecting 24 or less samples will result in only the top-left corner of the plates being used (A1 - D6).
* Number of Pools: Select the number of pools (2mL tubes) that should be created from the sample plate.
* Pool Volume (μl): Select the amount (in microliters) of sample material to transfer to each pooling tube.



### Robot
* [OT 2](https://opentrons.com/ot-2)


## Process
1. Select all desired settings according to the “Setup” section above to customize your protocol run.
NOTE ~ "Number of Samples" should be the same as [Part 1](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1), [Part 2](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2), and [Part 3](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3).
2. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
3. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
4. Make sure labware is properly set up on the deck. The plate containing samples should be in slot 1 and the tube rack should be in slot 2. Tubes should be loaded at 'A1', then 'B1', etc.

### Additional Notes
If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
bU7eUGEh
872
