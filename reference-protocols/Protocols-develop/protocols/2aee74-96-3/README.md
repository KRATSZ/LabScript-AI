# Olink® Target 96 Part 3/3: Detection

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Proteins & Proteomics
	* Olink® Target 96

## Description

Links:
* [Part 1: Incubation](./2aee74)
* [Part 2: Extension](./2aee74-2)
* [Part 3: Detection](./2aee74-3)

This protocol accomplishes part 3/3: Detection for use with the [Olink® Target 96 protocol](https://www.olink.com/products-services/target/) for protein biomarker discovery. Primers are transferred to the left 96 wells of the Fluidigm detection plate, and samples are transferred to the right 96 wells. The transfer mapping for these plates is shown in the following images:  
![scheme1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2aee74/scheme1-2.png)
![scheme2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2aee74/scheme2-2.png)
</br>
Olink® is a registered trademark of Olink Proteomics AB. Opentrons is not affiliated with or endorsed by Olink Proteomics AB.
---

### Labware
* [Fluidigm 96.96 Dynamic Array™ IFC for Gene Expression](https://store.fluidigm.com/Genomics/ApplicationsGenomics/GeneExpression/96-96%20Dynamic%20Array%E2%84%A2%20IFC%20for%20Gene%20Expression)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [NEST 1.5 mL Screwcap Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-1-5-ml-sample-vial) or equivalent
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P300 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* [Olink® Target 96](https://www.olink.com/products-services/target/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2aee74/deck3-5.png)
Note: all volumes for 96 samples (including controls)
* purple on primer plate (slot 1): samples
* blue on sample plate (slot 5): samples from extension
* green on tuberack (slot 9): 790.9µl detection mix

---

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2aee74
