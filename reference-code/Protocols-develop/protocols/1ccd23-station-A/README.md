# Generic Sample Plating Protocol (Station A)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Covid Workstation
	* Sample Plating


## Description
This protocol plates samples from custom or standard tuberacks to a NEST 96-deepwell plate. 10µl proteinase K and 10µl internal control are then added to each sample. Samples are transferred to the plate first down each column, then across each row (A1, B1, C1, ...H1, A2, B2, C2, etc.)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) or custom tuberack
* [NEST 96 Deepwell Plate 2mL](http://www.cell-nest.com/page94?product_id=101&_l=en)
* Sample Tubes


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

2ml tubeblock on temperature module (slot 1):  
* proteinase K: A1
* internal control: B1

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
generic_station_A
