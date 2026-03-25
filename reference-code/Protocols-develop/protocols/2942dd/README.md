# Custom Transfer From CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Plate Filling

## Description

This protocol uses a p300 single-channel pipette to transfer custom volumes of serum reagent from specified locations in four Opentrons 24-tube racks into specified tubes held in a 96-well rack. A p20 single-channel pipette is then used to tranfer a custom volume of RNase A and 20 percent Tween 20 to the same 96-tube rack locations. Finally, destination tube contents are mixed and the tubes are held at room temperature for 30 minutes. Volumes, rack locations and well locations are specified in a csv file uploaded at the time of protocol download.

Links:
* [example input csv](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2942dd/example.csv)
* [Fluidx rack and 1 mL tubes](https://www.azenta.com/products/1.0ml-tri-coded-tube-96-format-external-thread#specifications)
* [MTC Bio MTC-3220-SG tubes](http://mtcbiotech.com/product/clearseal-screw-cap-microcentrifuge-tubes/)

## Protocol Steps

Set up: Place up to four Opentrons 24-tube racks containing MTC Bio MTC-32220-SG 2 mL tubes in deck slots 7, 4, 1, 8 (racks 1-4 placed in that order) and a Fluidx 96-tube rack containing 1 mL Fluidx tubes in deck slot 9. 20 uL Opentrons filter tips in deck slots 5, 11. 200 uL Opentrons filter tips in deck slot 10.

The OT-2 will perform the following steps:
1. Use the p300 single to transfer a specified volume of serum reagent from specified locations in the 24-tube racks to specified tubes in the 96-tube rack according to the uploaded csv file.
2. Use the p20 single to transfer a specified volume of RNaseA to specified tubes in the 96-tube rack.
3. Use the p20 single to transfer a specified volume of 20 percent Tween 20 to specified tubes in the 96-tube rack. Mix.
4. Notify the user after a 30 minute room temperature incubation is complete.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 and Single-Channel p300 Pipettes](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Filter Tips for the p20 and p300 Pipettes](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2942dd/layout.png)

* Opentrons 200ul filter tips (Deck Slot 10)
* Opentrons 20ul filter tips (Deck Slots 5,11)
* 96-tube Fluidx rack with 1 mL Fluidx tubes (Deck Slot 9)
* 24-tube Opentrons rack with MTC-3220-SG 2 mL tubes  (Deck Slots 7,4,1,8)

![RNase and Tween](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2942dd/Screenshot+RNase+and+Tween.png)

![input csv data and file format](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2942dd/Screenshot+example+csv.png)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to indicate starting volume and location for the RNase and Tween, indicate the number of mix repeats to use, and upload the input csv file (containing info about plate locations, well locations and volumes for the transfers to be performed-see example for data and file format).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2942dd
