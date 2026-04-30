# Drug Screening

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol performs a custom drug screening assay through plate mapping from one mother plate to up to 6 daughter plates using a P10-multi channel pipette. All plates used are Corning 384-flatwell plates.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Corning 384-flatwell plates 112 µL](https://labware.opentrons.com/corning_384_wellplate_112ul_flat?category=wellPlate)
* [Opentrons P10 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons 10µl tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount side for your P10 multi-channel pipette, the number of daughter plates to map to (1-6), the start column for mapping (inclusive), the end column for mapping (inclusive), the transfer volume (in µl, up to 10), and the dispense plan (either one-to-one transfers, or multi-dispenses from the same source).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
18050b
