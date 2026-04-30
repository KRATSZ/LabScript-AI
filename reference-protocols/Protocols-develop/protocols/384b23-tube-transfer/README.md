# Custom Tube to Tube transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol transfers 500µL from tubes in 24 tube tuberacks to a 6x5 tube rack. New tips are granted between each transfer. Transfers are completed by column in the source tube rack and dispensed by row to the recipient tube racks. A new row starts with each column.


---
![Materials](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 1000µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* Custom Opentrons 24-tube tube rack
* Custom Opentrons 30-tube tube rack



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1: Source tube rack (6x4)

Slot 2: Destination tube rack (6x5)

Slot 3: Opentrons 1000µL Filter Tip Rack

</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Specify number of samples in the source tube rack to be transferred.
* **Delay Time after Aspirating (in seconds)**: Since saliva is being transferred, often times a delay after aspiration allows the pipette to achieve the full volume. Specify the amount of time in seconds after each aspiration (a value of 0 can be inputted).
* **Aspiration Height for Recipient tube**: Specify the height (in mm) from the bottom of the tubes in the recipient tube rack the pipette will aspirate from. Change this value if switching between T4, T5, or T6 tubes.
* **Dispense Height for Recipient tube**: Specify the height (in mm) from the bottom of the tubes in the destination tube rack the pipette will dispense at.  
* **P1000 Single GEN2 Mount**: Specify the mount side for the P300 Single GEN2 pipette

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
384b23-tube-transfer
