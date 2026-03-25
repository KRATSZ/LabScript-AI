# Transfer with Temperature Module

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol utilizes the P300 (GEN2) and P1000 pipettes to transfer and mix reagents between their original container and destination plate.

The protocol begins by making four (4) dilutions of reagent with heparin or sample. These dilutions are then added to a PCR plate on the temperature module and other reagents are added.

**Note about Temperature Module**: The temperature of the Temperature Module can now be set in the Opentrons App. To expedite a heating or cooling step in your protocol, you should set your Temperature Module to the desired temperature in the Opentrons App, prior to running your protocol.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P1000 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 1000µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Bio-Rad 96-Well Plate 200µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) (2mL and 15mL+50mL tops)
* Tubes (2mL, 15mL, and 50mL) for Tube Rack



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P300 Single GEN2 and P1000 Single) are attached.

Using the customization fields below, set up your protocol.
* P300 Single GEN2 Mount: Specify which mount the P300 is on (left or right).
* P1000 Single Mount: Specify which mount the P1000 is on (left or right.
* Incubation Time (in minutes): Specify how many minutes to have have the robot wait (incubate) after adding each reagent to the samples on the temperature module.

Slot 4: [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) (from set) and [Bio-Rad Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate), clean and empty

Slot 5: [15mL+50mL Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
	* A1: Reagent 1 (15mL Tube)
	* A2: Reagent 2 (15mL Tube)
	* A3: Reagent 4 (50mL Tube)
	* B1: Reagent 3 (15mL Tube)
	* B2: 20% Acetic Acid (15mL Tube)

Slot 6: [2mL Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 2mL tubes in A1-A5 and B1-B5
	* A1: Heparin Standard
	* B1: Sample
	* Remaining tubes should be empty to begin

Slot 5: [12 Column Reservoir](https://www.agilent.com/store/en_US/LCat-SubCat1ECS_112089/Reservoirs)
	* Column 1: Proeinase K
	* Column 3: Lysis Solution
	* Column 5: Magnetic Beads
	* Column 7: Elution

Slot 8: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 9: [Opentrons 1000µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)

Slot 11: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


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
08878b
