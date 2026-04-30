# Guanidine and PBS Transfer with CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol utilizes a CSV (.csv) file to dictate transfers of two reagents (Guanidine and PBS) to a 384-well plate. Simply upload the properly formatted CSV (examples below), set parameters, then download your protocol for use with the OT-2.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P10 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P50 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 10µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 50/300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [USA Scientific 12-Well Reservoir, 22mL](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* [Corning 384-Well Plate](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P10 and P50) are attached.

Using the customization fields below, set up your protocol.
* Transfer CSV: Upload your properly formatted (see below) CSV.
* P10 Single Mount: Specify which mount the P10 is on (left or right).
* P50 Single Mount: Specify which mount the P50 is on (left or right).

**Note about CSV**

The CSV should be formatted like so:

`Well` | `Guanidine Amount (µL)` | `PBS Amount (µL)`

The first row (A1, B1, C1) can contain headers (like above) or simply have the desired information. All of the following rows should just have the necessary information.

**Labware Setup**

Slot 1: [Opentrons 10µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 2: [12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* Column 1: Guanidine Solution
* Column 2: PBS Solution

Slot 3: [384-Well Plate](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)

Slot 4: [Opentrons 50/300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Upload your CSV and input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
26a414
