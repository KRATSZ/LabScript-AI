# Mag-Bind® Blood & Tissue DNA HDQ 96 Kit

### Author
[Opentrons (verified)](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
After lysing samples, your OT-2 can fully automate the entire Omega Bio-tek Mag-Bind® Blood & Tissue DNA HDQ 96 Kit. Buffer systems tailored specifically for each type of starting material are added to samples to undergo lysis. Samples are then mixed with HDQ Binding Buffer and Mag-Bind® Particles HDQ to bind magnetic beads to DNA. DNA is eluted in the Elution Buffer after rapid wash steps.

Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-extraction/Screen+Shot+2021-06-29+at+2.44.45+PM.png)

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


### Labware
* [NEST 96 Wellplate 2mL](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [USA Scientific 96 Wellplate 2.4mL](https://labware.opentrons.com/?category=wellPlate)
* [NEST 12 Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [USA Scientific 12 Reservoir 22mL](https://labware.opentrons.com/?category=reservoir)
* [Opentrons 96 tiprack 300ul](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Aluminum block Nest Wellplate 100ul](https://labware.opentrons.com/opentrons_96_aluminumblock_nest_wellplate_100ul?category=aluminumBlock)

### Pipettes
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Omega Bio-tek](https://www.omegabiotek.com/product/mag-bind-hdq-blood-dna-96-kit/?cn-reloaded=1)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-extraction/Screen+Shot+2021-06-29+at+5.29.44+PM.png)

### Reagent Setup

* Reservoir 1: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-extraction/Screen+Shot+2021-06-29+at+2.36.37+PM.png)

* Reservoir 2: Slot 3

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-extraction/Screen+Shot+2021-06-29+at+2.36.45+PM.png)

---

### Protocol Steps
1. Binding buffer is mixed
2. Binding buffer added to samples
3. Binding buffer and sample mixed
4. Delay for 10 minutes. Bind off-deck on a heater/shaker
5. Engage magnetic module
6. Incubate 7 minutes
7. Remove supernatant
8. Wash with wash buffer 1 and mix
9. Engage magnetic module
10. Delay 7 minutes
11. Remove supernatant
12. Disengage magnet
13. Repeat steps 8-11 with wash buffer 2 and 3
14. Elution solution added to sample and mixed
15. Delay 5 minutes for elution
16. Elute added to aluminum block

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
sci-omegabiotek-extraction
