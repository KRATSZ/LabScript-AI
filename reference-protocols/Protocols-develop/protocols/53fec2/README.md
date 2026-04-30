# Beckman Coulter AMPure XP PCR Cleanup and Size Selection

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
    * Cleanup

## Description
This is a flexible protocol accommodating Beckman Coulter AMPure XP PCR Cleanup and Size Selection. It consists of the following major sections:
* binding beads pre-addition
* sample pooling and mixing with binding beads
* 2x ethanol wash
* final elution in H2O

Samples to be pooled should be loaded in 2 PCR plates on the deck. For reagent layout used in this protocol, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 7) to the elution PCR plate (slot 8). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Eppendorf 96-deepwell plate 500µl
* Eppendorf 96-well PCR plate 200µl, skirted
* Eppendorf 1-channel automation reservoirs 30ml/100ml
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P300 Multi-Channel GEN2 Electrnoic Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

### Reagents
* [Beckman Coulter AMPure XP for PCR Purification](https://www.beckman.com/reagents/genomic/cleanup-and-size-selection/pcr)

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/53fec2/decksetup.png)

### Protocol Steps
1. Binding buffer is mixed and pre-added to the magnetic module plate.
2. Corresponding columns from each sample plate are consolidated into the magnetic module.
3. Supernatant is removed, and each sample is washed 2x with ethanol, without bead resuspension.
4. Beads are resuspended in H2O.
5. The beads are separated, and final elutions are transferred to a clean PCR plate.

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
53fec2
