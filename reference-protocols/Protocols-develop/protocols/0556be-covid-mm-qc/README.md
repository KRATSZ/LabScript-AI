# COVID MM-QC Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol performs the transfer of 2 components into multiple 2 mL tubes in the first step. In the second step, the protocol transfers reagent from the first tube to 9 select wells in the PCR tube strips. In the final step, it transfers Component 3 into the first 3 wells of the second strip.

This protocol combines v2 and v3 of the COVID MM-QC Protocol. The volumes of Component 1 and Component 2 can be changed in the parameters below.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Aluminum Blocks](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set?_ga=2.44012454.2010707504.1610321113-1181961818.1604785212)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons 10 Tube Rack (Slot 8)
* Temperature Module + 24 Well Aluminum Block (Slot 9)
* 24 Well Aluminum Block (Slot 5)
* 96 Well Aluminum Block with PCR Strips (Slot 6)
* 200 uL Filter Tips (Slot 4)
* 20 uL Filter Tips (Slot 1)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the required parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0556be-covid-mm-qc
