# Arcis Blood Extraction and PCR Setup (Multi)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Arcis Blood Kit


## Description
**Note: This is an updated version (apiV1 to apiV2) of [this protocol](https://protocol-delivery.protocols.opentrons.com/protocol/arcis-test-multi)**

This protocol is designed for running tests with the Arcis Blood Kit with Opentrons Multi-Channel Pipettes and a 12-channel trough. (further instructions about the protocol can be found [here](https://arcisbio.com/wp-content/uploads/2019/09/Arcis-Blood-kit-Bulk-kit-UFL005-50rxn-IFU-Rev-6.12.2018.pdf)). With the Arcis Blood Kit, nucleic acid investigations can be performed easily and efficiently with the two included reagents. This protocol calls for the use of a P50-Multi and P300-Multi pipettes, as well as a 12-channel reservoir (USA Scientific), Corning 96-well, 360μL flat plate, and two Bioplastics 100μL plates.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Arcis Blood Kit](http://www.arcisbio.com/products/arcis-dna-blood-kit/)
* [Opentrons P50 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 50uL/300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [USA Scientific 12-Channel Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* [Corning 96-Well Plate 360µL, Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat)
* [Bioplastics 8-Tube Strip Mat, 100µL](https://bioplastics.com/productdetails.aspx?code=B59009-1)
* Samples

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Corning 360µL Plate, clean and empty

Slot 2: Bioplastics Plate (in holder), clean and empty

Slot 3: Bioplastics Plate (in holder), clean and empty

Slot 4: 12-Channel Reservoir
* Channel 1: Reagent 1 (150µL per sample, 15mL for full plate)
* Channel 2: Reagent 2 (20µL per sample, 2mL for full plate)
* Channel 3: MasterMix (20µL per sample, 2mL for full plate)
* Channel 4: Sample (30µL per sample, 3mL for full plate)

Slot 5: Opentrons Tips

Slot 6: Opentrons Tips


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
This protocol is meant for validation testing of the Arcis Blood Kit with the Opentrons platform (multi-channel), but can be used for DNA extraction in a small number of samples.

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
arcis-test-multi
