# Atila iAMP COVID-19 Detection Kit - Saliva (Pt.1)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
* This protocol reformats 10ul of saliva samples from tubes to a 96 well plate. Tube racks should be placed in order of the slot numbers on the deck, (1, 2, 3,...,7). The pipette will access each tube rack in this order beginning from tube rack 1 on slot 1. The pipettes will access each tuberack by column (A1, B1, C1, A2, B2, C2...), meaning a 94 sample run would have all tube racks in slots 1-6 filled, with 4 tubes in A1, B1, C1, A2 of slot 7.

Explanation of complex parameters below:
* `Number of Samples (1-96)`: Specify the number of samples for this run (1-96).
* `Reaction plate`: Specify whether using the non-skirted or half-skirted reaction plate on slot 9. Slot 8 should always use a non-skirted plate.
* `P20 Pipette Mount`: Specify which mount (left or right) to host the P20 Single-Channel Pipette.

---

### Labware
* [Opentrons 4-in-1 Tube Racks](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*1j3fcfo*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0NTAyNjkwOC43MTUuMC4xNjQ1MDI2OTA4LjA.&_ga=2.189248875.1378610984.1644865280-1365106149.1621361358)
* Custom 0.12 and 0.2mL 96 well plates

### Pipettes
* [Opentrons P20 Single-Channel Pipette](https://opentrons.com/pipettes/)

### Reagents
* [iAMP® COVID-19 Detection Kit](https://www.fda.gov/media/136870/download)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/atila/Screen+Shot+2022-03-03+at+11.56.57+AM.png)

### Reagent Setup
* If running more than 6 columns (40 samples), mastermix should be dispensed evenly between columns 1 and 2 of the mastermix plate on slot 8. If running less than 40 samples, mastermix should only be in column one of the mastermix plate.
* Controls should always be in G12 and H12 of the mastermix plate on slot 8.


---

### Protocol Steps
1. 6ul of saliva sample is added to the wells on the 96 plate from the tuberack(s).

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
atila-saliva-pt1
