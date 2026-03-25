# RNA Extraction with Magnetic Beads (no tip waste)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
This protocol isolates nucleic acid preloaded onto a NEST 96 deep well plate premixed with magnetic beads. The sample undergoes extraction with one wash step. The eluate is then transferred to a full-skirted PCR plate for further processing. Tips are parked throughout the protocol for potential reuse. No tips are discarded in the trash.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://opentrons.com/modules/)
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)
* [Opentrons NEST 96 well plate 100ul PCR full skirt](https://labware.opentrons.com/?category=wellPlate)
* [Opentrons NEST 96 deep well plate 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [Opentrons NEST 12-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons NEST 1-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-1-well-reservoir-195-ml)




---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the P300 pipette is attached.

Using the customization fields below, set up your protocol.
* Number of samples: Specify the number of samples loaded onto the NEST deep well plate. Note that runs should only be completed in multiples of full columns (8 samples).
* Aspiration height from bottom of well (removing supernatant): Specify the height from the bottom of the well in which the pipette will aspirate from when removing supernatant.
* Multi_channel pipette aspiration flow rate for mixing (ul/s): Specify the aspiration flow rate for all mix steps.
* Multi_channel pipette dispense flow rate for mixing (ul/s): Specify the dispense flow rate for all mix steps.
* Distance from side of well opposite beads (1mm - 4.15mm): Specify the distance from the side of the well opposite the engaged magnetic beads to aspirate from. A value of 4.15mm returns the center of the well, with 1mm returning 1mm from the side of the well opposite the engaged beads.
* P300 multi GEN2 mount: Specify which mount to load the P300 multi GEN2 pipette.

**Note About Reagents**
Bind buffer + Etoh, wash buffer, and TE in the Nest 12 well reservoir should be loaded into their respective wells prior to the protocol. The minimum volume of which (dependent on how many samples are being run) can be found below.

![Binding Buffer + Etoh](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69db93/bufferetoh.png)

![Wash Buffer](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69db93/wash.png)

![TE](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69db93/te.png)


**Labware Setup**

Slots 1: Opentrons Magnetic Module with loaded NEST 96 2mL deep well plate. 400ul sample and pre-mix loaded in each well.

Slot 2: Nest 12 well reservoir with binding buffer + Etoh, wash buffer, and TE loaded.

Slot 3: Opentrons NEST 96 well plate 100ul PCR full skirt.

Slot 4, 7, 10: Opentrons 96 Filter Tip Rack 200 µL (empty for parking).

Slot 5, 6, 8, 9: Opentrons 96 Filter Tip Rack 200 µL.

Slot 11: Nest 1-well reservoir


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
69db93
