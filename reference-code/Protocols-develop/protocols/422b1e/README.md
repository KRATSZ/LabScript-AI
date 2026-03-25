# Titration Procedure

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Titration
	* Custom Titration


## Description
This titration protocol utilizes a custom labware definition (beaker + stir plate) for use on the OT-2.</br>
The P1000 Pipette (attached to the right mount) will pick up a tip from the tip rack located in slot 11. For each tube in the Opentrons Tube Rack (located in slot 9), the pipette will transfer 2mL to the beaker in slot 4, wait a predetermined amount of time, then transfer 2mL from the beaker in slot 4 to the beaker in slot 8.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* [Opentrons 4-in-1 Tube Rack Set, 6x50mL Top](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [50mL Conical Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-50-ml-centrifuge-tube)
* Custom Beaker + Stir Plate
* Reagents



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 4: Custom Beaker + Stir Plate

Slot 8: Custom Beaker + Stir Plate (Waste Container)

Slot 9: [Opentrons 4-in-1 Tube Rack Set, 6x50mL Top](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [50mL Conical Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-50-ml-centrifuge-tube) containing reagents*</br>
* The P1000 will aspirate liquid from the bottom of the tube, so do not overfill the tube to ensure the pipette does not submerge itself in liquid.</br>

Slot 11: [Opentrons 1000µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol package containing the custom labware definition for the beaker.
2. Upload the labware definition in the [OT App](https://opentrons.com/ot-app). For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
422b1e
