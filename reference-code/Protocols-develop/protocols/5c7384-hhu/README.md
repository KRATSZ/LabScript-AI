# SP3 Proteomics Mass Spec Sample Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Mass Spec


## Description
This protocol performs mass spec sample prep per this [SP3 Proteomics manual (Appendix Protocol B)](https://www.embopress.org/action/downloadSupplement?doi=10.15252%2Fmsb.20199111&file=msb199111-sup-0001-Appendix.pdf). The following steps are performed throughout the protocol with the use of the Opentrons OT-2, Thermocycler Module, and Magnetic Module (GEN2):

* Reduction and Alkylation
* Protein Binding
* Ethanol Wash
* Acetonitrile Wash
* On-Bead Digestion

Due to limited deck space, the user is prompted to change tipracks on the deck when needed, and to move labware when needed.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P20 GEN2 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons P300 GEN2 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-30ul-tips)
* [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) or comparable PCR plates


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Reagent plate (slot 5):
* column 1: DTT
* column 2: CAA
* column 3: magnetic bead stock
* columns 4-5: ABC
* column 6: trypsin

Ethanol plate (slot 2)

Acetonitrile plate (slot 3)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol. For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5c7384
