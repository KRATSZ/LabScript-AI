# Liquid Deposition on Custom Surface

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Slide Spotting

## Description

This protocol performs simple spotting transfers of variable volume to a custom plate occupying slots 1, 2, 3, 4, 5, 6, 7, 8, & 9 of the OT-2 deck.

**Calibration**  
The user should calibrate to the top left-most spot of the top left-most grid on the shaker (A). The pipette tip should be calibrated to just above the center of this spot during calibration.

**Offsets**  
Offsets are used to define the location of each additional grid. The offset of the top left-most spot of each additional grid (B) relative to the calibration point (A) will be specified in a pair of x- and y-coordinates via 	`.csv` file input, as in the following example (be sure to include the header line):
```
x offset (in mm),y offset (in mm)
50,0
0, 70
50, 70
```

The above example will transfer to 3 grids with specified offsets in addition to the starting grid to which the protocol is calibrated.

You can also download and modify [this template](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6a77d9/ex.csv).

![surface](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6a77d9/surface.png)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons 20µl Tiprack](https://shop.opentrons.com/collections/opentrons-tips)
* [USA Scientific 96 Deep Well Plate 2.4 mL](https://labware.opentrons.com/usascientific_96_wellplate_2.4ml_deep)


For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

* If using a multi-channel pipette, liquids A-D should be in reservoir wells A1-D1, and liquids E-H should be in reservoir wells E2-H2.  
* If using a single-channel pipette, liquids A-H should be in reservoir wells A1-H1.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
6a77a9
