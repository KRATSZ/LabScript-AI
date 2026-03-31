# rhAmpSeq Library Prep Part 2 - Cleanup 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* rhAmpSeq Library Prep

## Description
This is part 2 of a 4 part protocol for the rhAmpSeq kit.
* [Part 1](https://develop.protocols.opentrons.com/protocol/onsite-ganda-1)

* [Part 3](https://develop.protocols.opentrons.com/protocol/onsite-ganda-3)
* [Part 4](https://develop.protocols.opentrons.com/protocol/onsite-ganda-4)

This portion performs a cleanup on the PCR amplification product. A reagent list is below:
* 80% Freshly Prepared Ethanol
* IDTE Buffer
* Agencourt AMPure XP Beads

Explanation of complex parameters below:
* `Number of Samples`: How many samples are to be run, from 1 to 96
* `P20 Multi GEN2 mount`: Which side the P20 Multi pipette is attached to
* `Flash on Protocol Completion?`: Will the OT-2 lights flash on and off when the protocol is complete?

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [NEST 96 Well Plate](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)

### Pipettes
* [P20 Multi Gen2](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P300 Multi Gen2](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [rhAmpSeq Library Preparation](https://www.idtdna.com/pages/products/crispr-genome-editing/rhampseq-crispr-analysis-system?gclid=Cj0KCQjwyMiTBhDKARIsAAJ-9VtBLGaCcK1fUfyRoAHuj2WOK08tv23xHuL-QpeEnTI2TxbhLf9kO-MaAgFAEALw_wcB)

---

### Deck Setup
* For 96 Samples
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/part_2/Screen+Shot+2022-07-05+at+6.11.23+PM.png)

### Reagent Setup
* Color Code:

![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/part_2/Screen+Shot+2022-07-05+at+6.13.57+PM.png)
* Reagent Reservoir, Slot 2:
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/part_2/Screen+Shot+2022-07-05+at+6.01.52+PM.png)
* Reagent Reservoir, Slot 4:
![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/part_2/Screen+Shot+2022-07-05+at+6.16.46+PM.png)

---

### Protocol Steps
1. 30 uL of Agencourt AMPure XP Beads is added to all samples on the magnetic module in slot 1 and mixed to homogenization
2. Samples with beads are incubated for 10 minutes
3. The magnetic module is engaged for 5 minutes
4. An ethanol wash is performed twice as outlined below:
	* Supernatant is discarded
	* 200 uL of 80% ethyl alcohol is added to samples
	* Samples are incubated for 1 minute
	* Supernatant is discarded
5. Remainder of ethyl alcohol is removed
6. Samples are air dried for 3 minutes
7. Magnetic module is disengaged
8. 15 uL of IDTE, ph 8.0 is added to each sample
9. Samples are incubated for 3 minutes
10. Magnetic module is engaged for 3 minutes
11. 11 uL of the resulting supernatant is removed to the elution plate in slot 5
12. Robot lights flash on and off to signal protocol has completed

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
onsite-ganda-lab
