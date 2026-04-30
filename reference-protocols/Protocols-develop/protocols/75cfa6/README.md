# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This is a custom PCR prep protocol that transfers up to 24 RNA samples to 4 different mastermixes. The transfer scheme can be shown on the deck layout below.

---

### Modules
* [Temperature Module (GEN1)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [Bio-Rad 96 Well Plate 200 µL PCR](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601) seated in [Opentrons 96-well aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)
* [Opentrons 4-in-1 tuberack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with Eppendorf 1.5ml snapcap microcentrifuge tubes seated in 24-tube adapter
* [Opentrons 10/20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

### Pipettes
* P10 single-channel electronic pipette (GEN1)
* P10 multi-channel electronic pipette (GEN1)

### Reagents
* [ThermoFisher SuperScript™ IV One-Step RT-PCR System](https://www.thermofisher.com/order/catalog/product/12594025)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/75cfa6/deck.png)

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
75cfa6
