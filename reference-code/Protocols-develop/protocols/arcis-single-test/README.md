# Arcis Blood Extraction and PCR Setup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Arcis Blood Kit


## Description
**Note: This is an updated version (apiV1 to apiV2) of [this protocol](https://protocol-delivery.protocols.opentrons.com/protocol/arcis-test)**

This protocol is designed for running tests with the Arcis Blood Kit (further instructions about the protocol can be found [here](http://www.arcisbio.com/wp-content/uploads/2019/04/Arcis-Blood-kit-Bulk-kit-UFL005-50rxn-IFU-Rev-6.12.2018.pdf)). With the Arcis Blood Kit, nucleic acid investigations can be performed easily and efficiently with the two included reagents. This protocol calls for the use of a P50-Single and P300-Single pipettes, as well as Opentrons Tube Racks, Corning 96-well, 360μL flat plate, and two Bioplastics 100μL plates.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Arcis Blood Kit](http://www.arcisbio.com/products/arcis-dna-blood-kit/)
* [Opentrons P50 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 50uL/300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Corning 96-Well Plate 360µL, Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat)
* [Bioplastics 8-Tube Strip Mat, 100µL](https://bioplastics.com/productdetails.aspx?code=B59009-1)
* [1.5mL Eppendorf Safe-Lock Tube](https://www.usascientific.com/1.5ml-eppendorf-safe-lock-tube.aspx)
* 15mL Conical Tube
* 50mL Conical Tube
* Samples

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Opentrons Tiprack

Slot 2: Corning 360µL Plate, clean and empty

Slot 3: Bioplastics Plate (in holder), clean and empty

Slot 4: Bioplastics Plate (in holder), clean and empty

Slot 5: Opentrons 24 Tube Rack with 1.5mL Eppendorf Tubes
* A1: Sample (1000µL)
* A2: PCR Mastermix (1500µL)

Slot 6: Opentrons 10 Tube Rack with Conical Tubes
* A1: Reagent 2 (2000µL)
* A3: Reagent 1 (10000µL)


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
This protocol is meant for validation testing of the Arcis Blood Kit with the Opentrons platform, but can be used for DNA extraction in a small number of samples.

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
arcis-single-test
