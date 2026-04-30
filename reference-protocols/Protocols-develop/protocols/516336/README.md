# Ligation Sequencing Kit: DNA Repair and End-Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Oxford Nanopore Ligation Sequencing Kit

## Description
This protocol automates the DNA Repair and End Prep portion for preparing sequencing libraries in the Oxford Nanopore Ligation Sequencing Kit. The second part of this protocol can be found here: [Adapter Ligation and Clean-Up](https://protocols.opentrons.com/protocol/516336-part-2)</br>
</br>
**Note**: The protocol was updated on September 22nd, 2022
</br>

Explanation of parameters below:
* `Number of Samples`: Specify the number of samples in multiples of 8 (Max: 96).
* `P300 Multichannel GEN2 Mount Position`: Specify the mount position of the P300 Multichannel.
* `P300 Single GEN2 Mount Position`: Specify the mount position of the P300 Multichannel.
* `Magnetic Module Generation`: Specify whether using Gen 1 or Gen 2 magnetic module.
* `Magnetic Module Engage Height from Well Bottom (mm)`: Specify the height of the magnets from the bottom of the well.

---

### Modules
* [Magnetic Module (GEN1)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
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
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/516336/516336_new_layout.png)

### Reagent Setup

![reservoirs](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/516336/516336_reagents.png)

---

### Protocol Steps
0. Cool Temperature Module to 6C
1. Transfer master mix and put into PCR plate
2. Mix plate and pause for spin down step. Afterwards, Pre-Heat Thermocycler to 20C and Lid Temperature to 70C.
3. Incubate on Thermocycler at 20C for 5 mins and 65C for 5 mins
4. Resuspend AMPure beads by pipette mixing
5. Transfer samples from BioRad Plate on TC to MIDI Plate on Mag Mod
6. Add 60 uL of AMPure XP to the samples on MIDI Plate on Mag Mod
7. Mix samples on MIDI plate with pipette
8. Pause step for Hula mixer
9. Pause step for spin down
10. Engage magnet and delay for 5 minutes for beads to pellet
11. After 5 minutes, while engaged, remove supernatant
12. While engaged, wash beads with 200 uL of ethanol
13. Remove ethanol/supernatant. Discard tip.
14. Repeat 12-13
15. Pause for spin down.
16. While engaged, remove any residual ethanol. Delay for 30 seconds for drying.
17. Disengage mag mod and add 61 uL of nuclease-free water. Delay for 2 mins at room temp.
18. Engage magnet until eluate is clear (5 minutes)
19. Transfer 61 uL of eluate into Bio-Rad PCR Plate (Slot 2) for part 2.


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
516336
