# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs a custom PCR prep across 6 96-well plates. It accommodates selection of P20 and P300 GEN2 multi- or single-channel pipettes.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-well aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)

### Labware
* [ThermoFisher Nunc™ 96-Well Microplates #249944](https://www.thermofisher.com/order/catalog/product/249943#/249943)
* [Bio-Rad 96 Well Plate 200 µL PCR #HSP9601](https://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20µl and 300µl 96 Tipracks](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [Opentrons P20 and P300 GEN2 Electronic Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes)

---

### Reagent Setup
Reagent reservoir:  
* channel 1: DNAse buffer
* channel 2: EDTA
* channels 3-7: dilution buffer
* channel 8: PCR mix

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
0e8e3
