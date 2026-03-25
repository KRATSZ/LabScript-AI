# Standard Serial Dilution

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Serial Dilution


## Description
This protocol performs a simple serial dilution (factor 10) within each well plate for a specified number of well plates. 100ul of solution is mixed 12 times in each column before 20ul is transferred to the following column, with the mix-transfer iteration repeated up to the specified number of columns. New tips are granted between each well plate.


---
![Materials](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: 96 Tip Rack 300 µL

Slot 2 - (up to 11): Corning 96 Well Plate 360 µL Flat

P300-Multi Mount: Left


</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Columns**: Specify number of columns with solution in each well plate.
* **Number of Plates**: Specify number of plates for serial dilution.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package containing the custom labware definitions for the reservoir and plate.
2. Upload the labware definition in the [OT App](https://opentrons.com/ot-app). For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
74750e
