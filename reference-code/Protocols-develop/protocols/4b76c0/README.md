# DNA Normalization with Custom Labware

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization


## Description
![Normalization Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/normalization/normalization_example.png)

Concentration normalization is a key component of many genomic and proteomic applications, such as NGS library prep. With this protocol, you can easily normalize the concentrations of samples in a 96-well Axygen plate without worrying about missing a well or adding the wrong volume. Just upload your properly formatted CSV file (keep scrolling for an example), customize your parameters, and download your ready-to-run protocol.



**Using the customizations fields, below set up your protocol.**
* **Volumes CSV**: Upload the CSV (.csv) containing your diluent volumes.
* **P10 Multi Mount**: Select which mount (left or right) the P10 Multi is attached to.

*Note about CSV*: All values corresponding to wells in the CSV must have a value (zero (0) is a valid value and nothing will be transferred to the corresponding well(s)). Additionally, the CSV can be formatted in "portrait" orientation. In portrait orientation, the bottom left corner is treated as A1 and the top right corner would correspond to the furthest well from A1 (H12 in a 96-well plate).


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P10 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 12-Well Reservoir, 15mL](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* Axygen 96-Well Plate (PCR-96-FS-C)
* Diluent
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [NEST 12-Well Reservoir](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* A1: Diluent

Slot 2: Axygen 96-Well Plate (PCR-96-FS-C)

Slot 3: [Opentrons 10µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
4b76c0
