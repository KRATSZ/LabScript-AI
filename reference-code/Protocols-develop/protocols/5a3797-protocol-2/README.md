# Protocol 2 for PCR set-up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs the transfer of mastermix and samples from a source to a destination PCR plate.

## Protocol Steps

1. Aliquot 15uL of master mix from a PCR tube strip into an ABI 96 well fast start PCR plate
2. Aliquot 10uL of sample from the deep well RNA plate to the ABI 96 well PCR plate


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [KingFisher™ Plastics for 96 deep-well format](https://www.thermofisher.com/order/catalog/product/95040450#/95040450)
* [MicroAmp™ Fast Optical 96-Well Reaction Plate, 0.1 mL](https://www.thermofisher.com/order/catalog/product/4346907#/4346907)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
* Opentrons 200 uL Filter Tip Rack (Slot 1, Slot 2)
* Sample Deep Well Plate (Slot 4)
* PCR Plate (Slot 5)
* 12-well reservoir (Master Mix) (Slot 7)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Select the mount position for the P20-multichannel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5a3797-protocol-2