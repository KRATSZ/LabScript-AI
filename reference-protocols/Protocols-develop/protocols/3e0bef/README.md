# Omega Bio-Tek Mag-Bind Plant DNA DS Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Omega Bio-Tek Mag-Bind Plant DNA DS Kit

## Description
This protocol automates the [Omega Bio-Tek Mag-Bind® Plant DNA DS 96 Kit](https://www.omegabiotek.com/product/plant-extraction-mag-bind-plant-dna-ds-96/) on the OT-2.

Using the [P300 8-Channel Pipette, GEN2](https://shop.opentrons.com/8-channel-electronic-pipette/) all liquid handling steps outlined in [the protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-12-14/kf03tt7/Omega%20BioTek%20Mag-Bind%20Plant%20DNA%20extraction%20automation%20protocol.pdf) are handled on the OT-2, with minimal user intervention. To optimize liquid handling on the automated platform, some reagents should be combined prior to adding to the deck (more details below).

Explanation of complex parameters below:
* **Pipette Mount**: Select which mount (left or right) the [P300 8-Channel Pipette, GEN2](https://shop.opentrons.com/8-channel-electronic-pipette/) is attached to.
* **Number of Samples**: Specify the number of samples (1-96). Please note ~ because the 8-channel pipette is used in this protocol, any number will be rounded up to 8.
* **Binding Time (minutes)**: Specify the number of minutes for binding, prior to the first supernatant removal. Please note that this is an estimate, as there will be continuous mixing throughout this step.
* **MagDeck Incubation (minutes)**: Specify the number of minutes to delay the robot, while the MagDeck is engaged.
* **Air Dry Time (minutes)**: Specify the number of minutes for air drying after the final wash step.
* **Add Water Before Air Dry**: Specify whether or not to add, then remove 100µL of water immediately before the air dry step.
* **Labware for Samples Input**: Select the labware that will contain the samples from the drop down.
* **[QIAGEN ONLY] Aspiration Height**: Specify the height (in mm) from the bead to aspirate from (3mm is the default)
* **Final Wash Removal (in µL)**: Specify the volume for the supernatant removal step during the final wash.
* **Elution Volume (in µL)**: The volume of Elution Buffer added to each well. Please note ~ [the written protocol](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-12-14/kf03tt7/Omega%20BioTek%20Mag-Bind%20Plant%20DNA%20extraction%20automation%20protocol.pdf) states 100-200µL and this protocol has been designed accordingly.
* **Perform Resuspension Off-Deck**: Specify whether to perform resuspension with manual intervention (Yes) or with the OT-2 Pipette (No). This will apply to the initial 10 minute incubation and the 4 wash steps.
* **Play Custom Music at Pause**: Specify whether or not to play custom music during pause steps. Please note, selecting **'No'** will result in the pre-installed music playing. Please only select **'Yes'** if you've worked with the Opentrons team on this protocol prior to download
</br>

*Note*: This protocol was last updated on October 27th, 2022

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Sample Input Labware (specified in parameters)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/nest-1-well-reservoirs-195-ml/)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [NEST 96-Well Deepwell Plate, 2mL](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [Opentrons 200µL Filter Tip Racks](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

### Pipettes
* [P300 8-Channel Pipette, GEN2](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Reagents
* [Omega Bio-Tek Mag-Bind® Plant DNA DS 96 Kit](https://www.omegabiotek.com/product/plant-extraction-mag-bind-plant-dna-ds-96/)

---

### Deck Setup
![Deck Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3e0bef/3e0bef_deck_v2.png)

### Reagent Setup
Reagents for this protocol are split between two [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/). For each reagent, a section of 2-6 channels are dedicated and when transferring to samples, channels are used sequentially. For example, the CSPW2 Buffer can be split across 4 channels. In this example, each channel can hold enough reagent for up to 3 columns of samples (24 total samples). Continuing with this example, if 32 samples were being processed, enough reagent for 3 columns of sample would fill the first dedicated channel for the CSPW2 Buffer and enough reagent for 1 column would fill the second channel.</br>
</br>
When determining the amount of reagent, the number of sample columns should be multiplied by eight, 1.1 (an additional 10%), and the amount of reagent needed. Based on the number of channels dedicated to each reagent, the amount needed in each channel can be calculated.</br>
</br>
The SPM buffer is used for two, sequential washes and the protocol has been updated to utilize the columns of the reservoir sequentially (as opposed to broken into "wash 1" and "wash 2"). Given this, each column of the reservoir can hold enough reagent for 1.5 columns in the sample plate (ie, washes 1 & 2 for column 1 and wash 1 for column 2). Continuing with our example of 32 samples (4 sample columns), the first three reservoir columns would need to have SPM buffer to accomplish the protocol (see below):</br>
* Reservoir Well 1: Wash 1 Sample Column 1, Wash 2 Sample Column 1, Wash 1 Sample Column 2
* Reservoir Well 2: Wash 2 Sample Column 2, Wash 1 Sample Column 3, Wash 2 Sample Column 3
* Reservoir Well 3: Wash 1 Sample Column 4, Wash 2 Sample Column 4
</br>
</br>
**Reservoir 1: Deck Slot 2**</br>
* RNase A (5µL) + RBB Buffer (500µL) + Mag-Bind Beads (20µL): Channels 1-4
* CSPW1 Buffer (500µL): Channels 5-8
* CSPW2 Buffer (500µL): Channels 9-12
</br>
</br>
![Reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3e0bef/3e0bef_res1_v2.png)
</br>
</br>
**Reservoir 2: Deck Slot 3**</br>
* SPM Buffer (500µL, x2): Channels 1-8
* Nuclease-Free Water (if using): Channel 9
* Elution Buffer: Channels 11 (for samples 1-48) and 12 (for samples 49-96)
</br>
</br>
![Reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/3e0bef/3e0bef_res2_v2.png)

---

### Protocol Steps
1. [Off-robot manual step] The protocol begins with the manual addition of 720µL of CSPL Buffer + Proteinase K (700+20) to each sample.
2. After initial incubation is complete, user can manually transfer 500µL of starting material to deepwell plate and place on Mag Deck or (if using Qiagen tubes) place empty deepwell plate on Mag Deck and samples onto OT-2 deck for automated transfer.
3. If automating the initial sample transfer, 500µL will be transferred to the 96-Well deepwell plate. Otherwise, OT-2 steps will begin with step 4.
4. 525µL of RNase A + RBB Buffer + Mag-Bind Beads (5+500+20) is transferred to each column containing samples.
5. A 10 minute incubation period will begin. During this period, the OT-2 will mix each column for ~30 seconds before moving to the next column. In the case of 1 column of samples, the OT-2 will mix for ~30 seconds, then stop for 30 seconds before resuming the mix again.
6. After incubating, the Mag Deck engages, and after the pellet forms, 1080µL is transferred to the NEST 1-Well Reservoir for liquid waste.
7. 500µL of CSPW1 Buffer is added to each column of samples and mixed.
8. After incubating on the Mag Deck, 600µL is transferred to the liquid waste.
9. 500µL of CSPW2 Buffer is added to each column of samples and mixed.
10. After incubating on the Mag Deck, 600µL is transferred to the liquid waste.
11. 500µL of SPM Buffer (wash 1) is added to each column of samples and mixed.
12. After incubating on the Mag Deck, 600µL is transferred to the liquid waste.
13. 500µL of SPM Buffer (wash 2) is added to each column of samples and mixed.
14. After incubating on the Mag Deck, the final wash removal volume stated is transferred to the liquid waste.
15. [Optional] If the user selects to "add water before air dry", the pipette will slowly aspirate and dispense 100µL of nuclease-free water to each column of samples.
16. A 10 minute incubation begins, at which point, the user should fill the reagent reservoir with the warmed Elution Buffer.
17. Once the incubation period is over, the Elution Buffer is added to the samples on the Mag Deck.
18. The user is prompted to remove the Plate on the Mag Deck and incubate at 65C.
19. Once the incubation is complete, the user returns the Plate to the Mag Deck.
20. The Mag Deck engages and after the pellet forms, the elution is transferred to the PCR plate.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/s/article/How-positional-calibration-works-on-the-OT-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
3e0b3f
