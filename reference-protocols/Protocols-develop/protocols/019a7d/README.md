# Nucleic Acid Purification/Cloning

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Gibson Prep

## Description
This is part 1 of a 2 part protocol for prepping then loading nucleic acid onto agar plates. It requires both a multichannel and single channel 20ul pipette.
Part two can be found [here](https://protocols.opentrons.com/protocol/019a7d_part_2)


Explanation of complex parameters below:
* `Number of Samples`: Specify a number of samples. Can be any number from 1 to 96

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)


### Labware
* 1x Azenta Life Sciences 12 Well Reservoir, 21 ml
* 2x Azenta Life Sciences 96 Well Plate, 200 ul
* Aluminum Block for Generic Screw Cap Tubes, 1.5 ml
* [2x Opentrons 20ul Filter Tip Racks](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [Gen2 m20 Multi-Channel Pipette, Right Side](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Gen2 p20 Single-Channel Pipette, Left Side](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* Gibson Mix, Slot 1
* Fragments, Slot 2
* Backbone Mix, Slot 4

---

### Deck Setup
* Deck Layout, temp modules should initially be set to 4 C in both slot 1 and 4
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/019a7d/Screen+Shot+2022-04-05+at+4.25.21+PM.png)

---

### Protocol Steps
1. 9 ul of backbone mix in slot 4 is added across the Assembly plate in slot 3. Tips are reused then disposed of after this step
2. 1 ul of fragment mix in slot 2 is added across the Assembly plate in slot 3. Tips are not reused and disposed of after each dispense
3. 10 ul of Gibson mix in slot 1 is added across the Assembly plate in slot 3. The resultant mixture is mixed 3x with 10 ul aspirations. Tips are not reused and disposed of after each mix
4. Assembly plate is manually transferred from OT-2 deck to an external PCR thermocycler for a 1 hour incubation
5. Part 2 of this protocol is now setup and run. It can be found [here](https://protocols.opentrons.com/protocol/019a7d_part_2)

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
019a7d
