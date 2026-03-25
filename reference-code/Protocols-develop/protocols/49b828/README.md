# CovidNow SARS-CoV-2 Assay rRT-PCR Batch Set Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps a 384 well plate with mastermix and sample. Plates should loaded in order of slots 7, 8, 1, and 2. See below for how plates are transferred to the 384 well plate. If running a full run (382 samples), mastermix will be provided to the wells O24 and P24. If not running a full run, mastermix and controls will have to be placed manually. H11 and H12 of the final plate on slot 2 should be left empty if running a full run.


Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples in this run. Samples 1-96 will go in plate 1 slot 7, samples 97-192 will go in plate 2 slot 8, samples 193-288 will go in plate 3 slot 1, samples 289-384 will go in plate 4 slot 2. Samples will be put into the 384 well plate in the following manner:
* `96 Well Plate Type`: Specify whether using the four 96 plates as the Kingfisher plate (depth 12.8mm) or the thermofisher plate (depth 42.3mm).
* `384 Well Plate Type`: Specify whether using the 384 plate with the clear numbers, or the 384 plate with the black numbers. Plate should be mounted on aluminum block.
* `Use Temperature Module?`: Specify whether using the temperature module or not on the 384 plate in slot 3 for this run. The temperature module will be set at 4C. If not using the temperature module, just place the 384 plate in slot 3 with no aluminum block.
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 Single-Channel pipette.

---


### Labware
* [Opentrons 20ul Filter Tips](https://shop.opentrons.com/universal-filter-tips/?_gl=1*jcqbld*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTY0NzM2ODQyMC43OTAuMS4xNjQ3MzY5NzE3LjA.&_ga=2.241426050.1055140719.1647265384-1365106149.1621361358)
* [NEST 12 well 15mL Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* Thermo Scientific KingFisher Flex 96 well plates
* Thermo-Fisher 384 well microplate

### Pipettes
* [P20 Single-Channel Pipette](https://shop.opentrons.com/pipettes/)


### Reagents
* [CovidNow SARS-CoV-2 Assay rRT-PCR Batch Set Up](https://www.fda.gov/media/153175/download#:~:text=The%20CovidNow%20SARS%2DCoV%2D2,Drug%20Administration's%20Emergency%20Use%20Authorization)

---

### Deck Setup
* Note: Samples will be dispensed per plate to the 384 well plate by column. Column 1 plate 1 --> A1 of 384, column 2 plate 1 --> B1, column 3 plate 1 --> A2 so on and so forth. Each plate is then 6 columns of the 384 well plate. If there is an unfilled column (i.e. 54 samples = 0.5 plates + 6 samples), then the protocol will use 8 tips up to column 6 of the 96 well plate, pick up 6 tips, then go to dispense into A7 of the 384 well plate. For a full run (382 samples), mastermix will be supplied to all wells. For all other sample numbers, mastermix will not be provided to O24 and P24, and will have to be put in manually. Do not run this protocol for 368 < sample number < 384 samples.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/49b828/Screen+Shot+2022-03-15+at+2.37.47+PM.png)

---

### Protocol Steps
1. The 8-channel pipettte acquires 8 20 uL filtered pipette tips and aspirates 15 uL of PCR reagent from specified well of 12-well resorvoir and deposits the reagent in column A1 - H1 on the 384 well microplate (see plate layout attached) [same tips, with blowout; with touch tip]
2. 1 is repeated until all designated wells have been filled with reagent
3. Tips are discarded
4. The 8-channel pipette acquires fresh 8x20 uL filtered pipette tips and aspirates 5 uL of sample solution from elution (or King Fisher 96 deep-well) plate A beginning with column 1 (A1 - H1) [with touch tip; with variable aspiration location (if using 96 deep-well plate, tips need to be dead center of well to fit into groove)]
5. The 8-channel pipette then moves to the 384 microwell plate and dispenses the 5 uL of sample solutions into the corresponding wells A1 - H1 (see plate layouts attached) [with blow out]
6. The tips are discarded
7. 4 - 6 are repeated for subsequent columns on 96-well Plate A until all samples have been transferred to the 384 microwell plate by skipping a column on the 384 plate between additions (see plate layout attached) [different tips; with blow out; with touch tip]
8. 4 - 7 are repeated with plates B, C, and D in this order until all samples from all 4 96 well plates have been transferred to the 384-well microplate (again, see plate layout attached; NOTE. that microwells P22 and P24 have reagent in them but DO NOT have samples in them) [different tips; with blow out; with touch tip]

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
49b828
