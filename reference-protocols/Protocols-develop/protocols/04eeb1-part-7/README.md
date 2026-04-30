# Illumina COVIDSeq Test: Pool and Clean Up Libraries

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina COVIDSeq Test

## Description
The Illumina COVIDSeq Test is a high-throughput, next-generation sequencing test that is used fo detecting SARS-CoV-2 in patient samples. This protocol is the seventh part of a seven-part protocol that is run on the OT-2 for this kit.

* Part 1: [Anneal RNA](https://protocols.opentrons.com/protocol/04eeb1)
* Part 2: [Synthesize First Strand cDNA](https://protocols.opentrons.com/protocol/04eeb1-part-2)
* Part 3: [Amplify cDNA](https://protocols.opentrons.com/protocol/04eeb1-part-3)
* Part 4: [Tagment PCR Amplicons](https://protocols.opentrons.com/protocol/04eeb1-part-4)
* Part 5: [Post Tagmentation Clean Up](https://protocols.opentrons.com/protocol/04eeb1-part-5)
* Part 6: [Amplify Tagmented Amplicons](https://protocols.opentrons.com/protocol/04eeb1-part-6)
* Part 7: [Pool and Clean Up Libraries](https://protocols.opentrons.com/protocol/04eeb1-part-7)

Explanation of complex parameters below:
* `P300 Multichannel GEN2 Pipette Mount`: Choose the mount position of your P300 Multichannel pipette, either left or right.
* `P20 Multichannel GEN2 Pipette Mount`: Choose the mount position of your P20 Multichannel pipette, either left or right.

---

### Modules
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Opentrons 200 uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Bio-Rad Hard-Shell 96 Well Plate 200 µL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr/)

### Pipettes
* [P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)
* [P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Reagents
* [Illumina COVIDSeq Test](https://www.illumina.com/products/by-type/ivd-products/covidseq.html)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/04eeb1/04eeb1-p7.png)

**Note**: Add PCR strip on Column 1 of 96 Well Aluminum block in Slot 9. Add 1.7 mL tube to A1 of 24 Well Aluminum block on slot 6.

---

### Protocol Steps
1. Engage Magnetic Module and wait 3 minutes for beads to pellet.
2. Pick up 20 uL tips from slot 7
3. Aspirate 5 uL from Column 1 (A1) of the Magnetic Plate on Slot 3
4. Dispense into 8-strip PCR tubes.

**Steps 2-4 will repeat for the entire plate.**

5. Pause protocol for vortexing and centrifuging 8-strip tube.
6. Pick up SINGLE 200 uL tip from slot 4
7. Aspirate 55 uL from A1 of 8-strip tube
8. Dispense 55 uL into 1.7 mL tube in A1 of Slot 6.
9. Discard tip into the trash

**Steps 6-9 will repeat for all tubes in the strip.**

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
04eeb1-part-7