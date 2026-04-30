# Protocol 1 for Wash Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs aliquoting of multiple buffers from different reservoirs into multiple 2 mL KingFisher deep well plates.

## Protocol Steps

1. Aliquot 500uL from a 15mL -12 section reservoir (wash 1 solution) into a 96, 2mL deep well plate.
2. Aliquot 1000uL from a 15mL-12 section reservoir (wash 2 (80% ETOH) into a second 96, 2 mL deep well plate.
3. Aliquot 50uL from a 15mL-12 section reservoir (elution buffer) into a 96, 2mL deep well plate.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [KingFisher™ Plastics for 96 deep-well format](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons 200 uL Filter Tip Rack (Slot 1)
* Wash 1 Deep Well Plate (Slot 4)
* Wash 2 Deep Well Plate (Slot 5)
* Elution Buffer Deep Well Plate (Slot 6)
* 12-well reservoir (Wash 1 Solution) (Slot 7)
* 12-well reservoir (Wash 2 Solution) (Slot 8)
* 12-well reservoir (Elution Buffer Solution) (Slot 9)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select the mount position for the P300-multichannel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5a3797-protocol-1