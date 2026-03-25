# Sample Plate Filling 96 Wells to 384 Well Plate

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol automates the transfer of PCR mix and samples from up to four 96-well elution plates to a 384-well plate. It follows a specific format detailed in the image below. Columns from the 96 well elution plates correspond to specific wells on the 384 well plate. Each elution plate contains a control that is also transferred into the 384-well plate. For runs that have less than four plates, the controls will need to be added manually for the corresponding elution plate.

**96 Well Elution Plate Format**:

![96-Well Elution Plates](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6e2509/elution-plates.png)

**384 Well Plate Format**:

![384-Well Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6e2509/384-well-plate.png)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 4.0.0 or later)](https://opentrons.com/ot-app/)
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 96 Filter Tip Rack 20 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Thermofisher 384 well optical PCR plate](https://www.thermofisher.com/order/catalog/product/4309849#/4309849)
* [Molgen 96 Well Elution Plate](https://molgen.com/)
* [Opentrons NEST 12-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the P20 pipette is attached.

Using the customization fields below, set up your protocol.
* P20 Multichannel Mount: Choose the mount position of your P20 multichannel pipette.
* Number of samples: Input the total number of samples in all four plates. Supports up to 384 samples.
* PCR Mix Transfer Volume: Input the volume of PCR mix to transfer per well. Default is 7.5 uL.
* Sample Transfer Volume: Input the volume of sample to transfer per well. Default is 5 uL.
* Sample Aspiration Height Above Bottom of the Well: Specify the height from the bottom of the well in which the pipette will aspirate.
* Sample Dispensing Height Above Bottom of the Well: Specify the height from the bottom of the well in which the pipette will dispense.
* Master Mix Aspiration Height Above Bottom of the Well: Specify the height from the bottom of the well in which the pipette will aspirate.
* Master Mix Dispensing Height Above Bottom of the Well: Specify the height from the bottom of the well in which the pipette will dispense.


**Note About Reagents:**
PCR Mix should be placed into column A1 of the 96 well plate.


**Labware Setup**

Slot 1: Plate 1

Slot 2: Plate 2

Slot 4: Plate 3

Slot 5: Plate 4

Slot 3: 384 Well PCR Plate

Slot 6:  96 Well Plate (PCR Mix in Column A1)

Slots 7 - 11: Opentrons 96 Filter Tip Rack 20 uL

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
6e2509