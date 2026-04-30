# Viral Nucleic Acid Isolation from Oral and Nasal swabs

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
This protocol isolates nucleic acid using a MagBio CTL lysis buffer and MAG-S1 particle beads suspended in 100% isopropanol. 200µL of sample is pre-loaded into each well within a Kingfisher deep-well plate on the Opentrons magnetic module. The sample undergoes extraction with 2 ethanol washes. The eluate is then transferred to a full-skirted PCR plate along with PCR master-mix for further processing.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module](https://opentrons.com/modules/)
* [P20 Single Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [Opentrons 96 Filter Tip Rack 20 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_20ul?category=tipRack)
* [Opentrons 96 Filter Tip Rack 200 µL](https://labware.opentrons.com/opentrons_96_filtertiprack_200ul?category=tipRack)
* [Opentrons NEST 96 well plate 100ul PCR full skirt](https://labware.opentrons.com/?category=wellPlate)
* [Opentrons NEST 12-Well Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 4-in-1 Tube Rack Set (24-tube insert)](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

For this protocol, be sure that the pipettes (P20 and P300) are attached.

Using the customization fields below, set up your protocol.
* Number of columns: Specify the number of columns of samples loaded onto the NEST deep well plate. Note that runs should only be completed in multiples of full columns (8 samples).
* Sample and lysis buffer mix repetitions: Specify the number of repetitions to mix the sample and lysis buffer as mentioned in Step 1 of the MAGBIO protocol
* Mix repetitions before first magnetic engage: Specify the number of mix repetitions to re-suspend the MAG-S1 particles before use (i.e. "shake well" in Step 3 of the MAGBIO protocol).
* Incubation time: Specify the amount of incubation time to allow RNA to bind to the beads
* Magnetic bead engagement time: Specify the amount of time to engage the magnet for every engagement in protocol
* Aspiration height from bottom of well (removing supernatant): Specify the height from the bottom of the well in which the pipette will aspirate from when removing supernatant.
* Multi_channel pipette aspiration flow rate (ul/s): Specify the aspiration flow rate
* Multi-channel pippette dispense flow rate (ul/s): Specify the dispense flow rate
* Distance from side of well opposite beads (1mm - 4.15mm): Specify the distance from the side of the well opposite the engaged magnetic beads to aspirate from. A value of 4.15mm returns the center of the well, with 1mm returning 1mm from the side of the well opposite the engaged beads.
* Bead drying time: Specify the amount of incubation time for the beads to dry at room temperature while magnetically engaged.
* Bead drying time (with nuclease free water): Specify the amount of time to to dry the beads at room temperature after adding nuclease free water.
* Nuclease water volume: Specify the amount of nuclease free water to add to the beads
* P20 single GEN2 mount: Specify which mount to load the P20 single GEN2 pipette.
* P300 multi GEN2 mount: Specify which mount to load the P300 multi GEN2 pipette.

**Note about 20µL tip racks**

When prompted to replace the 300ul tip racks, be sure to re-load all 3 tip racks as in the original configuration of the deck.

**Labware Setup**

Slots 1: Opentrons Magnetic Module with loaded NEST 96 2mL deep well plate. 200ul of viral sample pre-loaded into each well.

Slot 2, 5: Opentrons 96 Filter Tip Rack 20 µL

Slot 3, 6, 9: Opentrons 96 Filter Tip Rack 200 µL

Slot 4: Opentrons NEST 12-Well Reservoir (empty)

Slot 7: Opentrons 4-in-1 Tube Rack Set. Mastermix loaded into tubes A1, B1.

Slot 8: Opentrons NEST 96 well plate 100ul PCR full skirt

Slot 10: Opentrons NEST 12-Well Reservoir with ethanol loaded

Slot 11: Opentrons NEST 12-Well Reservoir with CTL medium, isopropanol + beads, and nuclease free water loaded

**Note NEST 12-Well Reservoir with Reagents on Slot 11**
The minimum volume of reagents in the NEST 12-Well Reservoir will be calculated dependent on the number of columns specified and displayed in the Opentrons app prior to beginning the run.  

Ethanol is loaded into all 12 wells on the Nest 12-well reservoir on Slot 10.

![Ethanol Reservoir on Slot 10](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5f7d18/genophyl2protocol2readme2ethanol.png)

CTL medium is loaded onto the first two wells, isopropanol + beads onto wells 4-7, and nuclease free water loaded onto well 12 of the Nest 12-Well reservoir on Slot 11.

![Reagent Reservoir on Slot 11](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5f7d18/genophyl+protocol+readme.png)


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
5f7d18
