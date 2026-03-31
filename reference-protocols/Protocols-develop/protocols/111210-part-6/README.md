# GeneRead QIAact Lung RNA Fusion UMI Panel Kit: Cleanup of Adapter-ligated DNA with QIAseq Beads

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* GeneRead QIAact Lung RNA Fusion UMI Panel Kit

## Description
This protocol automates the sixth part of a ten part protocol for the [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936) which constructs molecularly bar-coded DNA libraries for digital sequencing. This protocol automates the Cleanup of Adapter-ligated DNA with QIAseq Beads part described in the [GeneRead QIAact Lung RNA Fusion UMI Panel Handbook](https://www.qiagen.com/us/resources/download.aspx?id=1a71d98a-c45c-44fa-b4af-874cd1d2b61f&lang=en).

* Part 1: [GeneRead QIAact Lung RNA Fusion UMI](https://protocols.opentrons.com/protocol/111210)
* Part 2: [Reverse transcription](https://protocols.opentrons.com/protocol/111210-part-2)
* Part 3: [Second strand synthesis](https://protocols.opentrons.com/protocol/111210-part-3)
* Part 4: [End repair / dA tailing](https://protocols.opentrons.com/protocol/111210-part-4)
* Part 5: [Adaptor ligation](https://protocols.opentrons.com/protocol/111210-part-5)
* Part 6: [Cleanup of Adapter-ligated DNA with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-6)
* Part 7: [Target Enrichment PCR](https://protocols.opentrons.com/protocol/111210-part-7)
* Part 8: [Cleanup of Target Enrichment PCR with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-8)
* Part 9: [Universal PCR Amplification](https://protocols.opentrons.com/protocol/111210-part-9)
* Part 10: [Cleanup of Universal PCR with QIAseq Beads](https://protocols.opentrons.com/protocol/111210-part-10)

Explanation of complex parameters below:
* `Number of Samples`: The total number of DNA samples. Samples must range between 1 (minimum) and 12 (maximum).
* `P20 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `P300 Single GEN2 Pipette Mount Position`: The position of the pipette, either left or right.
* `Magnetic Module Engage Height`: The height the magnets should raise.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* [Opentrons Filter Tips](https://shop.opentrons.com/collections/opentrons-tips)
* [NEST 96 Well 100 uL PCR Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons Aluminum Block Set](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)

### Pipettes
* [P20 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=31059478970462)
* [P300 Single GEN2 Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette?variant=5984549109789)

### Reagents
* [GeneRead QIAact Lung RNA Fusion UMI Panel Kit](https://www.qiagen.com/us/products/instruments-and-automation/genereader-system/generead-qiaact-lung-panels-ww/?catno=181936)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/111210/111210-part-6.png)

### Reagent Setup

**Slot 3**: QIAseq Beads (A1)

---

### Protocol Steps

**Note:** Ligation mix should be prepared beforehand and then placed in position A6 on the temperature module.

1. Transfer 100 uL of Ligation Product to deep well plate on magnetic module.
2. Add 90 uL of Beads to mixture.
3. Incubate for 5 minutes at room temperature.
4. Engage magnetic module for 10 minutes to separate beads from supernatant.
5. Remove supernatant and discard into trash.
6. Completely remove residual supernatant.
7. Perform ethanol wash with 260 uL and remove supernatant.
8. Repeat previous step.
9. Centrifuge samples briefly.
10. Replace samples on magnetic module and engage for 2 minutes. 
11. Remove residual supernatant.
12. Air dry beads for 10 minutes.
13. Add 52 uL of nuclease-free water to elute DNA.
14. Engage magnetic module for 5 minutes.
15. Transfer 50 uL of supernatant to new deep well plate in Slot 4.
16. Add 65 uL of QIAseq beads to new deep well plate.
17. Mix 10 times with a volume of 50 uL.
18. Incubate for 5 minutes at room temperature.
19. Remove old deep well plate and place new deep well plate on magnetic module.
20. Engage magnetic module for 10 minutes.
21. Remove supernatant and residual supernatant.
22. Perform ethanol wash with 200 uL and remove supernatant.
23. Repeat previous step.
24. Centrifuge plate briefly.
25. Replace plate on magnetic module and engage magnetic module for 2 minutes.
26. Completely remove supernatant.
27. Air dry beads for 10 minutes.
28. Add 22 uL of Nuclease-Free Water to samples in order to Elute DNA.
29. Engage Magnet for 10 minutes.
30. Transfer 9.4 uL of supernatant into two sets of PCR tubes in slot 2.

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
111210-part-6