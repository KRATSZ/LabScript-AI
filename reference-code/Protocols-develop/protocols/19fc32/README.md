# Library Prep Clean Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Clean Up


## Description
This protocol is a slightly modified version of a clean up protocol. With this protocol, the user selects which mount their P50-Multi is attached to and the protocol adds the necessary reagents and (dis)engages the magnetic module to accomplish the clean up. To conclude this protocol, 4µL of supernatant is added to a 384-well plate and 20µL of supernatant is added to a 96-well plate.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P50 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Bio-Rad 96-Well Plate, 200µL](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr)
* [Bio-Rad 384-Well Plate](https://www.bio-rad.com/en-au/product/384-well-pcr-plates?ID=OCH4UM15)
* [NEST 12-Well Reservoir](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [NEST 12-Well Reservoir](https://labware.opentrons.com/nest_12_reservoir_15ml?category=reservoir)
* A1: Magnetic Beads
* A2: 80% Fresh Ethanol (~10mL)
* A3: 80% Fresh Ethanol (~10mL)
* A4: 80% Fresh Ethanol (~10mL)
* A5: 80% Fresh Ethanol (~10mL)
* A6: RSB Buffer
* A7: Empty
* A8: Empty
* A9: Empty, for liquid waste
* A10: Empty, for liquid waste
* A11: Empty, for liquid waste
* A12: Empty, for liquid waste

Slot 2: [Bio-Rad 96-Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr), clean and empty

Slot 3: [Bio-Rad 384-Well Plate](https://www.bio-rad.com/en-au/product/384-well-pcr-plates?ID=OCH4UM15)

Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with a [Bio-Rad 96-Well Plate](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr), filled with 25µL of sample

Slot 5: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 6: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 7: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 8: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 9: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 10: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)




**Using the customizations fields, below set up your protocol.**
* **P50 Multi Mount**: Select which mount (left or right) the P50 Multi is attached to.



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
19fc32
