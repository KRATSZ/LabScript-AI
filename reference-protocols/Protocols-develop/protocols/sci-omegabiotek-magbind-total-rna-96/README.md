# Mag-Bind® Total RNA 96 Kit

### Author
[Opentrons (verified)](https://opentrons.com/)


## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
Your OT-2 can automate the Mag-Bind® Viral DNA/RNA 96 Kit. Please see the kit description below found on the [kit website](https://www.omegabiotek.com/product/mag-bind-total-rna-96-kit/):

"The Mag-Bind® Total RNA 96 Kit provides a novel technology for total RNA isolation. This kit allows the rapid and reliable isolation of high-quality total cellular RNA and viral RNA from a wide variety of cells and tissues. Unlike column-based systems, the binding of nucleic acids to magnetic particles occurs in solution resulting in increased binding kinetics and binding efficiency. Particles are also completely re-suspended during the wash steps of the purification protocol, which improves the removal of contaminants and increases nucleic acid purity. Mag-Bind® Total RNA 96 Kit procedure can be fully automated with most robotic workstations."

Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-magbind-total-rna-96/Screen+Shot+2021-08-09+at+4.10.56+PM.png)

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-magbind-total-rna-96/Screen+Shot+2021-08-09+at+4.11.10+PM.png)



Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96 and divisible by 8, i.e. whole columns at a time).
* `Deepwell type`: Specify which well plate will be mounted on the magnetic module.
* `Reservoir Type`: Specify which reservoir will be employed.
* `Starting Volume`: Specify starting volume of sample (ul).
* `Binding Buffer Volume`: Specify binding buffer volume (ul).
* `Wash Volumes`: Specify each of the three wash volumes (ul).
* `Elution Volume`: Specify elution volume (ul).
* `Settling Time`: Specify settling time for beads (minutes).
* `Mag Deck Generation`: Specify whether GEN1 or GEN2 magnetic module will be used.
* `Park Tips`: Specify whether to park tips or drop tips.
* `Track Tips`: Specify whether to track tips between runs (starting with fresh tips or pick up from last runs tips).
* `Flash`: Specify whether to flash OT-2 lights when the protocol runs out of tips, prompting the user to replenish tips.
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
* [Mag-Bind® Total RNA 96 Kit](https://www.omegabiotek.com/product/mag-bind-total-rna-96-kit/)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/528c16/Screen+Shot+2022-03-11+at+3.25.12+PM.png)

Saliva: add 200uL of saliva

Bacteria culture: spin down 200uL of culture, wash once in PBS, resuspend in 200uL of chilled PBS

200uL of sample + 200uL of lysis buffer. Mix thoroughly, add to deep well plate

Dnase 1 treatment: 49uL of buffer + 1uL of DNAse 1 per sample.
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/528c16/Screen+Shot+2022-03-11+at+3.25.34+PM.png)

![reagent volumes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/528c16/Screen+Shot+2022-03-11+at+3.26.29+PM.png)

---

### Protocol Steps
1. Binding buffer is mixed
2. Binding buffer added to samples
3. Binding buffer and sample mixed
4. User is instructed to mix samples on heater-shaker.
5. Engage magnetic module
6. Delay 7 minutes
7. Remove supernatant
8. Wash with wash buffer 1 and mix
9. Engage magnetic module
10. Delay 7 minutes
11. Remove supernatant
12. Disengage magnet
13. Repeat steps 8-11 with wash buffer 2
14. Elution solution added to sample and mixed
15. dnase1 added to sample and mixed
16. Stop solution added to sample and mixed
17. Engage magnet remove supernatant
18. Steps 8-11 with wash buffer 3 and 4
19. Delay, incubate 7 minutes
20. Elution solution added to sample and mixed
21. Elute added to aluminum block

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
sci-omegabiotek-magbind-total-rna-96
