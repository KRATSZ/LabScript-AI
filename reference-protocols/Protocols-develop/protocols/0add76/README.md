# DNA and Water Transfer with CSV File

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol utilizes a CSV (.csv) file to dictate transfers of two reagents (DNA Stock and Water) to a VWR 96-well PCR plate. Simply upload the properly formatted CSV (examples below), set parameters, then download your protocol for use with the OT-2.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P10 Single Pipette]
* [P300 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [GEB 96 Tip Rack 10 µL](https://labware.opentrons.com/geb_96_tiprack_10ul?category=tipRack)
* [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack)
* [VWR Universal Pipet Tips 10ul, XL, Low Retention](https://us.vwr.com/store/catalog/product.jsp?catalog_number=76323-388)
* [VWR Universal Pipet Tips 300ul, Low Retention](https://us.vwr.com/store/catalog/product.jsp?catalog_number=76322-148)
* [VWR Flat 96 Well PCR Plate 200ul](https://us.vwr.com/store/catalog/product.jsp?catalog_number=82006-636)
* [VWR Microplate 96 Square 2ml](https://us.vwr.com/store/product?keyword=75870-792)
* [EK Scientific Reservoir Without Lid 290 mL](https://us.vwr.com/store/catalog/product.jsp?catalog_number=89049-028)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P10 and P50) are attached.

Using the customization fields below, set up your protocol.
* Transfer CSV: Upload your properly formatted (see below) CSV.
* P10 Single Mount: Specify which mount the P10 is on (left or right).
* P300 Single Mount: Specify which mount the P50 is on (left or right).

**Note about CSV**

The CSV should be formatted like so:

`Samples` | `DNA Stock Volume (µL)` | `H20 Stock Volume (µL)` | `Well`

The first row (A1, B1, C1, D1) can contain headers (like above) or simply have the desired information. All of the following rows should just have the necessary information.

**Labware Setup**

Slot 6: EK Scientific Reservoir Without Lid 290 mL

Slot 8: VWR Flat 96 Well PCR Plate 200ul

Slot 9: Opentrons 96 Tip Rack 300 µL

Slot 10: VWR Square Microplate 96 Square 2ml

Slot 11: GEB 96 Tip Rack 10 µL

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Upload your CSV and input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0add76
