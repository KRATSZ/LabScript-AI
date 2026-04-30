# Custom Distribute Liquids Function

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Distribution

## Description
The distribute function in our Python API allows volumes from the same source well to be combined within the same tip and allow for multiple dispenses to multiple locations. However, sometimes additional parameters may be necessary such as overage volume, custom blowout locations, and air gaps. This protocol provides a custom distribute function that can be used to implement additional parameters and custom functionalities that fall outside of the default Python API distribute function.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes) and corresponding [Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [Corning 24 Well Plate 3.4 mL Flat](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Costar%C2%AE-Multiple-Well-Cell-Culture-Plates/p/3738)
* [Corning 6 Well Plate 16.8 mL Flat](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Costar%C2%AE-Multiple-Well-Cell-Culture-Plates/p/3335)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Usage:** `distribute_custom(pipette, vol, source, dest, overage, blowout, air_gap)`

Input:
```
distribute_custom(p300, 50, plate1['A1'], plate2.rows_by_name()['A'], 30, trash_plate['A1'], 10)
```

Output:
```
Picking up tip from A1 of Opentrons 96 Tip Rack 300 µL on 4
Aspirating 230.0 uL from A1 of Plate 1 on 1 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A1 of Plate 1 on 1 at 92.86 uL/sec
Dispensing 60.0 uL into A1 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A1 of Plate 2 on 2 at 92.86 uL/sec
Dispensing 60.0 uL into A2 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A2 of Plate 2 on 2 at 92.86 uL/sec
Dispensing 60.0 uL into A3 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A3 of Plate 2 on 2 at 92.86 uL/sec
Dispensing 60.0 uL into A4 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A4 of Plate 2 on 2 at 92.86 uL/sec
Blowout at A1 of Trash Plate on 3
Dispensing 300.0 uL into A1 of Trash Plate on 3 at 92.86 uL/sec
Aspirating 130.0 uL from A1 of Plate 1 on 1 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A1 of Plate 1 on 1 at 92.86 uL/sec
Dispensing 60.0 uL into A5 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A5 of Plate 2 on 2 at 92.86 uL/sec
Dispensing 60.0 uL into A6 of Plate 2 on 2 at 92.86 uL/sec
Air Gap
Aspirating 10.0 uL from A6 of Plate 2 on 2 at 92.86 uL/sec
Blowout at A1 of Trash Plate on 3
Dispensing 300.0 uL into A1 of Trash Plate on 3 at 92.86 uL/sec
Dropping tip into A1 of Opentrons Fixed Trash on 12
```

In this example 50 uL are distributed to wells across row A on `plate2` from well A1 in `plate1`. The function will account for the 30 uL overage volume as well as the 10 uL air gaps after each dispense step. It will take those parameters into consideration and determine the maximum volume to aspirate before performing multiple dispenses. Once it reaches the maximum dispenses, it will blowout into the specified blowout location: `trash_plate['A1']` (A1 of the Trash Plate)


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol and unzip if needed.
2. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes

If you’d like to request a protocol supporting multiple destination plates or require other changes to this script, please fill out our [Protocol Request Form](https://opentrons-protocol-dev.paperform.co/). You can also modify the Python file directly by following our [API Documentation](https://docs.opentrons.com/v2/). If you’d like to chat with an automation engineer about changes, please contact us at [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
1c086c