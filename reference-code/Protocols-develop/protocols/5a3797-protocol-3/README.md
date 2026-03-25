# Protocol 3 for Sample plate set up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs aliquoting from 7 different tube racks (first 96 tubes) into a 96 well plate. It then aliquots from a 12-well reservoir into the deep well plate.

## Protocol Steps

1. Aliquot 200uL from the approximately 7 tube racks into 96 well plate
2. Aliquot 275uL from 15mL-12 section reservoir into the deep well plate change tips for each row.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [KingFisher™ Plastics for 96 deep-well format](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* Sorfa 10 mL Tubes
* Copan 10 mL Tubes

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons 200 uL Filter Tip Rack (Slot 1, Slot 2)
* Sample Deep Well Plate (Slot 3)
* 12-well reservoir (Slot 4)
* Tube Racks 1-7 (Slots 5-11, sequentially)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select the mount position for the P300-multichannel and P300-single channel pipette. Choose tube rack type for each of the tube racks.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5a3797-protocol-3