# Zymo Research Direct-zol-96 RNA MagPrep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Kit


## Description
This protocol performs capsule nucleic acid purification according to the Zymo Research Direct-zol-96 RNA MagPrep kit. This protocol has been updated from [this protocol](https://protocol-delivery.protocols.opentrons.com/protocol/716efb) (written with APIv1) to APIv2.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [P300 Multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 300ul tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* [Bio-Rad Hardshell 96-Well PCR Plate 200ul #HSP9601](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Axygen 96-Deepwell Plate 2.0ml #P-DW-20-C-S](https://ecatalog.corning.com/life-sciences/b2c/US/en/Genomics-&-Molecular-Biology/Automation-Consumables/Deep-Well-Plate/Axygen%C2%AE-Deep-Well-and-Assay-Plates/p/P-DW-20-C-S)
* [Agilent 1 Well Reservoir 290mL #201252-100](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [USA Scientific 12-channel Reservoir 22ml #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

12-channel reservoir (deck slot 5)
* channel 1: magbeads **vortexed and added to the reservoir immediately before beginning the protocol run**
* channel 2: DNAse
* channels 3-5: RNA buffer
* channels 6-8: magbead wash 1
* channels 9-11: magbead wash 2
* channel 12: DNAse/RNAse-free water

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process, the mount side for your P300 multi-channel pipette, the volume of beads to transfer initially (in µl), and the bead separation time (in minutes).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2c83f7
