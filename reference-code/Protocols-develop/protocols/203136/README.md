# Purification of Genomic DNA

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Invitrogen ChargeSwitch


## Description
This protocol performs the Invitrogen ChargeSwitch gDNA Kit, using the P50 Single-Channel Pipette and the P300 Multi-Channel Pipette.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P50 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Bio-Rad 96-Well Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr)
* [USA Scientific 96-Deep Well Plate, 2.4mL](https://labware.opentrons.com/usascientific_96_wellplate_2.4ml_deep?category=wellPlate)
* [USA Scientific 12-Well Reservoir, 22mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml/)
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [Bio-Rad 96-Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr), clean and empty (for final elution)

Slot 2: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 3: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with a [96-Deep Well Plate](https://labware.opentrons.com/usascientific_96_wellplate_2.4ml_deep?category=wellPlate), filled with 200µL of sample

Slot 5: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 6: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 7: [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml/)
* A1: Lysis Buffer
* A2: Proteinase K
* A3: Purification Buffer
* A4: Mag Beads
* A5: Wash Buffer (Wash 1)
* A6: Wash Buffer (Wash 2)
* A7: Elution Buffer
* A8: Empty, for liquid waste
* A9: Empty, for liquid waste
* A10: Empty, for liquid waste
* A11: Empty, for liquid waste
* A12: Empty, for liquid waste

Slot 8: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 9: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 10: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 11: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


**Using the customizations fields, below set up your protocol.**
* **P300 Multi Mount**: Select which mount (left or right) the P300 Multi is attached to.
* **P50 Single Mount**: Select which mount (left or right) the P50 Single is attached to.
* **Number of Samples**: Specify the number of samples you'd like to run.



**Note**: The number of tips needed, will change according to the number of samples you select. For example, if running 96 samples, you'd need 8 tip racks, but if running 8 samples, only 1 tip rack is required. When you upload the protocol, you should see an updated deck layout with the necessary tip racks shown.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
203136
