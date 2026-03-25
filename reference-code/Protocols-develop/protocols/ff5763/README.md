# Illumina DNA Prep, Part 1 Tagmentation

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
    * Illumina DNA Prep

## Description
This is part one of a five part protocol for the [Illumina DNA Prep kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

[Part 2](https://develop.protocols.opentrons.com/protocol/ff5763_part2)

[Part 3](https://develop.protocols.opentrons.com/protocol/ff5763_part3)

[Part 4](https://develop.protocols.opentrons.com/protocol/ff5763_part4)

[Part 5](https://develop.protocols.opentrons.com/protocol/ff5763_part5)

Part 1: Tagmentation
Master mix is prepared offdeck and added to DNA samples. DNA samples are 30 uL in total volume. After master mix addition, the sample plate is put in a thermocycler pre-programmed as outlined in the reference manual.

Once the thermocycler is complete, part 2 can be run.

Variables:
* `Number of Samples`: Total number of samples from 1 to 48


---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Custom 96 Well Plate with AB Gene and NEST 96 well plate
* PCR Strip Tubes for Master Mix


### Pipettes
* [P300 Multi Channel]https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* Color code
![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_1/color_code.png)
* Master mix prepared as described in Illumina kit for Tagmentation w/10% overage
    * 22 uL master mix prepared per sample, 22 ul per well per column to be run. I.e. 24 samples will have 66 uL in slot 1 A1, 66 uL in slot 1 B1, etc.


* DNA Samples
    * Total volume for DNA samples in plate should be 30 uL and contain between 100-500 ng. If below 30 uL, add nuclease free water to samples

---
### Deck Setup
* Deck Layout for 96 samples
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_1/deck_layout.png)
---

### Reagent Setup
* Slot 1, Temperature Module, Master Mix in PCR Tubes, Column 1
* Slot 2, DNA Samples in Custom AB Gene plate

---

### Protocol Steps
1. 20ul of Master Mix is transferred from PCR tubes in slot 1's temperature module to slot 2's samples. Tips will be changed each time

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
