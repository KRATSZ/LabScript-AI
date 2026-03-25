# rhAmpSeq Library Prep Part 1 - PCR 1

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* rhAmpSeq Library Prep

## Description
This is part 1 of a 4 part protocol for the rhAmpSeq kit.
* [Part 2](https://develop.protocols.opentrons.com/protocol/onsite-ganda-2)

* [Part 3](https://develop.protocols.opentrons.com/protocol/onsite-ganda-3)
* [Part 4](https://develop.protocols.opentrons.com/protocol/onsite-ganda-4)

This portion adds three components to 30 uL samples as outlined in the rhAmpSeq manual.
* 10X rhAmp PCR Panel - Forward Pool
* 10X rhAmp PCR Panel - Reverse Pool
* 4X rhAmpSeq Library Mix 1

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
* If the deck layout of a particular protocol is more or less static, it is often helpful to attach a preview of the deck layout, most descriptively generated with Labware Creator. Example:
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/Screen+Shot+2022-07-05+at+5.03.11+PM.png)

### Reagent Setup
* Color Code:

![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/Screen+Shot+2022-07-05+at+5.05.51+PM.png)
* Reagent Reservoir, Slot 2:
![reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite-ganda/Screen+Shot+2022-07-05+at+5.20.46+PM.png)

---

### Protocol Steps
1. 5 uL of library mix from slot 2, column 1 is added to all samples in slot 1 on the magnetic module
2. 2 uL of forward primer from slot 2, column 2 is added to all samples in slot 1 on the magnetic module
3. 2 uL of reverse primer from slot 2, column 2 is added to all samples in slot 1 on the magnetic module
4. Robot lights flash on and off to signal protocol has completed

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
