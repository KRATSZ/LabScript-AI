# Thermofisher Magmax Viral/Pathogen Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Thermofisher MagMAX

## Description
Your OT-2 can fully automate the entire Thermofisher MagMAX Kit.
Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-thermofisher-magmax/results.jpeg)

Lysed samples should be loaded on the magnetic module in a NEST or USA Scientific 96-deepwell plate. For reagent layout in the 2 12-channel reservoirs used in this protocol, please see "Setup" below.

For sample traceability and consistency, samples are mapped directly from the magnetic extraction plate (magnetic module, slot 4) to the elution PCR plate (temperature module, slot 1). Magnetic extraction plate well A1 is transferred to elution PCR plate A1, extraction plate well B1 to elution plate B1, ..., D2 to D2, etc.

Explanation of complex parameters below:
* `park tips`: If set to `yes` (recommended), the protocol will conserve tips between reagent addition and removal. Tips will be stored in the wells of an empty rack corresponding to the well of the sample that they access (tip parked in A1 of the empty rack will only be used for sample A1, tip parked in B1 only used for sample B1, etc.). If set to `no`, tips will always be used only once, and the user will be prompted to manually refill tipracks mid-protocol for high throughput runs.
* `track tips across protocol runs`: If set to `yes`, tip racks will be assumed to be in the same state that they were in the previous run. For example, if one completed protocol run accessed tips through column 5 of the 3rd tiprack, the next run will access tips starting at column 6 of the 3rd tiprack. If set to `no`, tips will be picked up from column 1 of the 1st tiprack.
* `flash`: If set to `yes`, the robot rail lights will flash during any automatic pauses in the protocol. If set to `no`, the lights will not flash.

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
* [ThermoFisher MagMAX Kit](https://www.thermofisher.com/us/en/home/industrial/animal-health/animal-health-workflow-solutions/sample-extraction.html)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-thermofisher-magmax/deck.20.24+PM.png)

### Reagent Setup

![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-thermofisher-magmax/reagents.png)

Reagents:
* green: binding buffer
* pink: wash buffer 1
* purple: wash buffer 2
* blue: elution buffer
* orange: wash buffer 3

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
sci-thermofisher-magmax
