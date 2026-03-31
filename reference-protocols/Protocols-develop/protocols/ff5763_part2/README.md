# Illumina DNA Prep Part 2, Post-Tagmentation Clean Up

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
    * Illumina DNA Prep

## Description
This is part two of a five part protocol for the [Illumina DNA Prep kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

[Part 1](https://develop.protocols.opentrons.com/protocol/ff5763)

[Part 3](https://develop.protocols.opentrons.com/protocol/ff5763_part3)

[Part 4](https://develop.protocols.opentrons.com/protocol/ff5763_part4)

[Part 5](https://develop.protocols.opentrons.com/protocol/ff5763_part5)

Part 2: Post-Tagmentation Clean-Up
Tagmentation Stop Buffer (TSB) is added to each sample with a multi-channel 20ul pipette, using a fresh tip each time. The multi-channel 300ul pipette is then used to mix the samples before the plate is tranferred to an off-deck thermocycler. Once the post-tagmentation thermocycler program has completed, the plate is returned to slot 2 and 'Resume' is clicked on the OT-2 application

Samples are subsequently moved to a deep well plate locked onto the magnetic module in slot 4. The magnetic module is engaged and left for 3 minutes. After the 3 minutes the supernatant is discarded into the liquid trash in slot 6.

Tagmentation Wash Buffer (TWB) is utilized to wash the samples in the magnetic module twice as follows:
100ul TWB is added to the samples, the magnetic module is engaged for 3 minutes, then supernatant is removed to liquid trash in slot 6.

After the two TWB washes a third TWB wash is partially done. 100ul TWB is added to the samples and the magnetic module is engaged. Part 3 should be initiated as soon as possible after this step.

Explanation of complex parameters below:
* `Number of Samples`: Total number of samples from 1 to 48

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* PCR Strip Tubes for Tagmentation Stop Buffer (TSB) in slot 1, row 5
* Custom 96 Well Plate with AB Gene and NEST 96 well plate with samples, slot 2
* [NEST 2ml Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/) on Magnetic Module in slot 4
* [NEST 12-Well 15ml Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) in slot 5
* [NEST 195ml Reservoir](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/) in slot 6


### Pipettes
* [P300 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* Tagmentation Stop Buffer (TSB) in PCR tubes, slot 1 row 1
    * 10ul per sample per column, I.e. 24 samples will have 30 uL in slot 1 A1, 30 uL in slot 1 B1, etc.
* Tagmentation Wash Buffer (TWB) in slot 5 well 1, 300ul per sample
* Color Code
![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_2/color_code.png)

---
### Deck Setup
* Deck Layout for 96 samples
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_2/deck_layout.png)
---

### Protocol Steps
1. 10ul TSB from slot 1 row 1 is added to samples in slot 2
2. Sample plate is moved to pre-prepared thermocycler
3. Post-thermocycler, samples in slot 2 are transferred to NEST 2ml deep well plate in slot 4 ontop of the magnetic module
4. Magnetic module is engaged for 3 minutes
5. Supernatant is discarded from slot 4 samples to liquid trash in slot 6
6. 100ul TWB is added from slot 5 well 1 to sample plate on magnetic module
7. Magnetic module is engaged for 3 minutes
8. Supernatant is removed from sample plate on magnetic module
9. Steps 6, 7, and 8 are repeated
10. 100ul TWB is added from slot 5 well 1 one final time and left on an engaged magnetic module into part 3

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
ff5763
