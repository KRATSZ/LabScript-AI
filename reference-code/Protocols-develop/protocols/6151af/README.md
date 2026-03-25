# Sample Plating Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol automates sample plating from collection tubes to a 96-deepwell plate.  

Using a [Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette), this protocol will transfer the user-specified volume from sample tubes placed in the [Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) into a 96-well plate. Samples are transferred top to bottom, and then left to right (rack 1 tube A1 to plate well A1, rack 1 tube B1 to plate well B1, rack 1 tube C1 to plate well C1, rack 1 tube A2 to plate well D1, etc).

If you have any questions about this protocol, please email our Applications Engineering team at [protocols@opentrons.com](mailto:protocols@opentrons.com).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.1.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons P300 GEN2 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 200µl Filter/300µl Standard Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 3x5 15ml tube insert for [Avantik 3ml Viral Transport Medium Tubes #GL4692](https://www.avantik-us.com/specimen-handling/vtm-3ml-50-pack.asp)
* [NEST 96 Deepwell Plate 2mL](http://www.cell-nest.com/page94?product_id=101&_l=en)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6151af
