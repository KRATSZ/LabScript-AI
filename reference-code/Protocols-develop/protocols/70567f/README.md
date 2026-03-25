# NGS Library Cleanup with Ampure XP Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Ampure XP

## Description
This protocol performs a custom NGS library prep cleanup using Ampure XP beads in a variable ratio with samples. The samples are mounted on an Opentrons magnetic module, and the final elute is transferred to a fresh PCR plate.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [NEST 96 Deepwell Plate 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [P300 multi-channel electronic pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 200ul filtertipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

96-deepwell plate (slot 7)
* column 1: Ampure XP beads
* column 2: 80% ethanol
* column 3: EB buffer
* columns 10-12: liquid waste (loaded empty at start)

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
70567f
