# Cherry Picking PCR Prep with CSV File

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol transfers samples from a source plate to one of two target plates (to later undergo PCR) as specified in the uploaded CSV file. Samples from each well in the source plate are distributed to its corresponding target plate 6 columns apart. In the case that one of the target plates is filled, the user is prompted to replace it and resume the protocol. In the case that the source plate is depleted, the user is prompted to replace the source plate and upload its respective CSV file to this webpage, download, and run again. In the latter case, the OT-2 "remembers" what wells on the target plate are already filled when a new source plate is introduced (unless user resets the counter - see below). User will also be prompted to replace tip racks during a run if applicable.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P20 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* ThermoScientific 96-well Plate 200µl






---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P20 and P300) are attached.

Using the customization fields below, set up your protocol.
* Source Plate CSV: Upload a CSV corresponding with the source plate loaded onto the deck.
* Transfer Volume: Specify the volume (µL) desired for each well in target plates
* P20 Single Mount: Specify which mount the P10 is on (left or right).
* Reset Counter: Reset the counter if running with empty target plates. Do not reset the counter if wells in target plate from last run are to be tracked.

**Note about CSV**

The CSV should be formatted like so:

`Samples ID` | `Sample Type` | `ct_value` | `Plate Name (ex. A:1)` | `Plate Position` | `Target Plate (25 or 30)` | `Transfer ("done" or leave blank)`

The first row should contain headers (like above). All of the following rows should just have the necessary information.

**Labware Setup**

Slots 1: Custom Endura Source Plate on Opentrons 96 well Aluminum Block

Slot 2: ThermoScientific 96-well 25-Cycle Target Plate

Slot 4: ThermoScientific 96-well 30-Cycle Target Plate

Slot 5: Opentrons 96 Filter Tip Rack 20 µL


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
1c8468
