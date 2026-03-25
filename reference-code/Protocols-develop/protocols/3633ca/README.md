# Ethanol Transfer

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol adds and removes ethanol to a plate on the Magnetic Module.</br>
</br>
The protocol adds 150µL of ethanol to each well, using the P300 Multi-Channel pipette, waits 30 seconds, then removes the ethanol and discards the tips. After doing this a second time, the P20 Multi-Channel pipette aspirates 15µL of liquid from the wells and disposes of it.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* (2) [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slot 1: [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir) with ethanol in slots 1-4

Slot 3: [Opentrons 20µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 4: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Well Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 7: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

Slot 10: [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **P300-Multi Pipette Mount**: Select which mount (left or right) the P300-Multi is attached to.
* **P20-Multi Pipette Mount**: Select which mount (left or right) the P20-Multi is attached to.



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol. For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3633ca
