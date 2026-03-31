# Custom Plate Filling

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates the distribution of assays from a 48-well reservoir to 9, 96-well plates.</br>
</br>
Using the customizable parameters below, you can specify which column to start picking up tips from and how many *"runs"* to perform. During each *run*, all 9 plates will be filled with assay from the reservoir. At the conclusion of filling the 9 plates, the OT-2 will flash, pause, and prompt the user to replace the plates on the deck.</br>
</br>
This protocol uses custom labware definitions for the 48-well reservoir (Agilent) and 96-well plate (MicroAmp Endura). When downloading the protocol, the labware definitions (a JSON file) will be included for use with this protocol. For more information on using custom labware on the OT-2, please see this article: [Using labware in your protocols](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols)


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P50 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Agilent 48-Well Reservoir
* MicroAmp Endura 96-Well Plate
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: MicroAmp Endura 96-Well Plate

Slot 2: MicroAmp Endura 96-Well Plate

Slot 3: MicroAmp Endura 96-Well Plate

Slot 4: MicroAmp Endura 96-Well Plate

Slot 5: MicroAmp Endura 96-Well Plate

Slot 6: MicroAmp Endura 96-Well Plate

Slot 7: MicroAmp Endura 96-Well Plate

Slot 8: MicroAmp Endura 96-Well Plate

Slot 9: MicroAmp Endura 96-Well Plate

Slot 10: [Opentrons 50/300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 11: Agilent 48-Well Reservoir with Reagents
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Starting Tip Column**: Specify which column of tips to begin drawing from. Over the course of the protocol, the multi-channel pipette will pick up tips from
* **P300-Multi Mount**: Select which mount (left or right) the P300-Multi is attached to.



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
08e3eb
