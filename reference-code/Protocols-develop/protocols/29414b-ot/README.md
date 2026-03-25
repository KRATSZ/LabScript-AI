# Single-/Multi-Channel Calibration - Opentrons Tips

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Getting Started
	* Calibration


## Description
This protocol is designed for testing calibration of the OT-2 with a custom tube holder, holding 500µL tubes from Simport Scientific, with Opentrons Tips. This protocol can be used for testing the **P300 Single Channel Pipette** or the **P300 Multi Channel Pipette**.

If testing the P300 Single Channel Pipette, the robot will transfer 5µL from A1 to A2, A3, and A4 with a 200µL filter tip. The robot will then make transfers with 200µL filter tips, first 50µL from B1 to B2, B3, and B4; then 200µL from C1, to C2, C3, and C4.

If testing the P300 Multi Channel Pipette, the robot will transfer 5µL from column 1 to column 2, 3, and 4 with 200µL filter tips. The robot will then make transfers with 200µL filter tips, first 50µL from column 5 to column 6, 7, and 8; then 200µL from column 9 to column 10, 11, and 12.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Simport Scientific 500µL Tubes in Custom Holder](http://www.simport.com/en/products/173-t100-1.html)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


For this protocol, be sure that the correct pipette (P300 Single or Multi) is attached for the intended test case.

**Labware Setup**

Slot 1: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

Slot 3: [Simport Scientific 500µL Tubes in Custom Holder](http://www.simport.com/en/products/173-t100-1.html)

**Using the customization fields below, set up your protocol.**
* Pipette Type: Select either `Single Channel` or `Multi Channel`. This will also modify the protocol behavior to the corresponding test protocol.
* Pipette Mount: Specify which mount the P300 is on (left or right).
* Touch Tip (After Aspiration): Select `yes` to perform a touch-tip after aspirating from source well.
* Touch Tip (After Dispense): Select `yes` to perform a touch-tip after dispensing into source well.

---
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
29414b-ot
