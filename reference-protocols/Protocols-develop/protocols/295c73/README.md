# Accel-Amplicon® Plus EGFR Pathway Panel



## Categories
* NGS Library Prep
	* Accel-Amplicon Plus EGFR Pathway Panel


## Description

With this protocol, your [OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2) can prepare up to 24 libraries [Swift accel-amplicon-plus-egfr-pathway-panel](https://swiftbiosci.com/accel-amplicon-plus-egfr-pathway-panel/).



---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase consumables, labware, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)


* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.15.0 or later)](https://opentrons.com/ot-app/)
* [Swift accel-amplicon-plus-egfr-pathway-panel](Swift accel-amplicon-plus-egfr-pathway-panel)
* [Opentrons Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)
* [Opentrons Temperature Module with Aluminum Block Set](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or Opentrons P50 Single-Channel Pipette*
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/products/single-channel-electronic-pipette)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* DNA samples resuspended in 10 uL Low EDTA TE.

---




__Using the customizations fields, below set up your protocol.__
* **Number of Samples**: Specify the number of samples (choose from 1 up to 24) you'd like to run.



**Note**: Pre-cool the temperature module to 4 degrees C and pre-heat the thermocycler block (98) and thermocycler lid (105) using settings in the OT app prior to running this protocol. The initial DNA sample plate (with 10 ul samples in column order A1-H1, A2-H2 etc.) is placed on deck slot 1. The aluminum block on slot 5 should be pre-chilled for the master mix and again for the indexing reaction mix, otherwise at room temperature. After automated setup on the 4 degree temperature module, the PCR plate is manually transferred from the temperature module to the pre-heated 98 degree thermocycler block. The OT-2 deck lights will go off to signal pauses occurring when reagents are needed on the OT-2 deck. The final 20µL elution will be transferred to a fresh output plate on the temperature module and held at 4 degrees.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Input your protocol parameters (specify the number of initial DNA samples 1-24).
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app). Be sure to use OT App settings in advance of the protocol run to pre-cool the temperature and thermocycler modules to 4 degrees.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".
7. Deck lights will momentarily go off to indicate a pause when reagents should be added to the OT-2 deck:
   a.  Multiplex Mastermix (A1 of pre-chilled block)
   b.  Beads (A1 of room temp block) and 80% ethanol (A1 of reservoir).
   c.  Index plate (slot 1) and indexing rxn mix (A1 of pre-chilled block).
   d.  PEG NaCl (A1 of room temp block) and post PCR TE (A5 of reservoir).

###### Internal
295c73
