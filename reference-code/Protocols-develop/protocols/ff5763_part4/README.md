# Illumina DNA Prep Part 4, Clean Up Libraries 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
    * Illumina DNA Prep

## Description
This is part four of a five part protocol for the [Illumina DNA Prep kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

[Part 1](https://develop.protocols.opentrons.com/protocol/ff5763)

[Part 2](https://develop.protocols.opentrons.com/protocol/ff5763_part2)

[Part 3](https://develop.protocols.opentrons.com/protocol/ff5763_part3)

[Part 5](https://develop.protocols.opentrons.com/protocol/ff5763_part5)

Part 4: Cleanup Libraries First Half

Samples are centrifuged down before adding the sample tray to slot 2 on the OT-2's deck. Tray contents are transferred to the available wells in the deep well plate on the magnetic module and left until clear (~5 minutes). 45ul of the resulting supernatant is moved to the second deep well plate in slot 3. 40ul of NFW is added to this supernatant for each sample. 45ul of IPB mix is then added to the now diluted samples and mixed 10x at 100ul each time. The deep well plate is left to incubate for 5 minutes. This ends part 4.
Explanation of complex parameters below:
* `Number of Samples`: Total number of samples from 1 to 48

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Custom 96 Well Plate with AB Gene and NEST 96 well plate with samples, slot 2
* New [NEST 2ml Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/) in slot 3
* [NEST 2ml Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/) containing samples from previous steps on Magnetic Module in slot 4
* [NEST 12-Well 15ml Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) in slot 5 (reagent reservoirs)
* [NEST 195ml Reservoir](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/) in slot 6 (liquid trash)


### Pipettes
* [P300 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* Nuclease Free Water, PCR Tubes in slot 1 column 1,
* Illumina Purification Bead, PCR Tubes in slot 1 column 3
* Color code
![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_4/color+code.png)

---
### Deck Setup
* Deck Layout for 96 samples
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_4/deck_setup.png)
---

### Protocol Steps
1. Centrifuge the sample plate at 280 x g for 1 minute to collect contents at the bottom of the wells
2. The liquid portion (70ul) is transferred to the available wells (columns 7-12) on the magnetic module's deep well plate
3. The magnetic module is engaged at 10mm for 5 minutes
4. The resulting supernatant in columns 7-12 (if 48 samples) has 45ul moved to columns 1-6 in slot 3's deep well plate.
5. 40ul of NFW is added to columns 1-6 in slot 3
6. 45ul of IPB is added to columns 1-6 in slot 3 then mixed 10x at 100ul each time. The IPB tubes are mixed every other time the IPB is aspirated via a bead mixing function where the solution is aspirated from the bottom, dispensed 3 mm higher, aspirated at the same higher location, then dispensed from the bottom. This is repeated 10 times total.
7. The samples are left to incubate for 5 minutes
8. Slot 2's plate can be disposed of
9. Slot 4's plate (magnetic module plate) can be disposed of
10. Slot 3's plate should be moved to the magnetic module in slot 4 for part 5
---

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
