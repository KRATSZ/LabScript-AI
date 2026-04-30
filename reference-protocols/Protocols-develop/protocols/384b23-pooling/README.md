# Sample Pooling Down Column

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Normalization
	* Normalization and Pooling


## Description
This protocol pools 100µL from wells across each row to the recipient tube in column 6 of the respective row (total of 500µL in each recipient tube).


---
![Materials](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 200µL Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 200µL Filter Tips](hhttps://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* Custom Opentrons 6x5 tube racks



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1 (if applicable): Tuberack A

Slot 2 (if applicable): Tuberack B

Slot 4: Opentrons 200µL Filter Tip Rack

</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Using Tuberack A (tubes T1, T2, T3)**: Specify if Tuberack A will be pooled.
* **Tuberack A tubes**: Specify whether you will be populating Tuberack A with T1-T3 tubes or T7 tubes. Leave as is if not using Tuberack A.
* **Number of pooling rows for Tuberack A**: Specify how many rows to pool (1-5).
* **Using Tuberack B (tubes T4, T5, T6)**: Specify if Tuberack B will be pooled
* **Tuberack B tubes**: Specify whether you will be populating tuberack B with T4 & T5 tubes or T6 tubes. Leave as is if not using Tuberack B.
* **Number of pooling rows for Tuberack B**: Specify how many rows to pool (1-5).
* **Delay Time after Aspirating (in seconds)**: Since saliva is being transferred, often times a delay after aspiration allows the pipette to achieve the full volume. Specify the amount of time in seconds after each aspiration (a value of 0 can be inputted).
* **P300 Single GEN2 Mount**: Specify the mount side for the P300 Single GEN2 pipette
* **P300 Single GEN2 Mount**: Specify the mount side for the P300 Single GEN2 pipette

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
384b23-pooling
