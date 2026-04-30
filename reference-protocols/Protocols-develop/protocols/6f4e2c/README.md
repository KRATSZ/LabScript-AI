# DNA Isolation from Whole Blood

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Blood Sample


## Description
This protocol automates the protocol from Sileks for [DNA isolation from whole blood with MP@SiO2 magnetic particles](https://www.sileks.com/eu/librarian/librarian_ajax.php?ajaxaction=GetObjectByVName&VName=Manual_DNA_from_Blood_en_20141007.pdf). This protocol utilizes a P300-Multi Channel pipette and gives the user the option to select either 24 or 48 samples and whether to dispense liquid waste in a reservoir in slot 8 or in the fixed trash container. This protocol is also designed for using the Eppendorf 1000µL deep-well plate.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) or [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Bio-Rad 96-Well Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr)
* [NEST 12-Well Reservoir, 15mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* [NEST 1-Well Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir), if using for liquid waste
* Eppendorf 1000µL Deep-Well Plate
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with Eppendorf Deep-Well Plate and 100µL of blood sample in corresponding wells (either 24 or 48)

Slot 2: [NEST 12-Well Reservoir, 15mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* A1: Start Buffer
* A2: Lysis/Binding Buffer
* A3: Lysis/Binding Buffer (48 Samples)
* A4: Wash Buffer 1
* A5: Wash Buffer 1 (48 Samples)
* A6: Wash Buffer 2
* A7: Wash Buffer 2 (48 Samples)
* A8: Wash Buffer 3
* A9: Wash Buffer 3 (48 Samples)
* A10: Elution Buffer

Slot 3: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 4: [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

Slot 5: [Bio-Rad 96-Well Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr), for final elution

Slot 6: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 8: [NEST 1-Well Reservoir, 195mL](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir), if using for liquid waste

Slot 9: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 10: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 11: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


**Using the customizations fields, below set up your protocol.**
* **P300 Multi Mount**: Select which mount (left or right) the P300 Multi is attached to.
* **Tip Type**: Select the type of tips for this protocol (non/filter).
* **Number of Samples**: Specify the number of samples you'd like to run.
* **Liquid Waste in Reservoir**: Specify if liquid waste should be dispensed in reservoir (or fixed trash container)


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
6f4e2c
