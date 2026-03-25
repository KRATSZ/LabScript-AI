# PCR Preparation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs a custom PCR preparation on DNA samples in triplicate using pre-created mastermix.

DNA samples should be arranged down columns before moving across rows (sample 1 in plate well A1, sample 2 in plate well B1, ..., sample 9 in plate well A2, etc.).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Thermo Scientific semi-skirted 96-well PCR plate 300ul #AB1400150](https://www.fishersci.com/shop/products/thermo-scientific-96-well-semi-skirted-plates-flat-deck-11/ab1400150?searchHijack=true&searchTerm=AB1400150&searchType=RAPID&matchedCatNo=AB1400150)
* [NEST 12-channel reservoir 15ml #360102](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* [Opentrons P300 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons P20 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 10/20ul and 50/300ul tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the respective mount sides for your P300 multi-channel and P20 GEN2 single-channel pipettes and the number of DNA samples to process (1-96).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
640a85
