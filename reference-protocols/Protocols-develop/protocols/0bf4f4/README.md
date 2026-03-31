# Ilumina DNA Prep Part 1 - Tagment DNA

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina DNA Prep

## Description
This protocol is part 1 of a 3 part series which preps a 96 well Bio-Rad 200ul plate with diluted DNA and mastermix in accordance with the [Ilumina DNA Prep Kit](https://emea.support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf). DNA is diluted with water before mastermix is added. Find part 2 and part 3 of protocol below:

* [Part 2: Post Tagmentation Cleanup](https://protocols.opentrons.com/protocol/0bf4f4-pt2)
* [Part 3: Cleanup libraries](https://protocols.opentrons.com/protocol/0bf4f4-pt3)

Explanation of complex parameters below:
* `Number of samples`: Specify the number of samples for this run.
* `P300 Tip Start Column on Slot 8 (1-12)`: One column of the 200ul tip rack will be used per run. Specify which column to pick up tips from for this run.
* `P20 Multi-Channel GEN2 Mount`: Specify which side (left or right) the P20 multi channel pipette is mounted.
* `P300 Multi Channel GEN2 Mount`: Specify which side (left or right) the P300 multi channel pipette is mounted.


### Labware
* [Bio-RAD 96 well plate 200ul](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [Nest 12 Well Reservoir 15mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 20ul Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [Opentrons 200ul Filter Tip Rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)

### Pipettes
* [P20 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Ilumina DNA Prep](https://emea.support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/illumina_prep/illumina-dna-prep-reference-guide-1000000025416-09.pdf)

---

### Deck Setup

* Deck setup with a full plate of samples. Mastermix is always kept in column 1 regardless of number of samples, as is water in the first column of the Nest 12 well reservoir.

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0bf4f4/pt1/Screen+Shot+2021-07-15+at+5.05.35+PM.png)

---

### Protocol Steps
1. 10ul of water is added to each column, up to the number specified, in the empty plate in slot 3.
2. DNA is premixed for 10 repetitions before 5ul is transferred to the plate on slot 3 for each column containing water.
3. DNA and water is mixed.
4. Mastermix is added to water/DNA mixture, with a premix of mastermix step for every 3 columns that are transferred.


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
0bf4f4
