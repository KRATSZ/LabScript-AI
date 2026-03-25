# 96-well to 384-well transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the distribution of samples from a 96-well plate (on the Temperature Module) to a 384-well plate.</br>
</br>
Given the mapping differences between a 96-well plate and a 384-well plate, the user can specify to transfer to *odd* rows (A/C/E...) or *even* rows (B/D/F...).</br>
</br>
This protocol uses a custom labware definition for the [Greiner Bio-One 384-well plate](https://shop.gbo.com/en/row/products/bioscience/microplates/384-well-microplates/384-deep-well-small-volume-polypropylene-microplate/784201.html). When downloading the protocol, the labware definition (a JSON file) will be included for use with this protocol. For more information on using custom labware on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols)



---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set)
* [96-Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Greiner Bio-One 384-well plate](https://shop.gbo.com/en/row/products/bioscience/microplates/384-well-microplates/384-deep-well-small-volume-polypropylene-microplate/784201.html)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [Greiner Bio-One 384-well plate](https://shop.gbo.com/en/row/products/bioscience/microplates/384-well-microplates/384-deep-well-small-volume-polypropylene-microplate/784201.html)

Slot 2: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 4: [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [96-Well Aluminum Block](https://shop.opentrons.com/collections/verified-labware/products/aluminum-block-set) & [96-Well Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) containing samples in columns 1-8
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Destination Rows**: Specify which rows the multi-channel pipette will dispense in.
* **P300-Multi Mount**: Select which mount (left or right) the P300-Multi is attached to.



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package containing the custom labware definition for the 384-well plate.
2. Upload the labware definition in the [OT App](https://opentrons.com/ot-app). For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
060c4f
