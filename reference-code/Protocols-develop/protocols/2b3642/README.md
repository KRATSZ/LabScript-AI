# NEBNext Ultra II DNA Library Preparation Kit for Illumina E7645S

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* NEBNext Ultra II DNA Library Preparation Kit for Illumina E7645S

## Description
This protocol automates various parts of the NEBNext Ultra II DNA Library Preparation Kit for Illumina E7645S using the OT-2 and additional hardware modules. The protocol is divided into five sections which includes the following: End Preparation, Adaptor Ligation, Cleanup of Adaptor-Ligated DNA, PCR Amplication and Cleanup of PCR Reaction.

The protocol will also pause at various stages prompting for user intervention to replace reagents, tip racks, and perform centrifugation of reaction mixtures.

Explanation of complex parameters below:
* `Number of Samples`: The total number of samples or reactions being run. This kit supports a maximum of 24 samples. Please enter sample numbers in multiples of 8 (Ex: 8, 16, 24).
* `P300 Multichannel GEN2 Mount Position`: The position your P300 Multichannel GEN2 pipette is mounted (Left or Right).
* `P20 Single Channel GEN2 Mount Position`: The position your P300 Multichannel GEN2 pipette is mounted (Left or Right).
* `Initial Denaturation Cycles`: Number of cycles at 98C for 30 seconds.
* `Denaturation and Annealing/Extension Cycles`: Number of cycles at 98C for 10 seconds and 65C for 75 seconds.
* `Final Extension Cycles`: Number of cycles at 65C for 5 minutes.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* [NEST 12-well 15 mL Reservoir](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 20uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)

### Pipettes
* [P300 GEN2 Multichannel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [P20 GEN2 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

### Reagents
* [NEBNext Ultra II DNA Library Preparation Kit for Illumina E7645S](https://www.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2b3642/2b3642_new_layout.png)
**Note:** The deck layout shown in the image above will change throughout the protocol as labware is moved around. The image above represents the starting layout of the protocol. Please refer to the protocol steps below for more detailed instructions.

### Reagent Setup
* Reservoir: slot 4
![reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2b3642/2b3642_reservoir.png)
* 96-Well Aluminim Block: slot 2  
![block](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2b3642/2b3642_aluminum.png)
(Fragmented DNA should be placed inside PCR tubes/PCR-tube strips)

---

### Protocol Steps
**I. End Preparation**
1. Set temperature module to 4°C.
2. Add Components to PCR tubes containing fragmented DNA (Slot 2). Add 3.5 uL of NEBNext Ultra II End Prep Reaction Buffer (Slot 3, B1). Add 1.5 uL of NEBNext Ultra II End Prep Enzyme Mix (Slot 3, A1).
3. Protocol will pause and prompt user to remove reagents from the temperature module.
4. Resuspend mixture 10 times with a volume of 25 uL.
5. Protocol will pause and prompt user to centrifuge the mixture.
6. Click Resume and the Thermocycler lid will begin raising the temperature to 75°C. Return the mixtures to slot 2 once centrifugation is completed.
7. Mixtures will be transferred to the PCR plate in the thermocycler module.
8. Thermocycler will run at following profile: 20°C for 30 minutes, 65°C for 30 minutes, and then hold at 4°C.

**II. Adaptor Ligation**

**This part will begin with a pause and prompt the user to add the reagents in the correct positions in the temperature module. Once Resumed it will begin deactivating the thermocycler lid**
1. Add components to the reaction mixture (PCR plate on thermocycler): Add 1.25uL of NEBNext Adaptor for Illumina (Slot 3, A1). Add 0.5 uL of NEBNext Ligation Enhancer (Slot 3, B1)
2. Resuspend NEBNext Ultra II Ligation Master Mix (Slot 3, C1) 10 times.
3. Add 15 uL of Ligation Master Mix to the reaction mixture.
**PAUSE:** Remove Reagents from the Temperature Module then Resume.
4. Resuspend Reaction Mixture (PCR Plate) 10 times with a volume of 40 uL.
5. **PAUSE**: Centrifuge the reaction mixture and return the plate to into the thermocycler.
6. Incubate the reaction mixture at 20°C for 15 minutes.
**PAUSE:** Place USER Enzyme in Position A1 of the Temperature Module.
7. Add 1.5 uL of USER Enzyme (Slot 3, A1) to the reaction mixture.
**PAUSE:** Remove USER Enzyme from Temperature Module.
8. Resuspend Reaction Mixture (PCR Plate) 10 times with a volume of 40 uL.
9. **PAUSE**: Centrifuge Reaction Mixture
10. Raise the temperature of the thermocycler lid to 47°C.
11. Insert the reaction mixture (PCR Plate) into the thermocycler.
12. Incubate the reaction mixture at 37°C for 15 minutes.

**III. Cleanup of Adaptor-Ligated DNA**
1. Add 41 uL (Varied) of AMPure XP Beads to the ligation mixture (PCR plate).
2. Resuspend Reaction Mixture (PCR Plate) 10 times with a volume of 85 uL.
3. **PAUSE:** Centrifuge the reaction mixture and return the plate to magnetic module.
4. Incubate the reaction mixture for 5 minutes at room temperature.
5. Engage the magnets on the magnetic module and delay for 5 minutes.
6. Remove 100 uL of supernatant from the sample wells.
7. Add 100 uL of 80% Ethanol to the reaction mixture beads.
8. Incubate the ligation mixture for 30 seconds at room temperature.
9. Remove ethanol supernatant and discard.
10. Repeat steps 7-9 above.
11. Magnets are disengaged.
12. Protocol is paused and user is prompted to resume once the beads are dry.
13. Add 17 uL (Varied) of elution buffer the reaction mixture wells.
14. Resuspend Reaction Mixture (PCR Plate) 10 times with a volume of 15 uL.
15. Incubate the reaction mixture for two minutes at room temperature.
16. Engage magnets on the magnetic module and delay for 5 minuts.
17. Protocol is paused and prompts user to replace the PCR tubes in slot 2 with new PCR tubes.
18. Transfer 15 uL (Varied) of the reaction mixture to the new PCR tubes in Slot 2 (A1-H3 for 24 samples).
19. Magnets are disengaged.

**IV. PCR Amplification**
**This step begins with a pause prompting the user to add the correct reagents and add new PCR tubes in Slot 2 starting with well A10 (A10-H12 for 24 samples).**
1. Add components to new PCR tubes (Slot 2, A10-H12): Add 7.5 uL of Adaptor-Ligated DNA (A1-H3), Add 12.5 uL of NEBNext Ultra II Q5 Master Mix (Slot 3, A1), Add 2.5 uL of UDI Primers (Slot 3, B1).
**PAUSE:** Remove reagents from the temperature module.
2. Resuspend Reaction Mixture (new PCR Tubes, Slot 2) 10 times with a volume of 20 uL.
3. **PAUSE:** Centrifuge the reaction mixture and return the mixtures to the original location. Add a new PCR plate in the thermocycler for the remainder of the protocol.
4. Transfer reaction mixture from PCR tubes to PCR plate in thermocycler.
5. Begin thermocycler profile: Initial Denaturation: 98°C for 30 seconds (1 cycle), Denaturation and Annealing/Extension: 98°C for 10 seconds and 65°C for 75 seconds (6 cycles), Final Extension: 65°C for 5 minutes (1 cycle). Hold at 4°C.

**V. Cleanup of PCR Reaction**
1. Add components to PCR product mixture (PCR plate): Add 40 uL of AMPure XP Beads.
2. Resuspend Mixture 10 times (volume varied) and Incubate the reaction mixture tube for five minutes at room temperature.
3. Move the PCR plate from the thermocycler to the magnetic module.
4. Engage magnets on the magnetic module and delay for 5 minutes.
5. Remove 65 uL of supernatant and discard.
6. Add 100 uL of 80% Ethanol to the reaction mixture beads.
7. Incubate the ligation mixture for 30 seconds at room temperature.
8. Remove ethanol supernatant and discard.
9. Repeat steps 6-8 above.
10. Protocol is paused and user is prompted to resume once the beads are dry.
11. Magnets are disengaged.
12. Add 20 uL of elution buffer to the reaction mixture wells.
13. Resuspend Reaction Mixture (PCR Plate) 10 times with a volume of 15 uL.
14. **PAUSE**: Centrifuge the reaction mixture, add new PCR tubes starting in well A1 on slot 2. Return the reaction mixture to the original location and click Resume.
15. Incubate the reaction mixture for two minutes at room temperature.
16. Engage magnets on the magnetic module and delay for 5 minutes.
17. Transfer 30 uL of supernatant from the reaction mixture to the new PCR tubes on slot 2.
18. Protocol completed!

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
2b3642