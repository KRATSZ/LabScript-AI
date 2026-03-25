# Promega MagneHis™ Protein Purification System

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* MagneHis™ Protein Purification System

## Description
This protocol performs a custom protein purification on the OT-2 using the [Promega MagneHis™ Protein Purification System](https://www.promega.co.uk/products/protein-purification/protein-purification-kits/magnehis-protein-purification-system/?catNum=V8550) in conjunction with the [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck). The user is prompted to replace tipracks once in the protocol if necessary.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [Greiner Bio-One 96-deepwell block 2ml #780270](https://shop.gbo.com/en/usa/products/bioscience/microplates/polypropylene-storage-plates/96-well-masterblock-2ml/780270.html)
* [Greiner Bio-One 96-well PCR plate 200µl #651161](https://shop.gbo.com/en/usa/products/bioscience/microplates/96-well-microplates/96-well-microplates-clear/651161.html)
* [Agilent 12-channel reservoir 21ml #201256-100](https://www.agilent.com/store/productDetail.jsp?catalogId=201256-100)
* [Agilent 3-channel reservoir 95ml #204249-100](https://www.agilent.com/store/productDetail.jsp?catalogId=204249-100)
* [Opentrons P300 GEN1 multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette?variant=5984202489885)
* [Opentrons 300ul tipracks](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

12-channel reservoir (slot 2, volumes for 96 samples)
* channel 1: 17ml 10x FastBreak™ Cell Lysis Reagent
* channel 2: 17ml 10x Benzonase/Lysozyme Mix
* channel 3: 17ml 5M NaCl
* channel 4: 10ml MagneHis particles
* channel 5: 17ml MagneHis Elution Buffer
* channels 7-10: liquid waste (loaded empty)

3-channel reservoir (slot 3, volumes for 96 samples)
* channel 1: 80ml MagneHis Wash Buffer
* channels 2-3: liquid waste (loaded empty)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process (1-96) and the mount side for your P300 GEN1 multi-channel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
33900b
