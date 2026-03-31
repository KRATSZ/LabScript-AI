# Nucleic Acid Purification - Workflow 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Purification

## Description
This protocol automates variable pooling of samples and addition of lysis buffer for manual extraction downstream. 
[Workflow 1](https://develop.protocols.opentrons.com/protocol/6fe477-workflow-1)
---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P1000 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 200ul filter tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 1000ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [VWR 1.5mL Centrifuge](https://us.vwr.com/store/product/4674417/vwr-micro-centrifuge-tube-with-flat-screw-cap)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* Opentrons 200ul filter tiprack (Slot 5)
* Opentrons 1000ul tiprack (Slot 6)
* VWR 1.5mL Tubes in Opentrons 24 Tube Rack (Slot 2)
* NEST 195 mL Reservoir (Slot 3)
* 30 mL Caplug Tubes in Opentrons 6 Tube Rack (Slots 1, 4, 7, 8, 9, 10, 11)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input total sample number (number of 30 mL tubes), pool size (between 2-5), and pipette mounts.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6fe477