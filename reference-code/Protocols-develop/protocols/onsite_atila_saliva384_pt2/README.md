# Atila iAMP COVID-19 Detection Kit - Saliva (Pt.2)

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
* This protocol transfer SRM and saliva sample to a 384 well plate with one mix repetition. 4 plates are loaded into one 384 well plate. If running less than 4 full plates, SRM will still be transferred to the last two wells in the 384 well plate (controls). NOTE: positive and negative controls are to be added manually after the protocol into the last two wells. See below for plate setup.

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples for each plate.
* `Reaction plate`: Specify whether using the non-skirted or half-skirted reaction plate on slot 9. Slot 8 should always use a non-skirted plate.
* `P20 Pipette Mount`: Specify which mount (left or right) to host the P20 Single and Multi-Channel Pipettes.

---

### Labware
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*1j3fcfo*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0NTAyNjkwOC43MTUuMC4xNjQ1MDI2OTA4LjA.&_ga=2.189248875.1378610984.1644865280-1365106149.1621361358)
* [NEST 2mL 96, Deepwell Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)

### Pipettes
* [Opentrons P20 Single-Channel Pipette](https://opentrons.com/pipettes/)
* [Opentrons P20 Multi-Channel Pipette](https://opentrons.com/pipettes/)


---

### Deck Setup
Plate 4 (slot 2) should only have 94 samples to allow room for controls. Please refer to the following diagram for how samples are loaded from each of the four quadrants onto the 284 plate with the multi-channel. Any unfilled columns will switch to the single channel. SRM is added to control wells O24 and P24.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1fcf02/Screen+Shot+2022-03-08+at+2.41.54+PM.png)

### Reagent Setup
* SRM should be placed only in column 1 of the deepwell plate.


---

### Protocol Steps
1. 13ul of SRM is added to all wells which will receive sample, or control.
2. 2ul of sample is added to all wells which contrain SRM.
3. Solution is mixed for one repetition, 12ul.

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
atila-saliva-pt2
