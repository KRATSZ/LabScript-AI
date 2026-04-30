# Mag-Bind® Blood & Tissue DNA HDQ 96 Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* DNA Extraction

## Description
This is a custom implementation of the Mag-Bind Blood and Tissue kit. Specify the starting sample volume, final elution volume, and number of samples, allowing the OT-2 to automate the procedure with minimal intervention to empty trash and/or refill tip racks as alerted.

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples this run (1-96 and divisible by 8, i.e. whole columns at a time).
* `Initial Volume`: Specify starting volume of sample (ul).
* `Elution Volume`: Specify elution volume (ul) into final plate.
* `Flash on Robot Pause`: Specify whether the robot will flash on pause. This includes trash or tip rack notifications
* `P300 Multi Channel Pipette Mount`: Specify whether the P300 multi channel pipette will be on the left or right mount.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 96 Wellplate 2mL](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [NEST 12 Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Thermofisher 96 Well, semi-skirted, black lettering](https://www.thermofisher.com/order/catalog/product/AB1400L) mounted to deck with [Opentrons 96 Aluminum block](https://labware.opentrons.com/opentrons_96_aluminumblock_nest_wellplate_100ul?category=aluminumBlock)

### Pipettes
* [P300 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Mag-Bind® Blood & Tissue DNA HDQ 96 Kit](https://www.omegabiotek.com/product/tissue-and-blood-kit-genomic-dna-isolation-mag-bind-hdq-96/)

---

### Deck Setup

![reagent color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/color_code.png)

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/deck_state.png)

### Reagent Setup

* Reservoir 1: Slot 2

![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/slot_2.png)

* Reservoir 2: Slot 5

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/slot_5.png)

Binding buffer is mixed with purification beads and added to specified deck slot.

NOTE ON REAGENT SETUP:
The VHB and SPM/Ethanol reagents should be split evenly between the specified wells. Wells 1-5 and 5-10 in slot 5 are for the first and second VHB washes respectively. The OT-2 will access these reagent wells in sequence, aspirating equally across all wells. The NEST 12 well reservoirs should be filled to a minimum volume of 1.5 mL to ensure proper aspiration.
---

### Protocol Steps
1. Binding buffer/bead mixture is vigorously mixed to disperse beads. This is repeated when a well is accessed for the first time, i.e. every 4th column
2. Binding buffer is added to samples on deep well plate on the magnetic module.
3. Samples are mixed for 30 seconds
4. Magnetic module is engaged and incubated for 5 minutes
5. Supernatant is removed and disposed of in waste container, slot 4. Tips are re-used for future supernatant removals in first tip rack, slot 1
6. 600 uL of VHB buffer is added to each sample and mixed
7. Magnetic module is engaged and incubated for 5 minutes
8. Supernatant is removed and disposed of in waste container, slot 4
9. Steps 6 through 8 are repeated for a second VHB wash and supernatant removal
10. 600 uL of SPM buffer diluted with ethanol is added to each sample and mixed
11. Magnetic module is engaged and incubated for 5 minutes
12. Supernatant is removed and disposed of in waste container, slot 4. Supernatant tips are disposed of here after third use
13. 400 uL nuclease free water is added to a single column, delay for 20 seconds, then NFW is removed. This is to ensure ethanol removal without premature elution. Elution buffer is immediately added to column. Repeated for all samples
14. A specified volume of elution buffer is transferred to an awaiting plate in slot 3

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
9778eb
