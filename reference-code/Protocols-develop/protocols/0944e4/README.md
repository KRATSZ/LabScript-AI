# NGS Library Cleanup with Ampure XP Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Ampure XP

## Description
This protocol performs a custom NGS library cleanup using Ampure XP beads in a variable ratio with samples. The samples are mounted on an Opentrons magnetic module, and the final elute is transferred to a fresh PCR plate.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons Magnetic Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [USA Scientific 12-channel reservoir 22ml #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [Eppendorf twin.tec 96-well PCR plate #0030129512](https://www.fishersci.com/shop/products/eppendorf-twin-tec-96-lobind-pcr-plates-skirted-clear/e0030129512)
* [P20 multi-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 20ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-filter-tip)
* [Opentrons 200ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

12-channel reservoir (slot 7)
* channel 1: Ampure XP beads
* channel 2: 80% ethanol
* channel 3: EB buffer
* channels 11-12: liquid waste (loaded empty)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P20 and P300 multi-channel pipettes and the number of samples to process.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0944e4
