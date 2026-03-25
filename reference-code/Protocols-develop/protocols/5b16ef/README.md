# SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB - Part 1

### Author
[Opentrons](https://opentrons.com/)




## Categories
* NGS Library Prep
	* Illumina Nextera Flex

## Description
This protocol is a semi-automated workflow which performs 8.1-8.4.6 of the SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB kit. For detailed information on protocol steps, please see below. You can find part 2 of the protocol here:

* [SARS-CoV-2 Using Illumina Nextera Flex & MiSeqNEB - Part 2](https://protocols.opentrons.com/protocol/5b16ef)

Explanation of complex parameters below:
* `Number of Sample Columns (1-6)`: Specify how many sample columns (1-6) this run will process. Samples will be placed in every other column, starting from column 1 (i.e. 1, 3, 5, 7, 9, 11 for 6 columns).
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to host the P20 pipette.


---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* Bio-Rad 96 Well Plate 200 µL PCR
* [Opentrons 20ul Tips](https://shop.opentrons.com/universal-filter-tips/)

### Pipettes
* [Opentrons P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [Illumina DNA Prep](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5b16ef/pt1/Screen+Shot+2022-04-14+at+2.39.58+PM.png)


---

### Protocol Steps
1. 2ul of mastermix is added to samples and mixed.
2. User incubates and runs plate on thermal cycler.
3. Pool reagent is added to final plate cols (split columns).
4. 4.5ul of sample are split from sample plate into final plate.
5. User incubates and runs plate on thermal cycler.
6. Split columns are recombined to the left.

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
5b16ef
