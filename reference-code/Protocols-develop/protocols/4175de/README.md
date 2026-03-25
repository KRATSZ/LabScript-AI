# Cherrypicking PCR/qPCR prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep


## Description
This protocol performs a custom cherrypicked PCR/qPRC prep. It requires a CSV input for the source and destination wells of the samples. It will automatically add mastermix based on the number of samples inputted to the PCR plate sequentially (A1-12 then B1-12, etc...).
---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [P20 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)
* [Corning 96-Well Nonbinding Surface Microplates (3641)](https://www.fishersci.com/shop/products/corning-96-well-nonbinding-surface-nbs-microplates-flat-wells-clear/07200777)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 24 Tube Rack with Generic 2 mL Screwcap](https://shop.opentrons.com/products/tube-rack-set-1?_ga=2.48408495.884537678.1605539831-1181961818.1604785212)
* [Opentrons 96 Well Aluminum Block with Generic PCR Strip 200 µL](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set?_ga=2.124502019.884537678.1605539831-1181961818.1604785212)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* Opentrons 20ul filter tiprack (Slot 1, Slot 4, Slot 7)
* Opentrons 24 Tube Rack with Generic 2 mL Screwcap (Slot 2, Mastermix in well A6)
* Opentrons Temperature Module (Slot 3)
* 96 well PCR Strip (Aluminum Block) OR 96 well NEST 100uL PCR Plate (Slot 3 on Temperature Module)
* Corning 96-Well Nonbinding Surface Microplates OR Opentrons 24-slot Tube Rack (Slot 5, Slot 6, Slot 8, Slot 11)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the total sample number (used for distributing mastermix to variable number of wells sequentially), select P20-single channel mount, select PCR plate on top of the Temperature Module, and upload a CSV with sample transfer data. [Download an Example CSV](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/4175de/pcr_data.csv)
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4175de
