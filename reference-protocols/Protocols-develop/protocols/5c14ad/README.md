# Lysis Pre-Fill (Salmonella/Listeria)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol allows the user to fill custom adapters according to their specifications (found below):

The user can choose between: Salmonella or Listeria Fill (90µL, 70µL respectively), how many plates to fill (1-9), single channel or multi-channel pipette (P300), and which column to pick up a tip from (row A, to avoid cross contamination).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [P300 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette), or
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Fisherbrand 20-200µL Tips](https://www.fishersci.com/shop/products/fisherbrand-sureone-aerosol-barrier-pipette-tips-20-200-l-beveled-tip-graduated-at-10-50-100-l/02707430)
* [Simport Scientific 500µL Tubes in Custom Holder](http://www.simport.com/en/products/173-t100-1.html)
* [Nest 195mL Reservoir (or similar)](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)


For this protocol, be sure that the correct Lysis Type is selected for correct volume transfers, as well as Pipette Type and Mount.

**Labware Setup**

Slot 1: [Fisherbrand 20-200µL Tips](https://www.fishersci.com/shop/products/fisherbrand-sureone-aerosol-barrier-pipette-tips-20-200-l-beveled-tip-graduated-at-10-50-100-l/02707430)

Slot 2: [Nest Reservoir](https://labware.opentrons.com/nest_1_reservoir_195ml?category=reservoir)

Slot 3 - 11 (loaded sequentially): [Simport Scientific 500µL Tubes in Custom Holder](http://www.simport.com/en/products/173-t100-1.html)

**Using the customization fields below, set up your protocol.**
* Lysis Type (Salmonella/Listeria): Select either Salmonella or Listeria and the corresponding volume (90µL or 70µL, respectively) will be added to each well.
* Pipette Type: Select either `Single Channel` or `Multi Channel`. This will also modify the protocol behavior to the corresponding protocol.
* Pipette Mount: Specify which mount the P300 is on (left or right).
* Number of Plates: Specify how many plates to fill (1-9).
* Tip Pick-Up at (Row A): Specify which column to pick up tip (1-12).

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
5c14ad
