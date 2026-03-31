# Nucleic Acid Purification/Cloning

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Gibson Prep

## Description
This is part 2 of a 2 part protocol for prepping then loading nucleic acid onto agar plates. It requires both a multichannel and single channel 20ul pipette.
Part one can be found [here](https://protocols.opentrons.com/protocol/019a7d)

The basic outline follows:
The assembly plate liquid is added to a Mix and Go plate. A heat shock can be performed, bringing the Mix and Go plate to 42 C for 40 seconds then back to the holding temperature of 4 C. After 30 minutes, agar plates are loaded with the resultant mixture as specified in the parameters. If desired, this Mix and Go plate's liquid can be added to a deep well plate and mixed with liquid culture.

Tips are reused for the same sample repeatedly, i.e. sample A1 on the Mix and Go will use A1 in the tip rack.


Explanation of complex parameters below:
* `Number of Samples`: Number of samples in Mix and Go plate. Can be any number between 1 and 96
* `24 or 96 Distributions per Plate`: Choose to use up to four agar plates with 24 samples each and/or one agar plate with up to 96 samples. Distribution of samples follows a common layout for either 24 well plates or 96 well plates on the agar
* `Heat Shock`: Choose yes or no to determine whether a heat shock will occur during the protocol. This heat shock takes place after adding to the Mix and Go plate. It raises the temperature to 42 C for 40 seconds before returning to 4 C
* `Volume to Distribute on Agar`: Choose a liquid volume to add to the agar plate(s). This can theoretically be many volumes above 1 ul but caution should be exercised so as not to co-mingle samples on the agar by overloading
* `Add to Deep Well Plate`: Choose yes or no to add to deep well plate. Yes results in a specified amount of liquid being added to the deep well plate 1 cm above the well bottom and mixed
* `Volume to Add to Deep Well Plate`: Specifies volume to add to the deep well plate if yes is chosen under "Add to Deep Well Plate"

---

### Modules
* [2x Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

### Labware
* 2x Azenta Life Sciences 96 Well Plate, 200 ul
* 1x Greiner 96 Deep Well Plate, 2 ml
* 5x Thermo Fisher Omni Nunc Tray
* [1x Opentrons 20ul Filter Tip Racks](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [Gen2 m20 Multi-Channel Pipette, Right Side](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Gen2 p20 Single-Channel Pipette, Left Side](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* Assembly Plate liquid
* Liquid Culture, if used
* Agar (set in plate)

---

### Deck Setup
* Deck Layout, temp modules should initially be set to 4 C in both slot 1 and 4
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/019a7d_part_2/Screen+Shot+2022-04-05+at+3.40.32+PM.png)

### Reagent Setup
* Mix and Go 96 Well Plate: slot 1 in temperature module
* Assembly Plate 96 Well Plate: slot 3 in temperature module
* Agar Plates: slots 5, 6, 7, 8, 9 (5-8 hold 24 samples each, 9 holds 96)
  NOTE: Plates will be accessed in the above order. I.e. if 48 samples are selected for 24 well agar, plates in 5 and 6 will be filled
* Deep Well Plate: slot 11

---

### Protocol Steps
1. 5 ul of Assembly Plate liquid (slot 3) is added to the Mix and Go Plate (slot 1) for each sample
2. After each addition, a gentle mixing occurs 3x before the tip is blown out and returned to the tip rack (slot 4)
3. If heat shock is selected, it occurs here. Slot 1's temperature module is raised to 42 C for 40 seconds then returned to 4 C
4. Pause for 30 minutes
5. A specified amount of Mix and Go plate mixture is added to the agar plates as specified. Up to 96 samples can be distributed across 4 agar plates as if they were 24 plate wells in slots 5, 6, 7, and 8 or a single agar plate in slot 9 as if it were a 96 well plate. All additions occur ~5 mm above the agar. Tips are reused with the same samples they were previously used with in steps 1 and 2. If 24 well plates are selected, the single channel pipette is used. If the 96 well plate is selected, the multi channel pipette is used
6. Tips are returned to slot 4
7. If deep well plate addition is selected, it occurs here. A specified amount is added to the deep well plates for each sample using the same tip for each as used in steps 1, 2, and 5.
8. 20 ul mixing occurs after each addition 10x for each sample in the deep well plate
9. Tips are disposed of

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
