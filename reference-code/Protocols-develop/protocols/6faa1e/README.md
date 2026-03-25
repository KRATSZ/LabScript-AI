# PCR/qPCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol automates the steps of transferring mastermix from source plates to destination plates.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P20 multi-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Thermo Scientific™ PCR Plate, 96-well, semi-skirted](https://www.fishersci.com/shop/products/thermo-scientific-96-well-semi-skirted-plates-flat-deck/ab1400l)
* [Eppendorf PCR cooler](https://www.daigger.com/eppendorf-pcr-coolers-14616-group?gclid=CjwKCAiAz4b_BRBbEiwA5XlVVkYoJn1xfnsYoEzsrHijqNP-YRCcVBJtWxD9-ENFfB_Pc9RZJUaXYRoCWjQQAvD_BwE)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* Destination Plates (PCR Plate on top of Eppendorf Cooler) (Slots 1-8)
* Source Plate (NEST 12-channel 15ml reservoir on top of ice tray) (Slot 11)
* Opentrons 20 uL tip rack (Slot 10)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select your pipette mount
2. Download your protocol
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6faa1e