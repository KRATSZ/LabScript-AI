# Promega MagaZorb® DNA Mini-Prep Kit

### Author
[Opentrons (verified)](https://opentrons.com/)


## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
Your OT-2 can fully automate the entire Promega MagaZorb® DNA Mini-Prep Kit.
Results of the Opentrons Science team's internal testing of this protocol on the OT-2 are shown below:  

![results](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magazorb-dna-mini-prep-kit/promega-magazordb-results.png)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96 and divisible by 8, i.e. whole columns at a time).
* `Deepwell type`: Specify which well plate will be mounted on the magnetic module.
* `Reservoir Type`: Specify which reservoir will be employed.
* `Starting Volume`: Specify starting volume of sample (ul).
* `Binding buffer volume`: Specify the volume of binding buffer to use (ul).
* `Elution Volume`: Specify elution volume (ul).
* `Park Tips`: Specify whether to park tips or drop tips.
* `P300 Multi Channel Pipette Mount`: Specify whether the P300 multi channel pipette will be on the left or right mount.


---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

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
* [Promega MagaZorb® DNA Mini-Prep Kit](https://www.promega.com/products/nucleic-acid-extraction/genomic-dna/magazorb-dna-mini-prep-kit/?catNum=MB1004)

---

### Deck Setup

* Tip rack on Slot 4 is used for tip parking if selected.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magazorb-dna-mini-prep-kit/promega-extraction-layout.png)

### Reagent Setup

* Reservoir 1: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magazorb-dna-mini-prep-kit/res1.png)

* Reservoir 2: Slot 3

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-promega-magazorb-dna-mini-prep-kit/res2.png)

---

### Protocol Steps
1. Binding buffer is mixed 5 times.
2. Binding buffer is added to samples on deep well plate on the magnetic module.
3. Magnetic module is engaged and incubated for 7 minutes.
4. Supernatant is removed and dropped into the liquid waste container.
5. Add Wash Buffer and resuspend by mixing.
6. Remove supernatant to liquid waste container.
7. Perform second wash (repeats step 5-6 with second wash buffer set).
8. Incubate for 1 minute to dry beads.
9. Elution solution is added to the samples.
10. Beads are resuspended in elution solution.
11. Incubates elution solution for 5 minutes.
12. Magnetic module is engaged and incubates for 7 minutes (variable settling time).
13. Elution samples are transferred to elution plate in Slot 1.


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
sci-promega-magazorb-dna-mini-prep-kit
