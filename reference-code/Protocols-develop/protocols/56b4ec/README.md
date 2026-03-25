# Sample Prep with Custom Labware

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs all of the steps as outlined in the `MethodA_map_labware_protocol` file. This protocol requires the use of custom labware (Charles River Tube Rack) and custom tips (200µL, extended length).


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P50 Single Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons P1000 Single Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 1000µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Corning 96-Well Plate, 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* Custom 200µL Tips
* Custom Tube Rack for 10mL Charles River Tubes
* Falcon 50mL Conical Tube
* Eppendorf 2mL Tubes


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Custom 200µL Tips

Slot 2: Opentrons 1000µL Filter Tips

Slot 3: [Corning 96-Well Plate, 360µL](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)

Slot 4: *Empty*

Slot 5: *Empty*

Slot 6: *Empty*

Slot 7: [Opentrons 6 Tube Rack](https://labware.opentrons.com/opentrons_6_tuberack_falcon_50ml_conical?category=tubeRack) with 50mL Tube (Rack for water)
* A1: Water, 30mL

Slot 8: Custom Charles River Tube Rack (Rack for sample 1 dilution)
* A1: Sample 1, 4mL
* A2: Charles River Tube, empty
* A3: Charles River Tube, empty
* A4: Charles River Tube, empty
* B1: Charles River Tube, empty
* B2: Charles River Tube, empty
* B3: Charles River Tube, empty
* B4: Charles River Tube, empty

Slot 9: *Empty*

Slot 10: [Opentrons 24 Tube Rack](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap?category=tubeRack) with 2mL Tubes (Rack for RSE & NEP)
* A1: RSE, 1mL
* A2: HKSA, 500µL

Slot 11: Custom Charles River Tube Rack (Rack for RSE & HKSA dilution)
* A1: Charles River Tube, empty
* A2: Charles River Tube, empty
* A3: Charles River Tube, empty
* A4: Charles River Tube, empty
* A5: Charles River Tube, empty
* B1: Charles River Tube, empty
* B2: Charles River Tube, empty
* B3: Charles River Tube, empty
* C1: Charles River Tube, empty
* C2: Charles River Tube, empty


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your zipped protocol bundle.
3. Unzip your downloaded protocol bundle; there should be a protocol file and a labware folder.
4. Upload your labware definition files by dragging them into the 'Custom Labware' section of the 'More' tab of the [OT App](https://opentrons.com/ot-app).
5. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
6. Set up your deck according to the deck map.
7. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
8. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
56b4ec
