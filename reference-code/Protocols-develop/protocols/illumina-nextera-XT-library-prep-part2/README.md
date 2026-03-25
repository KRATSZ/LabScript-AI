# Nextera XT DNA Library Prep Kit Protocol: Part 2/4 - Clean Up Libraries

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Featured
     * NGS Library Prep: Illumina Nextera XT

## Description
Part 2 of 4: Clean Up Libraries

Links:
* [Part 1: Tagment and Amplify](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)
* [Part 2: Clean Up Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part2)
* [Part 3: Normalize Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part3)
* [Part 4: Pool Libraries](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part4)

With this protocol, your robot can perform the Nextera XT DNA Library Prep Kit protocol describe by the [Illumina Reference Guide](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-06.pdf).

This is Part 2 of the protocol, which consists of just step (3) of the overall process: clean up libraries. This step uses AMPure XP beads to purify the library DNA and remove short library fragments after the previous step, library amplification.

After this step, it is safe to stop the workflow and return to it at a later point. If you are stopping, seal the plate and store at -15°C to -25°C for up to seven days.

---
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
* A1: Resuspension Buffer
* A2: AMPure XP Beads
* A3: 80% Ethanol
* A4: 80% Ethanol (if needed)
* A5: 80% Ethanol (if needed)
* A9: Liquid Waste
* A10: Liquid Waste
* A11: Liquid Waste
* A12: Liquid Waste

Slot 4: [Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate) (clean and empty)

Slot 5: [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr) containing samples from [Part 1](http://protocols.opentrons.com/protocol/illumina-nextera-XT-library-prep-part1)

Slot 6: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 7: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 8: [Opentrons Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Note: If your protocol requires more tips due to the parameters you set, you will need to fill subsequent slots with tip racks.


Using the customization fields below, set up your protocol.
* Pipette Model: Select which pipette (P50/P300; Single/8-Channel) you will use for this protocol.
* Pipette Mount: Specify which mount your single-channel pipette is on (left or right).
* Magnetic Module Gen: Specify which Magnetic Module is in use
* Number of Samples: Select the number of samples (1-96) to be run in the protocol.
* Initial Product Volume (µl): Select the starting volume of PCR product to be used in the protocol.
* Bead Ratio: Select the bead ratio. 1.8 is recommended for small (300-500 bp) inputs, and 0.6 is recommended for larger (>500 bp) samples. Please see [documentation](https://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nextera-xt/nextera-xt-library-prep-reference-guide-15031942-05.pdf) for more information.
* Resuspension Buffer Volume (µL): Specify how much Resuspension Buffer is added to the wells.
* Final PCR Product Volume (µL): Specify the final elution volume to be transferred.
* Dry Time (minutes): Specify how long (in minutes) you would like to let the beads dry after the wash steps and before adding the resuspension buffer.





### Robot
* [OT-2](https://opentrons.com/ot-2)

### Modules
* [Magnetic Module](https://opentrons.com/modules)

### Reagents
* [Nextera XT DNA Library Prep Kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-xt-dna.html)
* [Ampure XP for Size Selection](https://www.beckman.com/reagents/genomic/cleanup-and-size-selection/pcr)

## Process
1. Select all desired settings according to the “Setup” section above to customize your protocol run.
2. Download your customized OT-2 protocol using the blue “Download” button, located above the deckmap.
3. Upload your protocol into the Opentrons App and follow the instructions there to set up your deck, calibrate your labware, and proceed to run.
4. Make sure to add reagents to your labware before placing it on the deck! Your reagents should be in your reservoir, and the samples you’re starting with should be in your plate in slot 5 on the deck.


### Additional Notes
If you’d like to request a protocol supporting multiple plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an applications engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
bU7eUGEh
872
