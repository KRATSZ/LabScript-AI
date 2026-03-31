# Cell Culture Nucleic Acid Purification

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Nucleic Acid Extraction & Purification
	* Nucleic Acid Purification

## Description
This protocol performs an RNA extraction on a user-specified number of samples. Beads are pre-mixed and added to sample with 5 sequential incubation-mix periods. Excess liquid is picked off the top of the wells and dispensed into waste, and the remaining liquid + beads are added to the magnetic plate. After two PBS washes, elution and neutralization buffer are added to the samples. Samples are then moved to the elution plate, with beads in the mag plate collected for later use. 

Explanation of complex parameters below:
* `Number of Samples`: Specify the number of samples to be processed this run.
* `Slow Aspiration Rate (Step 7)`: Specify the aspiration rate for Step 7 in the protocol. A value of 1 is the default flow rate, a value of 0.5 would be half of the default flow rate, and so on.
* `Aspiration Height to Remove Top Liquid (Step 7)`: Specify the aspiration height to aspirate 3 X 300ul from as specified in Step 7 in the protocol.
* `Aspiration Height to Remove Supernatant`: Specify the aspiration height to remove supernatant from.
* `Incubation Time After Engaging Magnet`: Specify the incubation time after engaging the magnet (in minutes).
* `Length From Side of Well Opposite Magnetically Engaged Beads`: Specify the distance from the side of the well opposite magnetically engaged beads to aspirate from. A value of 2 is 2mm from the side of the well opposite magnetically engaged beads.
* `P300 Multi-Channel Mount`: Specify which mount (left or right) for the P300 multi-channel pipette.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)


### Labware
* Nunc™ 96-Well Polypropylene DeepWell™ Storage Plates 278743
* [Bio-Rad 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Nest 1 well Reservoir 195mL](https://shop.opentrons.com/collections/reservoirs?_gl=1*dal21t*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTYzMDYwMzE1NC4zMjQuMS4xNjMwNjAzMTU2LjA.&_ga=2.241719242.911276984.1629234597-1365106149.1621361358)
* [Nest 12 well Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs?_gl=1*dal21t*_ga*MTM2NTEwNjE0OS4xNjIxMzYxMzU4*_ga_GNSMNLW4RY*MTYzMDYwMzE1NC4zMjQuMS4xNjMwNjAzMTU2LjA.&_ga=2.241719242.911276984.1629234597-1365106149.1621361358)
* [Opentrons 300ul tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

### Pipettes
* [P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)


---

### Deck Setup
* If the deck layout of a particular protocol is more or less static, it is often helpful to attach a preview of the deck layout, most descriptively generated with Labware Creator. Example:
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f4e7/Screen+Shot+2021-09-02+at+4.50.16+PM.png)

### Reagent Setup

* Reservoir 1: Slot 2
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04f4e7/Screen+Shot+2021-09-02+at+4.50.34+PM.png)


---

### Protocol Steps
1.	Mix Mag beads 5x.  Add 50ul per sample.  Repeat for all samples. (1 tip per sample) Return tips after use.
2.	Mix 5x (200ul), wait 4 minutes (One tip per sample, return after use)
3.	Mix 5x (200ul), wait 4 minutes (One tip per sample, return after use)
4.	Mix 5x (200ul), wait 4 minutes (One tip per sample, return after use)
5.	Mix 5x (200ul), wait 4 minutes (One tip per sample, return after use)
6.	Mix 5x (200ul), wait 10 minutes (One tip per sample, return after use)
7.	Slowly pipette out all but 180ul from the each well into the waste (one tip per sample, return after use) - based on distance from bottom of the well
8.	Mix again 5x and transfer the entire volume into the pcr plate on the magnet  (one tip per sample, return after use)
9.	Apply Magnet
10.	Pipette out all of the liquid from the pcr plate into the waste (180ul).  Discard tips
11.	Release magnet
12.	Add 180ul PBS, mix 2x100uL (NEW TIPS - one tip per sample, return after use)
13.	Apply Magnet
14.	Pipette out 180uL into the waste  (one tip per sample, return after use)
15.	Release magnet
16.	Add 180ul PBS, mix 2x100uL  (one tip per sample, return after use)
17.	Apply Magnet
18.	Pipette out 180uL into the waste  (one tip per sample, Throw out tips)
19.	Release magnet
20.	Add 100uL elution Buffer.  Mix 2x50ul  (one tip per sample, return after use)
21.	Add 50uL of Neutralization buffer (3X) to the elution plate (column 1 tips - 8 total, discard after use)
22.	Apply Magnet
23.	transfer the eluted protein (100uL) from the Magnet/PCR Plate to the elution plate (1 tip per sample, discard tips after use)
24.	Release magnet
25.	Add 50uL of PBS to the PCR Plate to recover the beads without touching contents or wells(column 2 - 8 tips)
26.	transfer the used beads to reservoir position 2-5 (Same 8 tips as step 25)


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
04f4e7
