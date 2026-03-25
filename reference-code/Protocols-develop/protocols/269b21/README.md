# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs a custom PCR preparation by transferring mastermix and sample from 1.5ml snapcap tubes and 8-strip PCR tubes, respectively. Mastermix tubes are actively cooled on a temperature module, and samples are passively cooled on a pre-frozen 96-well aluminum block.

Mastermix tubes should be aligned *down* the aluminum block on the temperature module before moving *over* a column (i.e. A1, B1, C1, D1, A2, etc.)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons temperature module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [4x6 aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) for [VWR 1.5ml snapcap microtubes #20170-038](https://us.vwr.com/store/product?keyword=20170-038)
* [Opentrons 96-well aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with [VWR 8-strip microtubes #490004-440](https://us.vwr.com/store/product/16208471/genemate-combination-packs-8-strip-standard-tubes-with-8-strip-optically-clear-flat-caps) (pre-frozen)
* [Bio-Rad Hardshell 384-well PCR plate 50µl #HSP3805](https://www.bio-rad.com/en-us/sku/hsp3805-hard-shell-384-well-pcr-plates-thin-wall-skirted-clear-white?ID=HSP3805)
* [Opentrons P20 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 20µl tiprack](opentrons_96_tiprack_20ul)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 aluminum block on temperature module
* tubes A1-D1: buffer

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of mastermixes to be processed, the number of CDNA samples to be processed, and the mount side for your P20 GEN2 single-channel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
269b21
