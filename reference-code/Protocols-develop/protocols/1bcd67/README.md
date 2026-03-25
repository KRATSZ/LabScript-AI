# Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
With this flexible protocol, you can normalize the concentrations of up to 32 samples. Just upload your properly formatted .json files (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol.

---

### Labware
* [ThermoFisher Abgene™ 96 Well 2.2mL Polypropylene Deepwell Storage Plate](https://www.thermofisher.com/order/catalog/product/AB0661#/AB0661)
* [ThermoFisher Nalgene™ Disposable Polypropylene Robotic Reservoirs 300ml](https://www.thermofisher.com/order/catalog/product/1200-1300#/1200-1300)
* [Nunc™ 96-Well Polypropylene Storage Microplates](https://www.thermofisher.com/order/catalog/product/267245)
* [Opentrons 300µl and 1000µl pipette tips](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [Opentrons P300 multi-channel GEN2 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* [Opentrons P1000 single-channel GEN2 pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

### Reagents
* aqueous solutions

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1bcd67/deck3.png)

---

### Protocol Steps
1. Diluent volume is calculated and added to all wells in deepwell plate if a 2-step dilution is necessary (maximum working volume of 1600µl). The protocol dynamically calculates the maximum efficiency for P300 multi-channel and P1000 single-channel use.
2. The protocol pauses and prompts the user to add the first column of samples (in a user-specified volume) to dilution plate 1.
3. The P300 multi-channel pipette mixes the column both at the bottom of each well and halfway up the liquid for homogeneity. The liquid level is automatically calculated to ensure the pipette tip stays submerged.
4. If necessary, the diluted sample is transferred to the corresponding column in dilution plate 3 that contains pre-added diluent (step 1) for a final dilution.

## Process
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
1bcd67
