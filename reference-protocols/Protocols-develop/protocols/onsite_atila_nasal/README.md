# Atila iAMP COVID-19 Detection Kit - Nasal

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
* This protocol preps a 96 well plate with buffer, sample, and mastermix for PCR. See below for details on reagent setup, protocol steps, etc. Tube racks should be placed in order of the slot numbers on the deck, (1, 2, 3,...,7). The pipette will access each tube rack in this order beginning from tube rack 1 on slot 1. The pipettes will access each tuberack by column (A1, B1, C1, A2, B2, C2...), meaning a 94 sample run would have all tube racks in slots 1-6 filled, with 4 tubes in A1, B1, C1, A2 of slot 7.

* If running a full plate (94 samples), the protocol will use the multi-channel pipette to dispense mastermix to all 96 wells. For SBM, it will use the multi-channel to dispense into the first 11 columns, and then the single-channel to dispense into the first 6 wells of the 12th column. If running less than 94 samples, say 12 for example, the protocol will use the multi-channel to dispense mastermix and SBM into the first column, then the single channel to dispense to the first four wells of column 2, then finally mastermix and SBM into G12, H12. Note, that extra SBM and mastermix should be placed in wells 1-7 depending on the number of samples.

Explanation of complex parameters below:
* `Number of Samples (1-94)`: Specify the number of samples for this run (1-94).
* `Reaction plate`: Specify whether using the non-skirted or half-skirted reaction plate on slot 9. Slot 8 should always use a non-skirted plate.
* `P20 Single/Multi Pipette Mounts`: Specify which mount (left or right) to host each pipette.

---

### Labware
* [Opentrons 4-in-1 Tube Racks](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*1j3fcfo*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0NTAyNjkwOC43MTUuMC4xNjQ1MDI2OTA4LjA.&_ga=2.189248875.1378610984.1644865280-1365106149.1621361358)
* Custom 0.12 and 0.2mL 96 well plates

### Pipettes
* [Opentrons P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [Opentrons P20 Multi-Channel Pipette](https://opentrons.com/pipettes/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/atila/pt2/Screen+Shot+2022-02-16+at+1.34.30+PM.png)

### Reagent Setup
* SBM should be distributed in column 1, and mastermix in column 2.
* Controls should always be in G12 and H12 of the mastermix plate on slot 8.


---

### Protocol Steps
1. SBM is added to the reaction plate up to the number of samples specified.
2. Samples are added to the plate and mixed 3 times with SBM.
3. 15 minute incubation period.
2. Mastermix is added to the reaction plate up to the number of samples specified.
3. Controls are added to G12 and H12 of the reaction plate.

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
atila-nasal
