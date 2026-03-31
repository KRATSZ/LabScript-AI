# Ligation Sequencing Kit: Adapter Ligation and Clean-Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Oxford Nanopore Ligation Sequencing Kit

## Description
This protocol automates the Adapter Ligation and Clean-Up portion for preparing sequencing libraries in the Oxford Nanopore Ligation Sequencing Kit. There is a first part of this protocol for the [DNA Repair and End-Prep](https://protocols.opentrons.com/protocol/516336).

Explanation of parameters below:
* `Number of Samples`: Specify the number of samples in multiples of 8 (Max: 96).
* `P300 Multichannel GEN2 Mount Position`: Specify the mount position of the P300 Multichannel.
* `P300 Single GEN2 Mount Position`: Specify the mount position of the P300 Multichannel.
* `Magnetic Module Engage Height from Well Bottom (mm)`: Specify the height of the magnets from the bottom of the well.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [ThermoFisher 96 Well 0.8mL Polypropylene Deepwell Storage Plate](https://www.thermofisher.com/order/catalog/product/AB0765#/AB0765)
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr/)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

### Pipettes
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 GEN2 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/516336/516336_deck_part2.png)

### Reagent Setup

![reservoirs](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/516336/516336_reagents_part2.png)

---

### Protocol Steps

1. Transfer master mix and put into PCR plate, and mix each time.
2. Transfer Samples from Sample PCR Plate to MIDI plate on Magnetic Module.
3. Resuspend AMPure beads by pipette mixing and transfer to MIDI plate on magnetic module.
4. Pause for Hula Mixer and Spin Down the plate.
5. Engage Magnetic Module for 5 minutes and then remove supernatant.
6. Wash the beads with fragment buffer (Long or Short). Mixing the buffer, engage magnetic module to allow beads to pellet and then remove supernantant.
7. Repeat Step 6.
8. Pause and Spin Down the samples.
9. Place on magnetic module and engage magnet for 1 minute.
10. Remove supernatant from samples.
11. Disengage magnet and add 15 uL of elution buffer.
12. Incubate for 10 minutes at room temperature.
13. Engage magnet for 5 minutes to allow beads to pellet and the eluate is clear.
14. Pause and remove old BioRad PCR plate on Slot 2 with a new Bio Rad PCR Plate.
15. Transfer 15 uL of eluate containing the new NDA library into the new BioRad PCR plate.


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
516336-part-2