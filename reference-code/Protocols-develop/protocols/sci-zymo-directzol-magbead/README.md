# Zymo Research Direct-zol™-96 MagBead RNA Kit

### Author
[Opentrons (verified)](https://opentrons.com/)


## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
Your OT-2 can fully automate the entire Zymo Research Direct-zol™-96 MagBead RNA Kit.
Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-directzol-magbead/Screen+Shot+2021-07-27+at+11.12.53+AM.png)

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-directzol-magbead/Screen+Shot+2021-07-27+at+11.13.04+AM.png)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96 and divisible by 8, i.e. whole columns at a time).
* `Deepwell type`: Specify which well plate will be mounted on the magnetic module.
* `Reservoir Type`: Specify which reservoir will be employed.
* `Starting Volume`: Specify starting volume of sample (ul).
* `Elution Volume`: Specify elution volume (ul).
* `Park Tips`: Specify whether to park tips or drop tips.
* `Mag Deck Generation`: Specify whether GEN1 or GEN2 magnetic module will be used.
* `P300 Multi Channel Pipette Mount`: Specify whether the P300 multi channel pipette will be on the left or right mount.


---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Temperature Module (GEN2)](https://shop.opentrons.com/products/tempdeck?_gl=1*fess6p*_gcl_aw*R0NMLjE2MjIwMzI4MjQuQ2p3S0NBanc0N2VGQmhBOUVpd0F5OGt6TkpCLTRGNUJPc2pZbHUxSEJMZS0wX09rNVZWTll4MmZZMXN3VGlkS1pkcGdPT202S1B4OWtSb0N0cndRQXZEX0J3RQ..*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTYyNzM5OTA1Ny4yMjcuMS4xNjI3Mzk5MDcxLjA.&_ga=2.80196951.1136571263.1627304996-1365106149.1621361358)


### Labware
* [NEST 96 Wellplate 2mL](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [USA Scientific 96 Wellplate 2.4mL](https://labware.opentrons.com/?category=wellPlate)
* [NEST 12 Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [USA Scientific 12 Reservoir 22mL](https://labware.opentrons.com/?category=reservoir)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 96 Aluminum block Nest Wellplate 100ul](https://labware.opentrons.com/opentrons_96_aluminumblock_nest_wellplate_100ul?category=aluminumBlock)

### Pipettes
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Zymo Research Direct-zol™-96 MagBead RNA Kit](https://files.zymoresearch.com/protocols/_r2100_r2101_r2102_r2103_r2104_r2105_direct-zol-96_magbead_rna.pdf)

---

### Deck Setup

* Tip rack on Slot 4 is used for tip parking if selected.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-directzol-magbead/Screen+Shot+2021-07-27+at+11.06.38+AM.png)

### Reagent Setup

* Reservoir 1: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-directzol-magbead/Screen+Shot+2021-07-27+at+11.07.19+AM.png)

* Reservoir 2: Slot 3

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-zymo-directzol-magbead/Screen+Shot+2021-07-27+at+11.07.29+AM.png)

---

### Protocol Steps
1. Temperature module is set to 4 C
2. Binding buffer is mixed to resuspend beads
3. Binding buffer is added to sample
4. Protocol is paused and user is prompted to mix for 10 minutes on heater shaker
5. Incubate on magnetic beads for 7 minutes
6. Supernatant is removed
7. Samples are washed
8. Beads are resuspended, magnetic module engaged
9. 7 minute incubation
10. Supernatant removed
11. Magnetic module disengaged
12. 7-11 repeated 3X
13. Dnase added to samples, mixed
14. Samples incubate 10 minutes with occasional mixing
15. Stop reaction added to samples
16. Elution solution added to samples and moved to temperature module


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
sci-zymo-directzol-magbead
