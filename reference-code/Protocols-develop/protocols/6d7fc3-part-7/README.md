# GeneRead QIAact Lung DNA UMI Panel Kit: Cleanup of Universal PCR with QIAact Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung DNA UMI Panel Kit

## Description
This protocol automates the seventh part of a seven part protocol for the [GeneRead QIAact Lung DNA UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the Cleanup of Universal PCR with QIAact Beads part described in the [GeneRead QIAact Lung DNA UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=94ab92d2-1918-4388-989b-4cefa8eed203&lang=en).

* Part 1: [Fragmentation, End-repair and A-addition](https://protocols.opentrons.com/protocol/6d7fc3)
* Part 2: [Adapter Ligation](https://protocols.opentrons.com/protocol/6d7fc3-part-2)
* Part 3: [Cleanup of Adapter-ligated DNA with QIAact Beads.](https://protocols.opentrons.com/protocol/6d7fc3-part-3)
* Part 4: [Target Enrichment PCR](https://protocols.opentrons.com/protocol/6d7fc3-part-4)
* Part 5: [Cleanup of Target Enrichment PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-5)
* Part 6: [Universal PCR Amplification.](https://protocols.opentrons.com/protocol/6d7fc3-part-6)
* Part 7: [Cleanup of Universal PCR with QIAact Beads](https://protocols.opentrons.com/protocol/6d7fc3-part-7)

Explanation of complex parameters below:
* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `P300 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `P20 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `Magnetic Module Engage Height (mm)`: The height the magnets should raise.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96 Well 100 uL PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)

### Pipettes
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)

### Reagents
* [GeneRead QIAact Lung DNA UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/)

---

### Deck Setup
* The example below illustrates the starting deck layout for Part 6 (Cleanup of Universal PCR with QIAact Beads).
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6d7fc3/6d7fc3-part-7-layout.png)

### Reagent Setup

* Thermocycler (Slot 7): PCR Products from Universal PCR Amplification

* Slot 1: Magnetic Module with NEST 96 Well Deep Well Plate

* Slot 2: 96 Well Aluminum Block with Empty PCR Tubes.

* Slot 3: Temperature Module with 24 Well Aluminum Block. Add QIAact Beads in 2.0 mL tube in position A1.

* Slot 5: NEST 12 Well Reservoir: 80% Ethanol (A1, Blue) and Nuclease-Free Water (A12, Pink)

---

### Protocol Steps
1. Transfer 20 uL of PCR Amplication product to magnetic plate.
2. Add 80 uL of nuclease-free water to make total volume 100 uL.
3. Add 100 uL of QIAact beads to samples on magnetic plate and mix thoroughly.
4. Incubate at Room Temperature for 5 minutes.
5. Engage magnet for 10 minutes to separate beads.
6. Remove supernatant from samples.
7. Completely remove residual supernatant from the samples.
8. Perform an 80% ethanol wash.
9. Repeat previous step.
10. Centrifuge samples and replace on the magnetic module.
11. Engage magnet for 2 minutes.
12. Completely remove residual supernatant from the samples.
13. Air dry beads for 10 minutes.
14. Elute DNA from beads using 16 uL of nuclease-free water. Mix thoroughly.
15. Engage magnet for 5 minutes.
16. Transfer 28 uL of supernatant into fresh PCR tubes in slot 2.

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
6d7fc3-part-7