# Capping Assay: Steps 3-6

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Nucleic Acid Extraction

## Description

Links:
* [Steps 1-2 (annealing preparation and digestion)](./7062c9)
* [Steps 3-6 (extraction)](7062c9-2)

This is a flexible protocol accommodating a multi-step nucleic acid extraction. The protocol is broken down into the following main parts:
* magnetic beads pre-wash
* beads binding to sample
* beads washing
* final elution

Before running the protocol, 100µl of beads in buffer should be pre-loaded on the magnetic module in a NEST 96-deepwell plate. For reagent layout, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 4) to the elution PCR plate (temperature module, slot 1). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

Explanation of complex parameters below:
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* [NEST 12 Well Reservoir 15 mL](https://labware.opentrons.com/nest_12_reservoir_15ml)
* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://labware.opentrons.com/nest_96_wellplate_100ul_pcr_full_skirt)
* [NEST 96 Deepwell Plate 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep)
* [Opentrons 96 Filter Tip Rack 200 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P300 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)

---

### Deck Setup
This example starting deck state shows the layout for 24 samples:  
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/7062c9/deck2-2.png)

* pink on starting sample plate: 110µl annealed and digested samples
* green on reagent reservoir: buffer 2 (wash buffer)
* blue on reagent reservoir: water
* purple on reagent reservoir: magnetic beads
* orange on reagent reservoir: buffer 3 (elution buffer)

---

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
7062c9
