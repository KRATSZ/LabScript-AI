# PCR Workflow With Thermocycler

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* Complete PCR Workflow

## Description
This protocol transfers buffer and sample to a PCR plate on an Opentrons Thermocycler. Buffer and mastermix is added in between temperature profile steps. Block temperature of the thermocycler is set to the temperature of the last sub-step in each profile incubation step. Lid temperature stays constant throughout the protocol and is specified by the user.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Thermocycler](https://opentrons.com/modules/#thermocycler_module)
* [P20 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [Opentrons 96 Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_tiprack_20ul?category=tipRack)
* [Opentrons 96 Tip Rack 300 µL](https://labware.opentrons.com/opentrons_96_tiprack_300ul?category=tipRack)
* [Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap?category=tubeRack)
* [Opentrons 24 Tube Rack with Eppendorf 2 mL Safe-Lock Snapcap](https://labware.opentrons.com/opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap?category=tubeRack)
* [ThermoFisher PCR Plate 96 Well Non Skirted](https://www.thermofisher.com/order/catalog/product/AB0600?us&en#/AB0600?us&en)






---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P20 and P300) are attached.

Using the customization fields below, set up your protocol.
* Lid Temperature: Specify lid temperature to be set for the duration of the protocol (default 105C).
* Tube rack used: Specify whether you are using 1.5mL or 2mL Eppendorf tube rack.
* Number of Samples in Plate B: Specify the number of samples to be transferred and ultimately cycled on the 96 well plate on the thermocycler.
* Number of tip racks: Specify the number of 20µL tip racks you will have loaded onto the deck.
* P20 Single Mount: Specify which mount the P10 is on (left or right).
* P300 Single Mount: Specify which mount the P50 is on (left or right).

**Note about 20µL tip racks**

You can upload up to 3 Opentrons 20µL tip racks for this protocol in slots 1, 2, and 3, respectively. If only loading one tip rack, load it onto Slot 1. If loading two tip racks, load to Slots 1 and 2 and so forth. The protocol will prompt you to replace tips when tips run out - you will need to reload all tip racks to the original configuration at the start of the protocol.

**Labware Setup**

Slots 1, 2, 3: Opentrons 20µL tip rack(s)

Slot 4: Thermo Fisher 96 well-plate

Slot 5: Opentrons 24 Tube Rack with Eppendorf 1.5 or 2mL Safe-Lock Snapcap

Slot 6: Opentrons 300µL tip rack

Slot 7, 8, 10, 11: Opentrons Thermocycler loaded with Thermo Fisher 96 well-plate loaded


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
2d9a0c
