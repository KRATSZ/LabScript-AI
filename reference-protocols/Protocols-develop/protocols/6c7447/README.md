# qPCR GCN Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep


## Description
This protocol is an update to a qPCR prep protocol designed for the OT-1.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P10 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Bio-Rad 96-Well Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr)
* Eppendorf 2mL Tubes
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Bio-Rad Plate (qPCR Plate)

Slot 2: Bio-Rad Plate (DNA Plate)

Slot 3: [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips), Full Tip Rack

Slot 4: [Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1) with 2mL Tubes and Reagents

Slot 5: [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips), with only tips in row 'A'

Slot 6: [[Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips), with only tips in 'A1' and 'A2'

Slot 7: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips), Full Tip Rack




**Using the customizations fields, below set up your protocol.**
* **P10 Multi Mount**: Select which mount (left or right) the P10 Multi is attached to.
* **P300 Single Mount**: Select which mount (left or right) the P300 Single is attached to.
* **Pre-Wet Tips?**: Specify whether or not you'd like a mix step prior to each transfer to pre-wet the tip.



**Note**: The tip racks in slot 5 and 6 should be empty, with tips only in row 'A'. This will allow the P10-Multi to effectively operate as a single channel pipette.

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
6c7447
