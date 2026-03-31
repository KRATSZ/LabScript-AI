# PCR/qPCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs PCR prep by reformatting 4 different 96 Well King Fisher plates into a MicroAmp 384 Well PCR plate. It begins by creating an adequate amount of mastermix depending on the number of samples.

**96 Well Plate Format**

![96 Well Plates](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2ee5be/96_plates.png)

**384 Well Plate Format**

![384 Well Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2ee5be/384_plate.png)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P300 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 multi-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5978988707869)
* [Opentrons 300ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 20ul tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [KingFisher™ Plastics for 96 deep-well format](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* [MicroAmp™ Optical 384-Well Reaction Plate with Barcode](https://www.thermofisher.com/order/catalog/product/4309849?SID=srch-srp-4309849#/4309849?SID=srch-srp-4309849)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Deck Setup
* KingFisher Deep Well Plates (Slots 1-4)
* MicroAmp 384 Well PCR Plate (Slot 5)
* NEST 12 Reservoir 15mL (Slot 6)
	- Water (A1)
	- Multiplex Reagent (A2)
	- Dye (A3)
* Opentrons 300 uL Tip Rack (Slot 7)
* Opentrons 200 uL Tip Rack (Slots 8-11)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the total sample number, select P20-multi channel mount, select P300-single channel mount
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2ee5be