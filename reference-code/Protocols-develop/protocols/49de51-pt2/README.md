# MagMAX Plant DNA Isolation Kit [2/2] DNA Purification

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Plant DNA


## Description
This protocol automates the ThermoFischer MagMAX Plant DNA Isolation Kit on up to 96 samples. The entire workflow is broken into 2 different protocols. This is part 2, DNA purification.</br>
</br>
In this protocol, 25µL of magnetic beads plus 400µL of ethanol is added to 400µL of sample (from [part 1](https://develop.protocols.opentrons.com/protocol/49de51-pt1)). After off-deck mixing, the plate is returned to the OT-2 for supernatant removal. This process continues with wash buffer 1, wash buffer 2, and the elution buffer. However, the supernatant of the elution buffer is preserved in a 96-well PCR plate and can be used for further downstream application.
</br>
</br>
**Update April 26, 2021**: The addition of magnetic beads has been made optional.</br>
</br>
**Update May 3, 2021**: A second wash step has been added and heights of aspiration adjusted.</br>
</br>
**Update June 8, 2021**: Added the ability to park tips. This will cut down on tip usage when using 48+ samples.</br>
</br>

If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.21.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons p300 Multi-Channel Pipette (attached to right mount)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [MagMAX™ Plant DNA Isolation Kit](https://www.thermofisher.com/order/catalog/product/A32549#/A32549)
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**</br>
</br>
Slot 11: [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) (for liquid waste)</br>
</br>
Slot 4: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* A1: Magnetic Beads (*see note 1 below*)
* A2: Ethanol (Samples 1-32)
* A3: Ethanol (Samples 33-64)
* A4: Ethanol (Samples 65-96)
* A5: *empty*
* A6: *empty*
* A7: *empty*
* A8: *empty*
* A9: *empty*
* A10: Wash Buffer 1 (Samples 1-32)
* A11: Wash Buffer 1 (Samples 33-64)
* A12: Wash Buffer 1 (Samples 65-96)

Slot 5: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* A1: Wash Buffer 2 (Samples 1-32)
* A2: Wash Buffer 2 (Samples 33-64)
* A3: Wash Buffer 2 (Samples 65-96)
* A4: Wash Buffer 2 (Samples 1-32)
* A5: Wash Buffer 2 (Samples 33-64)
* A6: Wash Buffer 2 (Samples 65-96)
* A7: *empty*
* A8: *empty*
* A9: *empty*
* A10: *empty*
* A11: Elution Buffer (Samples 1-48)
* A12: Elution Buffer (Samples 49-96)

Slot 10: Labware Containing Magnetic Beads (*see note 1 below*)</br>
</br>
Slot 7: [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Well Deep Well Plate](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) containing Samples</br>
</br>
Slot 1: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
</br>
Slot 8: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (*see note 2 below*)</br>
</br>
Slot 9: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (*see note 2 below*)</br>
</br>
Slot 6: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (*see note 2 below*)</br>
</br>
Slot 3: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (*see note 2 below*)</br>
</br>
</br>
Slot 2: [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips) (*see note 2 below*)</br>
</br>
</br>
**Note 1**: If using, the Magnetic Beads can be placed in well 1 of the [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) (in slot 4) or in column 1 of a different piece of labware (in slot 10)</br>
**Note 2**: Ten (10) columns of tips are needed per column of sample and will be accessed in the following order: slot 8, 9, 6, 3, 2. In the case that more than 48 samples are used, the user will be prompted midway through the protocol to replace the tips.</br>
</br>
**Using the customization fields below, set up your protocol.**
* Number of Samples: specify the number of samples (1-96)
* Deep Well Plate Type: select the type of deep well plate used (holding samples)
* Automate Bead Addition: select whether or not to automate the addition of magnetic beads
* Location of Magnetic Beads: select the location of the magnetic beads (*labware*; *deck slot*: *well*)
* Park Tips: Select **Yes** or **No**. If **Yes** is selected, one tiprack (in slot 2) will be used for all mixing and supernatant removals; the other tips should be placed in slot 3 and 6.
</br>
</br>

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol bundle.
2. Upload [custom labware definition](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols), if needed.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
49de51-pt2
