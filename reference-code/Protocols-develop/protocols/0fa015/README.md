# Plate Filling QE in NEST Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol fills[NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) with QE using a [GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes).</br>
</br>
The protocol can fill up to 9 plates and will dispense 10µL of QE into each well</br>
</br>
This protocol is based largely on [this protocol](https://develop.protocols.opentrons.com/protocol/17cb2d) and will employ similar behaviors (touch tip after aspiration, blow out, and aspiration at the top of the well to prevent cross-contamination).


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel Pipette, GEN2](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* Reagents (QE)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1 - 9: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)

Slot 10: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 11: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)</br>
A1: QE (for plates 1-5)</br>
A2: QE (for plates 6-9)</br>

</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Pipette Type**: Select which GEN2 Multi-Channel Pipette (p300 or p20) will be used
* **Pipette Mount**: Select which mount (left or right) the Multi-Channel Pipette is attached to
* **Number of Plates (1-9)**: Specify the number of plates to fill



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
0fa015
