# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol creates a custom PCR prep protocol. The input into this protocol is an elution plate of purified DNA, and the output is PCR strips containing the samples mixed with mastermix.
Using a [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will begin by creating reaction mix in a 2ml tube. Samples will then be transferred from their plate to the qPCR plate and mixed with the reaction mix.

You can select any of the 5 mastermix compositions shown below:  
![mm](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/280ea4/image.png)

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)  

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [NEST PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing purified nucleic acid samples
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [2ml NEST screwcap tubes or equivalent](https://shop.opentrons.com/collections/tubes/products/nest-microcentrifuge-tubes) in Opentrons aluminum block containing PCR reagents
* [Opentrons P300 Single-Channel GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

---

![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/280ea4/deck.png)

![reagent layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/280ea4/reagents.png)

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
280ea4
