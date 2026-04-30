# Illumina DNA Prep Part 5, Clean Up Libraries 2

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
    * Illumina DNA Prep

## Description
This is part five of a five part protocol for the [Illumina DNA Prep kit](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

[Part 1](https://develop.protocols.opentrons.com/protocol/ff5763)

[Part 2](https://develop.protocols.opentrons.com/protocol/ff5763_part2)

[Part 3](https://develop.protocols.opentrons.com/protocol/ff5763_part3)

[Part 4](https://develop.protocols.opentrons.com/protocol/ff5763_part4)

Part 5: Cleanup Libraries 2
Magnetic module is engaged for 5 minutes. IPB is added to the right side of the magnetic module. 125ul of supernatant is transferred from the left side of the magnetic module to the right side containing the bead mixture and mixed 10x. 5 minute incubation occurs followed by discarding of supernatant. Beads are then washed with 80% ethyl alcohol twice and allowed to airdry for 5 minutes. RSB is added to the samples and a 2 minute delay occurs. The magnetic module is now engaged for 2 minutes followed by a final transfer of resulting supernatant to an awaiting 96 well plate in slot 2.

Explanation of complex parameters below:
* `Number of Samples`: Total number of samples from 1 to 48

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* New Custom 96 Well Plate with AB Gene and NEST 96 well plate with samples, slot 2
* [NEST 2ml Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/) containing samples from previous step on Magnetic Module in slot 4
* [NEST 12-Well 15ml Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) in slot 5 (reagent reservoirs)
* [NEST 195ml Reservoir](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/) in slot 6 (liquid trash)


### Pipettes
* [P300 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 Multi Channel](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* IPB, PCR Tubes in slot 1 column 1 (15ul per sample per column)
* RSB, PCR Tubes in slot 1 column 3 (32ul per sample per column)
* EtOH 80% freshly made, Reservoir in slot 5 well 12 (200ul per sample)
* Color code
![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_5/color+code.png)
---
### Deck Setup
* Deck Layout for 96 samples
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/ff5763/part_5/deck_setup.png)
---
### Protocol Steps
1. Magnetic module is engaged for 5 minutes
2. 15ul IPB is transferred to columns 7-12 on magnetic module. The IPB tubes are mixed every other time the IPB is aspirated via a bead mixing function where the solution is aspirated from the bottom, dispensed 3 mm higher, aspirated at the same higher location, then dispensed from the bottom. This is repeated 10 times total.
3. 125ul supernatant is transferred from columns 1-6 to columns 7-12 on the magnetic module with a 10x mix at 120ul
4. Magnetic module is disengaged
5. 5 minute incubation period
6. Magnetic module is engaged for 5 minutes
7. Resulting supernatant is discarded
8. Beads in columns 7-12 are washed twice with 100ul 80% EtOH, discarding the supernatant each time
9. 20ul Pipette is used to ensure full removal of EtOH after second wash
10. Samples are air dryed for 5 minutes
11. 32ul RSB is added to columns 7-12 on magnetic module
12. 2 minute incubation
13. Magnetic module is engaged for 2 minutes
14. 30ul of resulting supernatant is transferred from magnetic module to final 96 well plate in slot 2
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
