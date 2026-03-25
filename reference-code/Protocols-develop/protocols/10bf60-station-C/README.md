# Covid-19 qPCR Setup Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This is a flexible protocol accommodating a wide range of PCR setups. Mastermix is transferred from a 2ml snapcap tube to clean PCR plate using a P20 GEN2 single-channel pipette. Then, a P20 GEN2 multi-channel pipette transfers eluates from RNA extraction to the PCR plate containing mastermix. Samples are transferred to their corresponding positions from plate to plate (A1 to A1, B1, to B1, etc.)

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)

### Labware
* [Applied Biosystems MicroAmp 96 Aluminum Block 200 µL](https://www.thermofisher.com/order/catalog/product/N8010560#/N8010560)
* [Opentrons 96 Tip Rack 20µl](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Pipettes
* [Opentrons P20 Single-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons P20 Multi-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* RIDA®GENE reaction mix

---

### Reagent Setup
* 2ml snapcap reaction mix: tube position A1 of aluminum block on Opentrons Temperature Module (slot 7)

---

### Protocol Steps
1. P20 single-channel GEN2 pipette transfers reaction mix to each well of clean PCR plate using the same tip.
2. P20 multi-channel GEN2 pipette transfers eluates from extraction plate to PCR plate now containing reaction mix. Samples are mixed 3x at 10µl after each transfer. Tips are changed for each sample.

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
10bf60
