# Version Update - Adding Water to RBC 96-Well Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol updates an existing protocol request from Opentrons API Version 1 to Opentrons API Version 2.</br>
</br>
Using the customizable parameters below, you can specify which column to start picking up tips from and how many samples are in each run for each protocol. </br>
</br>
This protocol uses custom labware definitions for the glass trough (Electron Microscopy Sciences), Omegaquant 96-Well Plate, Blood Tube Rack, and 200ul Tip Rack. When downloading the protocol, the labware definitions (a JSON file) will be included for use with this protocol. For more information on using custom labware on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols)


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P50 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons Corning 96 Well Plate 360 µL Flat](https://labware.opentrons.com/corning_96_wellplate_360ul_flat?category=wellPlate)
* [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack)
* [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Electron Microscopy Sciences Rectangular Staining Dish [https://www.emsdiasum.com/microscopy/products/histology/staining.aspx#70314]
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: Electron Microscopy Sciences Rectangular Staining Dish

Slot 2: Corning 96 Well Plate 360 µL Flat

Slot 4: Opentrons 96 Tip-Rack 300ul

P300-Multi Mount: Left




</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify number of samples in well plate.
* **Starting Tip Column**: Specify which column of tips to begin drawing from.



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
3e3c9d-protocol-Adding-Water-RBC
