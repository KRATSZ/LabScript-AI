# Mag-Bind® Viral DNA/RNA 96 Kit
### Author
[Opentrons (verified)](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* RNA Extraction

## Description
Your OT-2 can automate the Mag-Bind® Viral DNA/RNA 96 Kit. Please see the kit description below found on the [kit website]((https://www.omegabiotek.com/product/mag-bind-viral-dna-rna-96-kit/):

"Mag-Bind® Viral DNA/RNA Kit is designed for the rapid and reliable isolation of viral RNA and viral DNA from serum, swabs, plasma, saliva, and other body fluids. The Mag-Bind® magnetic beads technology enables purification of high-quality nucleic acids that are free of proteins, nucleases, and other impurities. In addition to easily being adapted with automated systems, this procedure can also be scaled up or down depending on the amount of starting sample. The purified nucleic acids are ready for direct use in downstream applications such as amplification or other enzymatic reactions."

Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-magbind/Screen+Shot+2021-08-09+at+11.16.53+AM.png)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96 and divisible by 8, i.e. whole columns at a time).
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
* [NEST 1 Reservoir 195mL](https://shop.opentrons.com/collections/reservoirs/products/nest-1-well-reservoir-195-ml)
* [NEST 12 Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 96 tiprack 300ul](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 96 Aluminum block Nest Wellplate 100ul](https://labware.opentrons.com/opentrons_96_aluminumblock_nest_wellplate_100ul?category=aluminumBlock)

### Pipettes
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Mag-Bind® Viral DNA/RNA 96 Kit](https://www.omegabiotek.com/product/mag-bind-viral-dna-rna-96-kit/)

---

### Deck Setup
Tip rack on Slot 5 is used for tip parking if selected. If not tip parking, place [200ul Opentrons Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) in Slot 5.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-magbind/Screen+Shot+2021-08-09+at+11.44.26+AM.png)

### Reagent Setup

* Reservoir: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-omegabiotek-magbind/Screen+Shot+2021-08-09+at+11.45.25+AM.png)

---

### Protocol Steps
1. Binding buffer is mixed.
2. Binding buffer added to samples.
3. Binding buffer and sample mixed.
4. Engage magnetic module.
4. Delay for 5 minutes.
5. Supernatant removed.
6. Magnetic module disengaged.
7. Wash 1 added, mixed with samples.
8. Magnetic module engaged, incubated 5 minutes.
9. Supernatant removed.
10. 7-9 repeated for wash buffer 2 and 3.
11. Elution solution added to sample and mixed.
12. Delay 10 minutes for elution.
13. Magnetic module engaged.
16. Elute added to aluminum block (4C)

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
sci-omegabiotek-magbind
